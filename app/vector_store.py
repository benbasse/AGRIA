# app/vector_store.py
import os
import chromadb

class VectorStoreManager:
    def __init__(self, config):
        persist_dir = config.get("CHROMA_PERSIST_DIR", "./chroma_db")
        os.makedirs(persist_dir, exist_ok=True)

        # Nouvelle API Chroma v1.1+
        self.client = chromadb.PersistentClient(path=persist_dir)

    def add_documents_chroma(self, collection_name, ids, metadatas, documents, embeddings):
        collection = self.client.get_or_create_collection(collection_name)
        collection.add(
            ids=ids,
            metadatas=metadatas,
            documents=documents,
            embeddings=embeddings
        )

    def query_chroma(self, collection_name, query_embeddings, n_results=4):
        collection = self.client.get_or_create_collection(collection_name)
        results = collection.query(
            query_embeddings=[query_embeddings],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        return results
