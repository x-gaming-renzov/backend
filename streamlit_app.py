import streamlit as st
import threading
import queue
import time
import sys
import json
import pathlib
import main
from uuid import uuid4

class QueueStream:
    def __init__(self, queue):
        self.queue = queue
    def write(self, msg):
        if msg != '\n':
            self.queue.put(msg)
    def flush(self):
        pass

def run_main_run_graph(log_queue, USER_ID, USER_SESSION_ID, file_name, DATA_INFO_FROM_USER):
    # Redirect stdout
    original_stdout = sys.stdout
    sys.stdout = QueueStream(log_queue)
    
    try:

        main.run_graph(USER_ID, USER_SESSION_ID, file_name, DATA_INFO_FROM_USER)
    finally:
        # Restore stdout
        sys.stdout = original_stdout

def main_app():
    st.title('Make your data AI ready')

    st.write('Upload your data file and we will make it AI ready for you')

    # Initialize session state variables
    if 'USER_ID' not in st.session_state:
        st.session_state.USER_ID = str(uuid4())
    if 'USER_SESSION_ID' not in st.session_state:
        st.session_state.USER_SESSION_ID = str(uuid4())
    if 'generate_clicked' not in st.session_state:
        st.session_state.generate_clicked = False
    if 'log_queue' not in st.session_state:
        st.session_state.log_queue = queue.Queue()
    if 'thread' not in st.session_state:
        st.session_state.thread = None
    if 'log_text' not in st.session_state:
        st.session_state.log_text = ""
    if 'process_completed' not in st.session_state:
        st.session_state.process_completed = False

    USER_ID = st.session_state.USER_ID
    USER_SESSION_ID = st.session_state.USER_SESSION_ID

    def on_uploaded_file_data_kb_data_change(): 
        if st.session_state.uploaded_file_data_kb_data is None:
            return
        # Save the uploaded file
        pathlib.Path(f"temp/{USER_ID}/{USER_SESSION_ID}").mkdir(parents=True, exist_ok=True)
        with open(f"temp/{USER_ID}/{USER_SESSION_ID}/kb_data.txt", "wb") as f:
            f.write(st.session_state.uploaded_file_data.getvalue())

        main.upload_input_files("kb_data.txt", st.session_state.uploaded_file_data_kb_data.type, USER_ID, USER_SESSION_ID)

    def on_uploaded_file_data_change():
        if st.session_state.uploaded_file_data is None:
            return
        # Save the uploaded file
        pathlib.Path(f"temp/{USER_ID}/{USER_SESSION_ID}").mkdir(parents=True, exist_ok=True)
        with open(f"temp/{USER_ID}/{USER_SESSION_ID}/{st.session_state.uploaded_file_data.name}", "wb") as f:
            f.write(st.session_state.uploaded_file_data.getvalue())

    # Text input
    DATA_INFO_FROM_USER = st.text_input("What is this data about?")

    uploaded_file_data = st.file_uploader("Choose a file", key='uploaded_file_data', on_change=on_uploaded_file_data_change, help="Upload the data file you want to make AI ready. Do not that the file should be in JSONArray format. Greater the size longer it will take to process.")
    uploaded_file_data_kb_data = st.file_uploader("Choose a file", key='uploaded_file_data_kb_data', on_change=on_uploaded_file_data_kb_data_change)

    kb_urls = []

    # Text input with add button
    kb_url = st.text_input("Add KB URL")
    if st.button("Add"):
        kb_urls.append(kb_url)

    # Display all the URLs in the kb_urls list
    st.write("KB URLs")
    st.write(kb_urls)

    
#data.json -> orignal_data.json
#data.json
    # Add generate button
    generate = st.button("Generate")
    if generate and not st.session_state.generate_clicked:
        if st.session_state.uploaded_file_data is not None:
            st.session_state.generate_clicked = True
            print("Generate button clicked")
            #TODO : flat processing ()
            with open(f"temp/{USER_ID}/{USER_SESSION_ID}/kb_urls.json", "w") as f:
                kb_urls_dict = {"urls": kb_urls}
                json.dump(kb_urls_dict, f)
            # Start the thread
            args = (st.session_state.log_queue, USER_ID, USER_SESSION_ID, st.session_state.uploaded_file_data.name, DATA_INFO_FROM_USER)
            st.session_state.thread = threading.Thread(target=run_main_run_graph, args=args)
            st.session_state.thread.start()
        else:
            st.error("Please upload a data file before generating.")

    # Define placeholders for progress and logs
    progress_placeholder = st.empty()
    log_expander_placeholder = st.empty()

    if st.session_state.generate_clicked:
        # Check if the thread is alive
        thread_alive = st.session_state.thread is not None and st.session_state.thread.is_alive()
        
        if thread_alive:
            # Display the progress indicator
            with progress_placeholder.container():
                st.write("### Processing... ⏳")
                st.write("Please wait while we process your data.")
            
            # Update logs
            while not st.session_state.log_queue.empty():
                log_msg = st.session_state.log_queue.get()
                st.session_state.log_text += log_msg + "\n"
            
            # Display logs inside the expander
            with log_expander_placeholder.expander("Show logs", expanded=False):
                st.text_area("Logs", st.session_state.log_text, height=500)
            
            time.sleep(0.5)
            st.rerun()
        else:
            # Remove progress indicator
            progress_placeholder.empty()
            # Read any remaining logs
            while not st.session_state.log_queue.empty():
                log_msg = st.session_state.log_queue.get()
                st.session_state.log_text += log_msg + "\n"
            
            # Display logs inside the expander
            with log_expander_placeholder.expander("Show logs", expanded=False):
                st.text_area("Logs", st.session_state.log_text, height=200)
            # Display the output
            def post_download_process():
                st.session_state.generate_clicked = False
                USER_SESSION_ID = str(uuid4())
                USER_ID = str(uuid4())
                st.session_state.USER_ID = USER_ID
                st.session_state.USER_SESSION_ID = USER_SESSION_ID
                st.session_state.process_completed = False
                st.session_state.log_text = ""
                st.session_state.log_queue = queue.Queue()
                st.session_state.thread = None
                st.session_state.kb_urls = []

            try:
                changed_field_names_table =main.get_changes_to_field_names(USER_ID, USER_SESSION_ID)
                with st.expander("Changed Field Names", expanded=False):
                    st.table(changed_field_names_table)

                out_data_link = main.get_download_link( USER_ID, USER_SESSION_ID, "out.json")
                st.link_button("Download AI ready data", out_data_link)
            
            except FileNotFoundError:
                st.error("Output file not found. There might have been an error in processing.")
                
            # Reset the session state variables
            st.session_state.process_completed = True
            

    else:
        # Ensure placeholders are empty when not processing
        progress_placeholder.empty()
        log_expander_placeholder.empty()

if __name__ == "__main__":
    main_app()
