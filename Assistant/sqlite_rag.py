from .openai_embedding_provider import OpenAIEmbeddingProvider
from .vllm_reranker_provider import VLLMRerankerProvider
from .logging_config import get_logger

import sqlite_vec
import sqlite3
import struct
import os
from typing import Optional

logger = get_logger("kb")


class VectorDB_kb:
    embed_provider: OpenAIEmbeddingProvider
    rerank_provider: Optional[VLLMRerankerProvider]
    embed_model_name: str
    rerank_model_name: Optional[str]
    db_path: str
    n_dims: int

    def __init__(
        self,
        emb_model_provider: OpenAIEmbeddingProvider,
        emb_model_name: str,
        rerank_model_provider: Optional[VLLMRerankerProvider] = None,
        rerank_model_name: Optional[str] = None,
        db_path: str = "default_kb.db",
        n_dims: int = 512,
    ):
        self.embed_provider = emb_model_provider
        self.embed_model_name = emb_model_name
        self.rerank_provider = rerank_model_provider
        self.rerank_model_name = rerank_model_name
        self.db_path = db_path
        self.n_dims = n_dims
        self.conn = sqlite3.connect(db_path)
        self.conn.enable_load_extension(True)
        vec0_path = os.path.join(os.path.dirname(sqlite_vec.__file__), "vec0.dylib")
        self.conn.execute(f"SELECT load_extension('{vec0_path}')")
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.conn.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents USING vec0(
                id INTEGER PRIMARY KEY,
                content TEXT,
                embedding FLOAT[{self.n_dims}]
            )
        """)
        self.conn.commit()

    def _vector_to_bytes(self, vector: list[float]) -> bytes:
        """将向量转换为 sqlite-vec 需要的字节格式"""
        return struct.pack(f"{len(vector)}f", *vector)

    def add_document(self, text: str) -> int:
        """添加单个文档，返回文档 ID"""
        logger.debug(f"添加文档: {text[:50]}...")
        vector = self.embed_provider.embed_single(self.embed_model_name, text)
        vector_bytes = self._vector_to_bytes(vector)
        self.cursor.execute(
            "INSERT INTO documents (content, embedding) VALUES (?, ?)",
            (text, vector_bytes)
        )
        self.conn.commit()
        doc_id = self.cursor.lastrowid
        logger.info(f"文档添加成功, id={doc_id}")
        return doc_id

    def add_documents(self, texts: list[str]) -> list[int]:
        """批量添加文档，返回文档 ID 列表"""
        vectors = self.embed_provider.embed_batch(self.embed_model_name, texts)
        ids = []
        for text, vector in zip(texts, vectors):
            vector_bytes = self._vector_to_bytes(vector)
            self.cursor.execute(
                "INSERT INTO documents (content, embedding) VALUES (?, ?)",
                (text, vector_bytes)
            )
            ids.append(self.cursor.lastrowid)
        self.conn.commit()
        return ids

    def search(
        self,
        query: str,
        top_k: int = 5,
        ann_k: int = 20,
        use_rerank: bool = True,
    ) -> list[dict]:
        """搜索文档

        Args:
            query: 查询文本
            top_k: 最终返回数量
            ann_k: ANN 检索候选数量（粗排）
            use_rerank: 是否使用 rerank 精排

        Returns:
            list[dict]: [{"id": int, "content": str, "score": float}, ...]
        """
        query_vector = self.embed_provider.embed_single(self.embed_model_name, query)
        query_bytes = self._vector_to_bytes(query_vector)

        self.cursor.execute("""
            SELECT id, content, distance
            FROM documents
            WHERE embedding MATCH ?
            LIMIT ?
        """, (query_bytes, ann_k))
        candidates = self.cursor.fetchall()

        if not candidates:
            logger.warning(f"未找到相关文档: {query}")
            return []

        logger.debug(f"ANN 检索到 {len(candidates)} 个候选文档")

        if use_rerank and self.rerank_provider and self.rerank_model_name:
            docs = [c[1] for c in candidates]
            reranked = self.rerank_provider.rerank_with_scores(
                self.rerank_model_name,
                query=query,
                documents=docs,
                top_k=top_k,
            )
            id_to_doc = {c[1]: c[0] for c in candidates}
            seen = set()
            results = []
            for doc, score in reranked:
                if doc and doc not in seen:
                    seen.add(doc)
                    results.append({"id": id_to_doc.get(doc), "content": doc, "score": score})
            return results

        return [
            {"id": c[0], "content": c[1], "score": -c[2]}
            for c in candidates[:top_k]
        ]

    def delete_document(self, doc_id: int) -> bool:
        """删除文档"""
        self.cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def count(self) -> int:
        """返回文档总数"""
        self.cursor.execute("SELECT COUNT(*) FROM documents")
        return self.cursor.fetchone()[0]

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_: any) -> None:
        self.close()