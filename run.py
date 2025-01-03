from flask import Flask, request, jsonify
import os
import logging
import requests
import json
from dotenv import load_dotenv
import traceback
from gcloud import storage
import pandas as pd

load_dotenv()

from src.utils.database import connect_to_mongo
from src.utils.large_files_ops import rename_field_in_json
from oauth2client.service_account import ServiceAccountCredentials

from Autolabel.templates.GenerateCleanMetadata.GenerateCleanMetadata import GenerateCleanMetadata

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("task_processor")

# Load environment variables
print("Connecting to mongo")
xg_mongo_db = connect_to_mongo(os.getenv('XG_MONGO_URI'), os.getenv('XG_MONGO_DB'))
print("Connected to mongo")

# Initialize Google Cloud Storage client
credentials = ServiceAccountCredentials.from_json_keyfile_name('gcreds.json')
client = storage.Client(credentials=credentials, project='assetgeneration')
bucket = client.get_bucket('xg_live_ops')

# Temporary storage directory
temp_dir = os.getcwd() + '/temp'

# Function to process task completion
def process_task_completion(task_id):
    try:
        logger.info(f"Processing task completion for task_id: {task_id}")

        task = xg_mongo_db['tasks'].find_one({'_id': task_id})
        if not task:
            return jsonify({'status': 'error', 'message': f'Task {task_id} not found'}), 404

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

        return jsonify({'status': 'success', 'message': f'Task {task_id} completed'})

    except Exception as e:
        logger.error(f"Error processing task completion: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Function to process user feedback
def process_user_feedback(task_id):
    try:
        logger.info(f"Processing user feedback for task_id: {task_id}")

        task = xg_mongo_db['tasks'].find_one({'_id': task_id})
        if not task:
            return jsonify({'status': 'error', 'message': f'Task {task_id} not found'}), 404

        user_id = task['userID']
        fields = task['fields']
        task_path = f"{temp_dir}/{user_id}/{task_id}"

        # Download existing output
        blob = bucket.blob(f'{user_id}/tasks/{task_id}/out.json')
        os.makedirs(task_path, exist_ok=True)
        blob.download_to_filename(f"{task_path}/data_to_rename.json")

        # Rename fields based on user feedback
        with open(f"{task_path}/data_to_rename.json") as f:
            data = json.load(f)

        for field in fields:
            if 'user_suggested_name' in field:
                data = rename_field_in_json(data, field['ai_suggested_name'], field['user_suggested_name'])
                field['ai_suggested_name'] = field['user_suggested_name']
                field['score'] = 5

        with open(f"{task_path}/data_to_rename.json", 'w') as f:
            json.dump(data, f, indent=4)

        # Upload updated file
        blob.upload_from_filename(f"{task_path}/data_to_rename.json")
        blob.metadata = {"xg_live_ops": "attachment", "content-disposition": "attachment"}
        blob.content_disposition = f"attachment; filename=data.json"
        blob.patch()

        xg_mongo_db['tasks'].update_one({'_id': task_id}, {'$set': {'status': 'paused', 'stage': 'complete', 'fields': fields}})
        xg_mongo_db['tasks'].update_one({'_id': task_id}, {'$unset': {'hasUserResponded': 1}})

        return jsonify({'status': 'success', 'message': f'User feedback processed for task {task_id}'})

    except Exception as e:
        logger.error(f"Error processing user feedback: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Flask route to handle incoming requests
@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.json
        task_id = data.get('task_id')
        task_type = data.get('task_type')

        if not task_id or not task_type:
            return jsonify({'status': 'error', 'message': 'task_id and task_type are required'}), 400

        if task_type == 'completion':
            return process_task_completion(task_id)
        elif task_type == 'user_feedback':
            return process_user_feedback(task_id)
        else:
            return jsonify({'status': 'error', 'message': f'Invalid task_type: {task_type}'}), 400

    except Exception as e:
        logger.error(f"Error in /process endpoint: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=(os.getenv('PORT', 8080)),debug=True)
