from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv
import shutil

load_dotenv()

# Global variables
retriever = None
current_file_name = None

def load_docx_whith_langchain_and_split(file_path, chunk_size=3000, chunk_overlap=400):
    try:
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path=file_path)
        elif file_path.endswith(".docx"):
            loader = Docx2txtLoader(file_path=file_path)
        
        documents = loader.load()
        
        text_spliter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        
        splits = text_spliter.split_documents(documents=documents)
        
        return splits
        
    except Exception as e:
        print(f"Error loading document: {e}")
        return None

def setup_vector_store(file_path):
    global retriever, current_file_name
    
    splits = load_docx_whith_langchain_and_split(file_path)
    
    if splits is None:
        print("Không load được file")
        return False
    
    embeding = OpenAIEmbeddings(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="text-embedding-ada-002"
    )
    
    db_location = "./chrome_langchain_db"
    
    # Remove existing database
    if os.path.exists(db_location):
        shutil.rmtree(db_location)
    
    vector_store = Chroma(
        collection_name="doc_review",
        persist_directory=db_location,
        embedding_function=embeding
    )
    
    vector_store.add_documents(splits, ids=[f"chunk_{i}" for i in range(len(splits))])
    
    retriever = vector_store.as_retriever(search_kwargs={"k": 20})
    current_file_name = os.path.basename(file_path)
    
    print(f"Đã setup vector store với {len(splits)} chunks từ file {current_file_name}")
    return True

def get_retriever():
    return retriever

def get_current_file():
    return current_file_name

def clear_vector_store():
    """Clear vector store"""
    global retriever, current_file_name
    db_location = "./chrome_langchain_db"
    if os.path.exists(db_location):
        shutil.rmtree(db_location)
    retriever = None
    current_file_name = None