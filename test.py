
    upload_input_files("original.json", "application/json", USER_ID, USER_SESSION_ID)
    upload_input_files(graph_input["file_name"], "application/json", USER_ID, USER_SESSION_ID)
    print("Files uploaded")

    data_blob = bucket.blob(f"""{graph_input["user_id"]}/{graph_input["user_session_id"]}/{graph_input["file_name"]}""")
    data_blob.download_to_filename(f"""temp/{graph_input["user_id"]}/{graph_input["user_session_id"]}/{graph_input["file_name"]}""")

    kb_urls_blob = bucket.blob(f"""{graph_input["user_id"]}/{graph_input["user_session_id"]}/kb_urls.json""")
    if kb_urls_blob.exists():
        pathlib.Path(temp_dir_path + "/kb_urls.json").touch()
        kb_urls_blob.download_to_filename(f"""temp/{graph_input["user_id"]}/{graph_input["user_session_id"]}/kb_urls.json""")

    kb_data_blob = bucket.blob(f"""{graph_input["user_id"]}/{graph_input["user_session_id"]}/kb_data.txt""")
    if kb_data_blob.exists():
        pathlib.Path(temp_dir_path + "/kb_data.txt").touch()
        kb_data_blob.download_to_filename(f"""temp/{graph_input["user_id"]}/{graph_input["user_session_id"]}/kb_data.txt""")
