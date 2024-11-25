import streamlit as st
import json, pathlib
import main
from uuid import uuid4

st.title('Make your data AI ready')

st.write('Upload your data file and we will make it AI ready for you')

#text input "What is this data about?"
DATA_INFO_FROM_USER = st.text_input("What is this data about?")

uploaded_file_data = st.file_uploader("Choose a file", key='uploaded_file_data')
uploaded_file_data_kb_data = st.file_uploader("Choose a file", key='uploaded_file_data_kb_data')

USER_ID = str(uuid4())
USER_SESSION_ID = str(uuid4())

kb_urls = []

#text input with add button. Add button will add the url to kb_urls list
kb_url = st.text_input("Add KB URL")
if st.button("Add"):
    kb_urls.append(kb_url)


#display all the urls in the kb_urls list
st.write("KB URLs")

if uploaded_file_data_kb_data is not None:
    #save the uploaded file to the temp/{USER_ID}/{USER_SESSION_ID} directory
    #check if the directory exists, if not create it
    pathlib.Path(f"temp/{USER_ID}/{USER_SESSION_ID}").mkdir(parents=True, exist_ok=True)
    with open(f"temp/{USER_ID}/{USER_SESSION_ID}/kb_data.txt", "wb") as f:
        f.write(uploaded_file_data_kb_data.getvalue())

    main.upload_input_files("kb_data.txt", uploaded_file_data_kb_data.type, USER_ID, USER_SESSION_ID)
    #main.upload_input_files(uploaded_file_data_kb_data, "kb_data.txt", uploaded_file_data_kb_data.size, uploaded_file_data_kb_data.type, USER_ID, USER_SESSION_ID)

if uploaded_file_data is not None:
    #save the uploaded file to the temp/{USER_ID}/{USER_SESSION_ID} directory
    #check if the directory exists, if not create it
    pathlib.Path(f"temp/{USER_ID}/{USER_SESSION_ID}").mkdir(parents=True, exist_ok=True)
    with open(f"temp/{USER_ID}/{USER_SESSION_ID}/{uploaded_file_data.name}", "wb") as f:
        f.write(uploaded_file_data.getvalue())

    #save the uploaded file to the bucket
    #main.upload_input_files(uploaded_file_data.name, uploaded_file_data.type, USER_ID, USER_SESSION_ID)

#add generate button
generate = st.button("Generate")

if generate:
    print("Generate button clicked")
    main.upload_input_files(uploaded_file_data.name, uploaded_file_data.type, USER_ID, USER_SESSION_ID)
    print("Files uploaded")

    main.run_graph(USER_ID, USER_SESSION_ID, uploaded_file_data.name, DATA_INFO_FROM_USER)

    with open(f"temp/{USER_ID}/{USER_SESSION_ID}/out.json", "r") as f:
        out = json.load(f)

        st.download_button(label="Download AI ready data", data=json.dumps(out), file_name="out.json", mime="application/json")