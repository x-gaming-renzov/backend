import os, json, dotenv
from gcloud import storage
from oauth2client.service_account import ServiceAccountCredentials
import os, dotenv, pathlib
from termcolor import colored
from concurrent.futures import ThreadPoolExecutor, as_completed
from pandas import DataFrame
from src.tools.retriever_tool import get_retriever
import uuid
from typing import Set
from src.flat.main import flatten_json_leaving_lists
import src.graph

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


def run_graph(USER_ID, USER_SESSION_ID, FILE_NAME, DATA_INFO_FROM_USER, should_upload_files=True):
    #creating input dict for graph
    graph_input = {
        "user_id": USER_ID,
        "user_session_id": USER_SESSION_ID,
        "file_name": FILE_NAME,
        "data_info_from_user": DATA_INFO_FROM_USER,
        "message": []
    }
    print(colored(f"Graph input: {graph_input}", "blue"))
    #creating retriever (only one for whole function)
    retriever = get_retriever(USER_ID, USER_SESSION_ID, DATA_INFO_FROM_USER)

    #set it for graph input
    graph_input["retriever"] = retriever

    temp_dir_path = os.getcwd() + f"""/temp/{graph_input["user_id"]}/{graph_input["user_session_id"]}"""
    print(colored(f"Checking/creating directory: {temp_dir_path}", "blue"))
    pathlib.Path(temp_dir_path).mkdir(parents=True, exist_ok=True)
    pathlib.Path(temp_dir_path + f"""/{graph_input["file_name"]}""").touch()

    with open(f"""{temp_dir_path}/{graph_input["file_name"]}""", "r") as f:
        json_data_to_flat = json.load(f)
    flat_data = flatten_json_leaving_lists(json_data_to_flat)
    json_data_to_flat = None
    graph_input["file_name"] = f"{FILE_NAME.split('.')[0]}_flattened.json"
    with open(f"""{temp_dir_path}/{graph_input['file_name']}""", "w") as f:
        json.dump(flat_data, f)

    print("Flat processing done")
    #test.py

    graph = src.graph.get_feild_name_correcting_task_graph()

    out = graph.invoke(graph_input, {"recursion_limit": 100})

    data_info = {
        "meaning_of_elements_in_data": str(out["meaning_of_elements_in_data"])
    }

    for field_info in out["field_info_list"]:
        data_info[field_info.field_name] = json.loads(field_info.model_dump_json())

    with open(f"""{temp_dir_path}/data_info.json""", "w") as f:
        json.dump(data_info, f)


    with open(f"""{temp_dir_path}/out.json""", "r") as f:
        out_data = json.load(f)
    with ThreadPoolExecutor() as executor:
        running_correction_on_elements_results = []
        for i, element in enumerate(out_data):
            for key in element:
                if isinstance(element[key], list):
                    if isinstance(element[key][0], dict):
                        #element[key] = run_deep_value_correction(USER_ID, USER_SESSION_ID, element[key], key, i)
                        sub_process_id = uuid.uuid4()

                        #create a folder for the sub process
                        pathlib.Path(f"{temp_dir_path}/{sub_process_id}").mkdir(parents=True, exist_ok=True)
                        with open(f"""{temp_dir_path}/{sub_process_id}/data.json""", "w") as f:
                            json.dump(element[key], f)

                        sub_process_input = {  
                            "user_id": USER_ID,
                            "user_session_id": f"{USER_SESSION_ID}/{sub_process_id}",
                            "file_name": f"data.json",
                            "data_info_from_user": f"{DATA_INFO_FROM_USER} for {key} in key in element. This element is part of a list of dictionaries. This element represents {data_info['meaning_of_elements_in_data']}",
                            "message": []
                        }

                        with open(f"""{temp_dir_path}/{sub_process_id}/input.json""", "w") as f:
                            json.dump(sub_process_input, f)
                        
                        sub_process_input["retriever"] = retriever
                        
                        running_correction_on_elements_results.append({
                            "sub_process_id": sub_process_id,
                            "future": executor.submit(run_graph, sub_process_input["user_id"], sub_process_input["user_session_id"], sub_process_input["file_name"], sub_process_input["data_info_from_user"], False),
                            "key": key,
                            "element_index": i
                        })
        out_data = None
        #wait for all sub processes to finish
        for running_correction_on_elements_result in as_completed([running_correction_on_elements_result["future"] for running_correction_on_elements_result in running_correction_on_elements_results]):
            continue
        
        with open(f"""{temp_dir_path}/out.json""", "r") as f:
            out_data = json.load(f)

        for running_correction_on_elements_result in running_correction_on_elements_results:

            with open(f"""{temp_dir_path}/{running_correction_on_elements_result["sub_process_id"]}/out.json""", "r") as f:
                corrected_deep_value = json.load(f)
                if len(corrected_deep_value) ==1:
                    out_data[running_correction_on_elements_result["element_index"]][running_correction_on_elements_result["key"]] = corrected_deep_value[0]
                else:
                    out_data[running_correction_on_elements_result["element_index"]][running_correction_on_elements_result["key"]] = corrected_deep_value

        with open(f"""{temp_dir_path}/out.json""", "w") as f:
            json.dump(out_data, f)

        out_data = None

        print("Graph run done")

        if should_upload_files:
            upload_input_files("out.json", "application/json", USER_ID, USER_SESSION_ID)

    #TODO : upload all files using script


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

def get_changes_dict(path, parent_dict = None) : 
    #check if """temp/{USER_ID}/{USER_SESSION_ID}/data_info.json""" exists
    if not os.path.exists(path):
        return parent_dict
    
    if parent_dict is None:
        parent_dict = {}


    with open(path, "r") as f:
        data_info = json.load(f)

    for field_info in data_info:
        if field_info == "meaning_of_elements_in_data":
            continue
        if not data_info[field_info]['field_new_name'] in parent_dict:
            parent_dict[data_info[field_info]['field_new_name']] = {
                "description": data_info[field_info]['field_description'],
                "old_names": set([data_info[field_info]['field_name']])
            }
        else:
            parent_dict[data_info[field_info]['field_new_name']]["old_names"].add(data_info[field_info]['field_name'])

    return parent_dict


def get_changes_to_field_names(USER_ID, USER_SESSION_ID) -> DataFrame:
    changes = []

    changes_dict = get_changes_dict(os.getcwd() + f"""/temp/{USER_ID}/{USER_SESSION_ID}/data_info.json""")

    #loop through all folders and subfolders 
    for root, dirs, files in os.walk(os.getcwd() + f"""/temp/{USER_ID}/{USER_SESSION_ID}"""):
        for file in files:
            if file == "data_info.json":
                temp_changes_dict = get_changes_dict(os.path.join(root, file))
                for key in temp_changes_dict:
                    if key in changes_dict:
                        changes_dict[key]["old_names"].update(temp_changes_dict[key]["old_names"])
                    else:
                        changes_dict[key] = temp_changes_dict[key]
    
    for key in changes_dict:
        changes.append({
            "new_name": key,
            "old_names": list(changes_dict[key]["old_names"]),
            "description": changes_dict[key]["description"]
        })

    return DataFrame(changes)