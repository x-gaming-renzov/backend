import os, json, dotenv
from gcloud import storage
from oauth2client.service_account import ServiceAccountCredentials
import os, dotenv, pathlib
from termcolor import colored
from concurrent.futures import ThreadPoolExecutor
from pandas import DataFrame

from src.flat.main import flatten_json_leaving_lists

"""__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
"""

dotenv.load_dotenv()

"""credentials = ServiceAccountCredentials.from_json_keyfile_dict({
    "type": os.getenv("TYPE"),
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY"),
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL")
})"""

credentials = ServiceAccountCredentials.from_json_keyfile_name("gcreds.json")
client = storage.Client(credentials=credentials, project="assetgeneration")
bucket = client.get_bucket("xg_live_ops")

dotenv.load_dotenv()

def run_graph(USER_ID, USER_SESSION_ID, FILE_NAME, DATA_INFO_FROM_USER):

    graph_input = {
        "user_id": USER_ID,
        "user_session_id": USER_SESSION_ID,
        "file_name": FILE_NAME,
        "data_info_from_user": DATA_INFO_FROM_USER,
        "message": []
    }
    print(colored(f"Graph input: {graph_input}", "blue"))

    temp_dir_path = os.getcwd() + f"""/temp/{graph_input["user_id"]}/{graph_input["user_session_id"]}"""
    print(colored(f"Checking/creating directory: {temp_dir_path}", "blue"))
    pathlib.Path(temp_dir_path).mkdir(parents=True, exist_ok=True)
    pathlib.Path(temp_dir_path + f"""/{graph_input["file_name"]}""").touch()

    with open(f"""{temp_dir_path}/{graph_input["file_name"]}""", "r") as f:
        json_data_to_flat = json.load(f)
    flat_data = flatten_json_leaving_lists(json_data_to_flat)
    graph_input["file_name"] = f"{FILE_NAME.split('.')[0]}_flattened.json"
    with open(f"""{temp_dir_path}/{graph_input['file_name']}""", "w") as f:
        json.dump(flat_data, f)

    print("Flat processing done")
    #test.py
    import src.graph

    graph = src.graph.get_feild_name_correcting_task_graph()

    out = graph.invoke(graph_input)

    data_info = {
        "meaning_of_elements_in_data": str(out["meaning_of_elements_in_data"])
    }

    for field_info in out["field_info_list"]:
        data_info[field_info.field_name] = json.loads(field_info.model_dump_json())

    with open(f"""{temp_dir_path}/data_info.json""", "w") as f:
        json.dump(data_info, f)
    
    print("Graph run done")

    upload_input_files("out.json", "application/json", USER_ID, USER_SESSION_ID)
    # Run upload_all_files and cleanup in background
    with ThreadPoolExecutor() as executor:
        executor.submit(upload_all_files_async, USER_ID, USER_SESSION_ID)
        #executor.submit(cleanup_files_dir_async, USER_ID, USER_SESSION_ID)


def upload_input_files(file_name, file_type, USER_ID, USER_SESSION_ID):
    user_id = USER_ID
    user_session_id = USER_SESSION_ID
    file_name = file_name

    print(colored(f"Uploading file: {file_name}", "green"))

    blob = bucket.blob(f"""{user_id}/{user_session_id}/{file_name}""")
    blob.upload_from_filename(os.getcwd() + f"""/temp/{user_id}/{user_session_id}/{file_name}""", content_type=file_type)
    blob.metadata = { "xg_live_ops" : "attachment", "content-disposition" : "attachment" }
    blob.patch()
    blob.content_disposition = f"attachment; filename={file_name}"
    blob.patch()

    print(colored(f"File uploaded to: {blob.public_url}", "green"))

# Modify upload_all_files to accept callback
def upload_all_files_async(USER_ID, USER_SESSION_ID, callback=None):
    user_id = USER_ID
    user_session_id = USER_SESSION_ID

    print(colored(f"Uploading all files for user_id: {user_id} and user_session_id: {user_session_id}", "green"))

    for root, dirs, files in os.walk(os.getcwd() + f"""/temp/{user_id}/{user_session_id}"""):
        for file in files:
            if file != "out.json":
                upload_input_files(file, "application/json", user_id, user_session_id)

    print(colored("Files uploaded", "green"))
    if callback:
        callback("Upload completed")

# Modify cleanup_files_dir to accept callback
def cleanup_files_dir_async(USER_ID, USER_SESSION_ID, callback=None):
    user_id = USER_ID
    user_session_id = USER_SESSION_ID

    print(colored(f"Cleaning up files for user_id: {user_id} and user_session_id: {user_session_id}", "green"))

    for root, dirs, files in os.walk(os.getcwd() + f"""/temp/{user_id}/{user_session_id}"""):
        for file in files:
            os.remove(os.path.join(root, file))
                
    for root, dirs, files in os.walk(os.getcwd() + f"""/temp/{user_id}/{user_session_id}"""):
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))

    print(colored("Files cleaned up", "green"))
    if callback:
        callback("Cleanup completed")

def get_download_link(USER_ID, USER_SESSION_ID, FILE_NAME):

    blob = bucket.blob(f"""{USER_ID}/{USER_SESSION_ID}/{FILE_NAME}""")
    return blob.public_url

def get_changes_to_field_names(USER_ID, USER_SESSION_ID) -> DataFrame:
    with open(f"""temp/{USER_ID}/{USER_SESSION_ID}/data_info.json""", "r") as f:
        data_info = json.load(f)

    changes = []
    for field_info in data_info:
        if field_info == "meaning_of_elements_in_data":
            continue
        changes.append({
            "field_name": data_info[field_info]['field_name'],
            "field_name_corrected": data_info[field_info]['field_new_name'],
            "description": data_info[field_info]['field_description']
        })

    return DataFrame(changes)