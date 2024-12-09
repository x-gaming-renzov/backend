import os, dotenv
from gcloud import storage
from oauth2client.service_account import ServiceAccountCredentials
import requests, json

dotenv.load_dotenv()

credentials = ServiceAccountCredentials.from_json_keyfile_name('gcreds.json')
client = storage.Client(credentials=credentials, project='assetgeneration')
bucket = client.get_bucket('xg_live_ops')

from src.utils.database import connect_to_mongo
from runner import run_graph, get_changes_to_field_names
from src.utils.large_files_ops import rename_field_in_json

dotenv.load_dotenv()

xg_mongo_db = connect_to_mongo(os.getenv('XG_MONGO_URI'), os.getenv('XG_MONGO_DB')) 

def check_task_required_completion():
    print('Checking tasks that require completion')

    # Get all tasks that require completion
    tasks = xg_mongo_db['tasks'].find({
        'status': 'active',
        'stage': 'active'
    })

    inputs = []
    temp_dir = os.getcwd() + '/temp'

    for task in tasks:
        if 'touched' in task:
            continue
        # add 'touched' field to task
        xg_mongo_db['tasks'].update_one({'_id': task['_id']}, {'$set': {'touched': True}})

        user_id = task['userID']
        task_id = task['_id']
        if 'kb_url' in task:
            kb_url = task['kb_url']
        else:
            kb_url = None
        description = task['description']

        if not os.path.exists(f"{temp_dir}/{user_id}/{task_id}"):
            os.makedirs(f"{temp_dir}/{user_id}/{task_id}")

        if kb_url:
            print('Downloading file from', kb_url)
            r = requests.get(kb_url)
            kb_file_name = 'kb_data.json'
            with open(f"{temp_dir}/{user_id}/{task_id}/kb_data.txt", 'wb') as f:
                f.write(r.content)

        #TODO : start processing task
        if task['type'] == 'json':
            data_url = task['data_url']
            
            
            # Download the file
            print('Downloading file from', data_url)
            r = requests.get(data_url)

            with open(f"{temp_dir}/{user_id}/{task_id}/data.json", 'wb') as f:
                f.write(r.content)
            
            inputs.append({
                'user_id' : user_id,
                'session_id' : task_id,
                'data_info_from_user' : description,
            })

        if task['type'] == 'mongo':
            source_id = task['sourceID']
            mongo_uri = xg_mongo_db['sources'].find_one({'_id': source_id})['url']
            collection = task['collection']
            db_name = task['db_name']

            print(f"Connecting to mongo at {mongo_uri} and fetching data from {collection} in {db_name}")

            #download all documents from mongo and save to data.json
            user_mongo_db = connect_to_mongo(mongo_uri, db_name)
            data = [doc for doc in user_mongo_db[collection].find()]
            print('Downloaded data from mongo')
            print(data)
            
            # Convert ObjectId to string for JSON serialization
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
            with open(f"{temp_dir}/{user_id}/{task_id}/data.json", 'w') as f:
                json.dump(converted_documents, f, indent=4)
            
            inputs.append({
                'user_id' : user_id,
                'session_id' : task_id,
                'data_info_from_user' : description,
            })

    print('Tasks that require completion:', len(inputs))
    print(inputs)
    return inputs

def process_tasks(inputs):
    print('Processing tasks')
    for input in inputs:
        user_id = input['user_id']
        task_id = input['session_id']
        description = input['data_info_from_user']

        #TODO : process the task
        print('Processing task for user', user_id, 'with task ID', task_id, 'with description', description)
        temp_dir = os.getcwd() + '/temp'

        run_graph(user_id, task_id, 'data.json', description)

        changes_df = get_changes_to_field_names(user_id, task_id)
        fields_names = []
        for index, row in changes_df.iterrows():
            fields_names.append(
                {
                    'original_name': row['old_names'],
                    'ai_suggested_name': row['new_name'],
                    'score': row['score']
                }
            )
        #if any score less than 3
        if any(row['score'] < 3 for index, row in changes_df.iterrows()):
            xg_mongo_db['tasks'].update_one({'_id': task_id}, {'$set': {'status': 'paused'}})
        else:
            xg_mongo_db['tasks'].update_one({'_id': task_id}, {'$set': {'status': 'paused'}})
            xg_mongo_db['tasks'].update_one({'_id': task_id}, {'$set': {'stage': 'complete'}})
        xg_mongo_db['tasks'].update_one({'_id': task_id}, {'$set': {'fields': fields_names}})
        

    print('Tasks processed')

def check_for_user_feedback():
    tasks = xg_mongo_db['tasks'].find(
    {'hasUserResponded': True},
    {'_id': 1, 'userID': 1, 'description': 1, 'fields': 1}
    )

    for task in tasks:
        user_id = task['userID']
        task_id = task['_id']
        description = task['description']
        fields = task['fields']

        #TODO : process the task
        print('Processing task for user', user_id, 'with task ID', task_id, 'with description', description)
        temp_dir = os.getcwd() + '/temp'

        #download data 
        blob = bucket.blob(f'{user_id}/tasks/{task_id}/out.json')
        blob.download_to_filename(f"{temp_dir}/{user_id}/{task_id}/data_to_rename.json")

        with open(f"{temp_dir}/{user_id}/{task_id}/data_to_rename.json") as f:
            data = json.load(f)
        
        for field in fields:
            if 'user_suggested_name' in field:
                print('Renaming field', field['ai_suggested_name'], 'to', field['user_suggested_name'])
                data = rename_field_in_json(data, field['ai_suggested_name'], field['user_suggested_name'])
                field['ai_suggested_name'] = field['user_suggested_name']
                field['score'] = 5
        
        with open(f"{temp_dir}/{user_id}/{task_id}/data_to_rename.json", 'w') as f:
            json.dump(data, f, indent=4)
        
        blob = bucket.blob(f'{user_id}/tasks/{task_id}/out.json')
        blob.upload_from_filename(f"{temp_dir}/{user_id}/{task_id}/data_to_rename.json")
        blob.metadata = { "xg_live_ops" : "attachment", "content-disposition" : "attachment" }
        blob.content_disposition = f"attachment; filename=data.json"
        blob.patch()

        xg_mongo_db['tasks'].update_one(
            {'_id': task_id},
            {'$set': {'status': 'paused', 'stage': 'complete', 'fields': fields}}
        )

        xg_mongo_db['tasks'].update_one({'_id': task_id}, {'$unset': {'hasUserResponded': 1}})



if __name__ == '__main__':
    while True:
        try:
            process_tasks(check_task_required_completion())
            check_for_user_feedback()
        except Exception as e:
            #check is log.txt exists
            if not os.path.exists('log.txt'):
                with open('log.txt', 'w') as f:
                    f.write(str(e))
            else:
                with open('log.txt', 'a') as f:
                    f.write(str(e))
            continue