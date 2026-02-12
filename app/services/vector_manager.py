import chromadb
from chromadb.utils import embedding_functions
import os
import torch
import uuid


class VectorManager:
    def __init__(self, persist_path="data/vector_store"):
        # Ensure the storage directory exists
        if not os.path.exists(persist_path):
            os.makedirs(persist_path)

        self.client = chromadb.PersistentClient(path=persist_path)

        # Use industrial-grade BGE-M3 model with auto device detection
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-m3",
            device=device
        )

        # Create or get collection with cosine similarity for semantic matching
        # Using a new collection name for the independent storage to avoid conflicts
        self.collection = self.client.get_or_create_collection(
            name="deepgloss_independent_vdb",
            embedding_function=self.emb_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def add_sentences_independent(self, sentence_list, domain_id):
        """
        Store sentences directly in VectorDB with independent IDs.
        sentence_list: list of strings (raw sentences)
        """
        if not sentence_list: return

        # Generate unique IDs since these are independent of SQLite
        ids = [str(uuid.uuid4()) for _ in sentence_list]
        documents = sentence_list
        metadatas = [{"domain_id": str(domain_id)} for _ in sentence_list]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search_similar_text(self, query_text, domain_id, n_results=5):
        """
        Search for semantically similar text directly.
        Returns a list of strings (raw sentences).
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where={"domain_id": str(domain_id)}
            )
            # ChromaDB returns a list of lists (one per query), we take the first list
            if results['documents'] and len(results['documents'][0]) > 0:
                return results['documents'][0]
        except Exception as e:
            print(f"Vector search error: {e}")
        return []