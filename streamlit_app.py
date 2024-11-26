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

    # Text input
    DATA_INFO_FROM_USER = st.text_input("What is this data about?")

    uploaded_file_data = st.file_uploader("Choose a file", key='uploaded_file_data')
    uploaded_file_data_kb_data = st.file_uploader("Choose a file", key='uploaded_file_data_kb_data')

    kb_urls = []

    # Text input with add button
    kb_url = st.text_input("Add KB URL")
    if st.button("Add"):
        kb_urls.append(kb_url)

    # Display all the URLs in the kb_urls list
    st.write("KB URLs")
    st.write(kb_urls)

    if uploaded_file_data_kb_data is not None:
        # Save the uploaded file
        pathlib.Path(f"temp/{USER_ID}/{USER_SESSION_ID}").mkdir(parents=True, exist_ok=True)
        with open(f"temp/{USER_ID}/{USER_SESSION_ID}/kb_data.txt", "wb") as f:
            f.write(uploaded_file_data_kb_data.getvalue())

        main.upload_input_files("kb_data.txt", uploaded_file_data_kb_data.type, USER_ID, USER_SESSION_ID)

    if uploaded_file_data is not None:
        # Save the uploaded file
        pathlib.Path(f"temp/{USER_ID}/{USER_SESSION_ID}").mkdir(parents=True, exist_ok=True)
        with open(f"temp/{USER_ID}/{USER_SESSION_ID}/{uploaded_file_data.name}", "wb") as f:
            f.write(uploaded_file_data.getvalue())
#data.json -> orignal_data.json
#data.json
    # Add generate button
    generate = st.button("Generate")
    if generate and not st.session_state.generate_clicked:
        if uploaded_file_data is not None:
            st.session_state.generate_clicked = True
            print("Generate button clicked")
            #TODO : flat processing ()
            main.upload_input_files(uploaded_file_data.name, uploaded_file_data.type, USER_ID, USER_SESSION_ID)
            print("Files uploaded")
            
            # Start the thread
            args = (st.session_state.log_queue, USER_ID, USER_SESSION_ID, uploaded_file_data.name, DATA_INFO_FROM_USER)
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
                st.text_area("Logs", st.session_state.log_text, height=200)
            
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
            try:
                with open(f"temp/{USER_ID}/{USER_SESSION_ID}/out.json", "r") as f:
                    out = json.load(f)
                    st.download_button(label="Download AI ready data", data=json.dumps(out), file_name="out.json", mime="application/json")
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
