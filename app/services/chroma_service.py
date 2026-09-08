"""Acceso a la base vectorial ChromaDB."""

from typing import List, Optional, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from app.config import config
from app.extensions import logger_app


class ChromaService:
    def __init__(
        self,
        persist_directory=None,
        collection_name=None,
        embedding_model=None,
        ollama_host=None,
    ):
        self.persist_directory = persist_directory or config.CHROMA_PATH
        self.collection_name = collection_name or config.COLLECTION_NAME
        self.embedding_model = embedding_model or config.EMBEDDING_MODEL
        self.ollama_host = ollama_host or config.OLLAMA_HOST
        self.embedding_function = OllamaEmbeddings(
            model=self.embedding_model, base_url=self.ollama_host
        )
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function,
        )

    def add_embeddings(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
        batch_size: int = 64,
    ) -> int:
        metadatas = metadatas or [{} for _ in texts]
        if len(metadatas) != len(texts):
            raise ValueError("texts y metadatas deben tener la misma longitud")
        if ids is not None and len(ids) != len(texts):
            raise ValueError("texts e ids deben tener la misma longitud")

        for start in range(0, len(texts), batch_size):
            end = min(start + batch_size, len(texts))
            self.vector_store.add_texts(
                texts=texts[start:end],
                metadatas=metadatas[start:end],
                ids=ids[start:end] if ids else None,
            )
        return len(texts)

    def delete_by_document_hash(self, document_hash: str) -> None:
        self.vector_store._collection.delete(where={"document_hash": document_hash})

    def search(self, query: str, k: int = 3) -> List[Document]:
        return self.vector_store.similarity_search(query, k=k)

    def search_with_scores(
        self, query: str, k: int = 5
    ) -> List[Tuple[Document, float]]:
        return self.vector_store.similarity_search_with_score(query, k=k)

    def count(self) -> Optional[int]:
        return self.vector_store._collection.count()

    def as_retriever(self, k: int = 4):
        return self.vector_store.as_retriever(search_kwargs={"k": k})

    def reset(self) -> None:
        self.vector_store.delete_collection()
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function,
        )
        logger_app.info("Colección Chroma recreada: %s", self.collection_name)
