import chromadb
from chromadb.utils import embedding_functions
import os
import torch


class VectorManager:
    def __init__(self, persist_path="data/vector_store"):
        if not os.path.exists(persist_path):
            os.makedirs(persist_path)

        self.client = chromadb.PersistentClient(path=persist_path)

        # 使用工业级 BGE-M3 模型，自动检测设备
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-m3",
            device=device
        )

        # 创建或获取向量集合
        self.collection = self.client.get_or_create_collection(
            name="deepgloss_bge_m3",
            embedding_function=self.emb_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def add_sentences(self, sentences, domain_id):
        """批量添加句子到向量库，sentences 结构: [{'id': int, 'content': str}]"""
        if not sentences: return
        ids = [str(s['id']) for s in sentences]
        documents = [s['content'] for s in sentences]
        metadatas = [{"domain_id": str(domain_id), "sqlite_id": s['id']} for s in sentences]

        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def search_similar_ids(self, query_text, domain_id, n_results=5):
        """语义搜索，返回最相似句子的 SQLite ID 列表"""
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where={"domain_id": str(domain_id)}
            )
            if results['ids'] and len(results['ids'][0]) > 0:
                return [int(id_str) for id_str in results['ids'][0]]
        except Exception:
            pass
        return []