import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

class KnowledgeBaseRetriever:
    def __init__(self, db_path="./chroma_db"):
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"ChromaDB directory at '{db_path}' not found.")
            
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        self.vectorstore = Chroma(
            collection_name="singapore_travel",
            embedding_function=embeddings,
            persist_directory=db_path
        )
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})

    def retrieve_context(self, query: str) -> str:
        docs = self.retriever.invoke(query)
        if not docs:
            return "NO RELEVANT KNOWLEDGE BASE INFORMATION FOUND."

        formatted_context = "=== RETRIEVED TRAVEL KNOWLEDGE BASE FACTS ===\n"
        for i, doc in enumerate(docs, 1):
            source_file = os.path.basename(doc.metadata.get("source", "Unknown"))
            formatted_context += f"[Source Chunk {i} | File: {source_file}]\n{doc.page_content}\n\n"
            
        return formatted_context