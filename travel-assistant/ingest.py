import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

def build_vector_store(data_dir="./data", db_path="./chroma_db"):
    print("Loading knowledge base documents...")
    
    docs = []
    
    # 1. Load Text Files (.txt)
    txt_loader = DirectoryLoader(data_dir, glob="*.txt", loader_cls=TextLoader)
    docs.extend(txt_loader.load())

    # 2. Load PDF Files (.pdf)
    pdf_loader = DirectoryLoader(data_dir, glob="*.pdf", loader_cls=PyPDFLoader)
    docs.extend(pdf_loader.load())

    print(f"Loaded a total of {len(docs)} document pages/files.")

    # Split text into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Created {len(chunks)} text chunks.")

    # Generate Embeddings & Save to ChromaDB
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )

    print(f"Storing chunks in ChromaDB at '{db_path}'...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="singapore_travel",
        persist_directory=db_path
    )
    print(f"ChromaDB successfully updated at '{db_path}'.")

if __name__ == "__main__":
    build_vector_store()