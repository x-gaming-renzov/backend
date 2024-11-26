from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
import json
import uuid

def get_retriever(user_id, user_session_id, data_info_from_user, model_name='text-embedding-3-small'):

    temp_dir = f"temp/{user_id}/{user_session_id}"

    #check if kb_urls.json exists
    try:
        with open(f"{temp_dir}/kb_urls.json", "r") as f:
            urls = json.load(f)['urls']
    except:
        urls = []
    
    #check if kb_data.txt exists
    try:
        with open(f"{temp_dir}/kb_data.txt", "r") as f:
            kb_docs = f.readlines()
            kb_docs = CharacterTextSplitter().create_documents(kb_docs)

    except:
        kb_docs = []

    docs = [WebBaseLoader(url).load() for url in urls]
    docs_list = [item for sublist in docs for item in sublist]
    docs_list.extend(CharacterTextSplitter().create_documents([data_info_from_user, "not much to say", "not much to say", "not much to say"]))
    docs_list.extend(kb_docs)

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=100, chunk_overlap=50
    )
    doc_splits = text_splitter.split_documents(docs_list)

    try:
        # Add to vectorDB
        vectorstore = Chroma.from_documents(
            documents=doc_splits,
            collection_name=str(uuid.uuid4().hex),
            embedding=OpenAIEmbeddings(model=model_name),
            persist_directory=temp_dir,
        )
    except:
        vectorstore = Chroma(
            collection_name=str(uuid.uuid4().hex),
            embedding_function=OpenAIEmbeddings(model=model_name),
            persist_directory=temp_dir,
        )

    
    retriever = vectorstore.as_retriever()

    return retriever

    
        


    