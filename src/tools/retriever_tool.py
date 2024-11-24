from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
import json

def get_retriever(user_id, user_session_id, model_name='text-embedding-3-small'):

    temp_dir = f"temp/{user_id}/{user_session_id}"

    #check if kb_urls.json exists
    try:
        with open(f"{temp_dir}/kb_urls.json", "r") as f:
            urls = json.load(f)
    except:
        urls = []
    
    #check if kb_data.txt exists
    try:
        with open(f"{temp_dir}/kb_data.txt", "r") as f:
            kb_docs = f.readlines()
    except:
        kb_docs = []

    docs = [WebBaseLoader(url).load() for url in urls]
    docs_list = [item for sublist in docs for item in sublist]
    docs_list.extend(kb_docs)

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=100, chunk_overlap=50
    )
    doc_splits = text_splitter.split_documents(docs_list)

    # Add to vectorDB
    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        collection_name="rag-chroma",
        embedding=OpenAIEmbeddings(model=model_name),
    )
    retriever = vectorstore.as_retriever()

    return retriever

    
        


    