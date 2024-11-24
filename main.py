import os, json, dotenv
from gcloud import storage
from oauth2client.service_account import ServiceAccountCredentials
import os, dotenv

import src.graph

dotenv.load_dotenv()

credentials = ServiceAccountCredentials.from_json_keyfile_name('gcreds.json')
client = storage.Client(credentials=credentials, project='assetgeneration')
bucket = client.get_bucket('xg_live_ops')

dotenv.load_dotenv()

graph_input = {
    'user_id': os.getenv('USER_ID'),
    'user_session_id': os.getenv('USER_SESSION_ID'),
    'file_name': os.getenv('FILE_NAME'),
    'data_info_from_user': os.getenv('DATA_INFO_FROM_USER'),
    'message': []
}

graph = src.graph.get_feild_name_correcting_task_graph()

out = graph(graph_input)

data_info = {
    'meaning_of_elements_in_data': str(out['meaning_of_elements_in_data'])
}

for field_info in out['field_info']:
    data_info[field_info['field_name']] = field_info['field_info']

