from gcloud import storage
from oauth2client.service_account import ServiceAccountCredentials
from termcolor import colored
import os

credentials = ServiceAccountCredentials.from_json_keyfile_name("gcreds.json")
client = storage.Client(credentials=credentials, project="assetgeneration")
bucket = client.get_bucket("xg_live_ops")

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
