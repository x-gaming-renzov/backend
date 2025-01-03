import os, dotenv
from gcloud import storage
from oauth2client.service_account import ServiceAccountCredentials
import requests, json

dotenv.load_dotenv()

credentials = ServiceAccountCredentials.from_json_keyfile_name('gcreds.json')
client = storage.Client(credentials=credentials, project='assetgeneration')
bucket = client.get_bucket('xg_live_ops')

from src.utils.database import connect_to_mongo
import pandas as pd
from src.utils.large_files_ops import rename_field_in_json
from Autolabel.templates.GenerateCleanMetadata.GenerateCleanMetadata import GenerateCleanMetadata

dotenv.load_dotenv()

xg_mongo_db = connect_to_mongo(os.getenv('XG_MONGO_URI'), os.getenv('XG_MONGO_DB')) 

def check_task_required_completion():
    print('Checking tasks that require completion')

    # Get all tasks that require completion
    tasks = xg_mongo_db['tasks'].find({
        'status': 'active',
        'stage': 'active'
    })

    task_list = []
    for task in tasks:
        task_list.append(str(task['_id']))

    print('Tasks that require completion:', task_list)
    return task_list

def process_task_completion(task_id):
    try:

        task = xg_mongo_db['tasks'].find_one({'_id': task_id})
        if not task:
            return 

        user_id = task['userID']
        description = task['description']
        task_type = task['type']
        task_path = f"temp/{user_id}/{task_id}"

        print(f"task_path : {task_path}")

        # Create task directory
        os.makedirs(task_path, exist_ok=True)

        # Handle task types
        if task_type == 'json':
            data_url = task['data_url']
            kb_url = task['kb_url']
            r = requests.get(data_url)
            if kb_url and kb_url != 'null' and kb_url != '':
                kb_r = requests.get(kb_url)
                with open(f"{task_path}/kb.txt", 'wb') as f:
                    f.write(kb_r.content)
                with open(f"{task_path}/kb.txt", 'r') as f:
                    kb = f.read()
                    kb += '\n'+ description
                with open(f"{task_path}/kb.txt", 'w') as f:
                    f.write(kb)
            else:
                with open(f"{task_path}/kb.txt", 'w') as f:
                    f.write(description)

            with open(f"{task_path}/data.json", 'wb') as f:
                f.write(r.content)

        elif task_type == 'mongo':
            source_id = task['sourceID']
            mongo_uri = xg_mongo_db['sources'].find_one({'_id': source_id})['url']
            collection = task['collection']
            db_name = task['db_name']

            user_mongo_db = connect_to_mongo(mongo_uri, db_name)
            data = [doc for doc in user_mongo_db[collection].find()]

            # Convert ObjectId to string
            def convert_objectids(doc):
                if isinstance(doc, dict):
                    return {k: convert_objectids(v) for k, v in doc.items()}
                elif isinstance(doc, list):
                    return [convert_objectids(v) for v in doc]
                elif not isinstance(doc, (int, float, str)):
                    return str(doc)
                else:
                    return doc

            converted_documents = [convert_objectids(doc) for doc in data]
            with open(f"{task_path}/data.json", 'w') as f:
                json.dump(converted_documents, f, indent=4)

            kb_url = task['kb_url']
            if kb_url and kb_url != 'null' and kb_url != '':
                kb_r = requests.get(kb_url)
                with open(f"{task_path}/kb.txt", 'wb') as f:
                    f.write(kb_r.content)
                with open(f"{task_path}/kb.txt", 'r') as f:
                    kb = f.read()
                    kb += '\n'+ description
                with open(f"{task_path}/kb.txt", 'w') as f:
                    f.write(kb)

        elif task_type == 'csv':
            data_url = task['data_url']
            kb_url = task['kb_url']
            r = requests.get(data_url)
            if kb_url and kb_url != 'null' and kb_url != '':
                kb_r = requests.get(kb_url)
                with open(f"{task_path}/kb.txt", 'wb') as f:
                    f.write(kb_r.content)
                with open(f"{task_path}/kb.txt", 'r') as f:
                    kb = f.read()
                    kb += '\n'+ description
                with open(f"{task_path}/kb.txt", 'w') as f:
                    f.write(kb)
            else:
                with open(f"{task_path}/kb.txt", 'w') as f:
                    f.write(description)

            with open(f"{task_path}/data.csv", 'wb') as f:
                f.write(r.content)

            data = pd.read_csv(f"{task_path}/data.csv")
            #create json file of first 10 rows
            data = data.head(10)
            data.to_json(f"{task_path}/data.json", orient='records', indent=4)

        # Process task with graph runner
        generator = GenerateCleanMetadata(data_path=f"{task_path}/data.json", kb_path=f"{task_path}/kb.txt", cache_path=f"{task_path}/")
        output = generator.run()
        metadata_output = {
            'field_mapping': [],
            'enhanced_descriptions': [],
            'semantic_clarity_report': []
        }

        for field in output['field_mapping']:
            metadata_output['field_mapping'].append({
                'new_field_name': output['field_mapping'][field],
                'old_field_name': field,
            })
        
        for field in output['enhanced_descriptions']:
            metadata_output['enhanced_descriptions'].append({
                'field_name': field,
                'description': output['enhanced_descriptions'][field],
            })
        for field in output['semantic_clarity_report']:
            metadata_output['semantic_clarity_report'].append(output['semantic_clarity_report'][field])

        xg_mongo_db['tasks'].update_one({'_id': task_id}, {'$set': {'status': 'paused', 'stage': 'complete', 'metadata_output': metadata_output}})
        
        with open(f"{task_path}/metadata_output.json", "w") as f:
            json.dump(metadata_output, f, indent=4)
        with open(f"{task_path}/metadata.json", "w") as f:
            json.dump(output, f, indent=4)
        return metadata_output

    except Exception as e:
        #throw error
        print(e)

        return 404


def process_tasks(tasks):
    for task in tasks:
        with open('out.json', 'w') as f:
            json.dump(process_task_completion(task), f, indent=4)


if __name__ == '__main__':
    while True:
        try:
            process_tasks(check_task_required_completion())
        except Exception as e:
            #check is log.txt exists
            if not os.path.exists('log.txt'):
                with open('log.txt', 'w') as f:
                    f.write(str(e))
            else:
                with open('log.txt', 'a') as f:
                    f.write(str(e))
            continue