import os
from typing import List, Dict, Any, Optional
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# Set a fallback dummy API key if OPENAI_API_KEY is not set in environment
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-proj-API key in here"

# Path resolved relative to project_root to reach db directory
VECTOR_DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../db/chroma_rag"))

class RAGManager:
    def __init__(self):
        # Initializing embeddings with configured/fallback API Key
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.environ.get("OPENAI_API_KEY")
        )
        self.vector_store = Chroma(
            persist_directory=VECTOR_DB_DIR,
            embedding_function=self.embeddings,
            collection_name="privilege_policies"
        )

    def add_document(self, doc_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Dynamically add/update a document in Vector DB."""
        try:
            meta = metadata or {}
            meta["doc_id"] = doc_id
            doc = Document(page_content=content, metadata=meta)
            self.vector_store.add_documents(documents=[doc], ids=[doc_id])
            return True
        except Exception as e:
            print(f"Error adding document to RAG: {e}")
            return False

    def remove_document(self, doc_id: str) -> bool:
        """Dynamically remove a document from Vector DB by ID."""
        try:
            self.vector_store.delete(ids=[doc_id])
            return True
        except Exception as e:
            print(f"Error removing document from RAG: {e}")
            return False

    def retrieve_privilege_policy(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve applicable privilege review policies."""
        try:
            docs = self.vector_store.similarity_search(query, k=top_k)
            return [doc.page_content for doc in docs]
        except Exception as e:
            print(f"Retrieval note: {e}")
            return ["Default Privilege Standard: Flag confidential and attorney-client communications."]