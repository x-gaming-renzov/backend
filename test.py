from Autolabel.templates.GenerateCleanMetadata.GenerateCleanMetadata import GenerateCleanMetadata

import os
import logging
import requests
import json
from dotenv import load_dotenv
import traceback
from gcloud import storage
import pandas as pd
from pymongo import MongoClient

load_dotenv()

from oauth2client.service_account import ServiceAccountCredentials

def connect_to_mongo(uri: str, database_name: str):
    """
    Connect to a MongoDB database.

    :param uri: MongoDB connection URI.
    :param database_name: Name of the database to connect to.
    :return: The database object.
    """
    try:
        # Create a MongoClient instance
        client = MongoClient(uri)
        
        # Access the specified database
        db = client[database_name]
        
        print(f"Connected to MongoDB database: {database_name}")
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None


def process_task_completion(task_id):
    try:
        xg_mongo_db = connect_to_mongo(os.getenv('XG_MONGO_URI'), os.getenv('XG_MONGO_DB'))

        credentials = ServiceAccountCredentials.from_json_keyfile_name('gcreds.json')
        client = storage.Client(credentials=credentials, project='assetgeneration')
        bucket = client.get_bucket('xg_live_ops')

        temp_dir = os.getcwd() + '/temp'

        task = xg_mongo_db['tasks'].find_one({'_id': task_id})

        if not task:
            return 

        user_id = task['userID']
        description = task['description']
        task_type = task['type']
        task_path = f"{temp_dir}/{user_id}/{task_id}"

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

        return 

    except Exception as e:
        traceback.print_exc()
        return 

process_task_completion("eb36b4ba-3217-4da2-9f72-7db9e1920261")
