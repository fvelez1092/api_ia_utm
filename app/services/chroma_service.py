# # from langchain_chroma import Chroma
# from langchain_community.vectorstores import Chroma
# from langchain_ollama import OllamaEmbeddings
# from app.config import config
# from app.extensions import logger_app


# class ChromaService:
#     def __init__(self):
#         self.persist_directory = config.CHROMA_PATH
#         # Embeddings con Ollama
#         self.embedding_function = OllamaEmbeddings(
#             model=config.EMBEDDING_MODEL, base_url=config.OLLAMA_HOST
#         )
#         self.vector_store = Chroma(
#             persist_directory=self.persist_directory,
#             embedding_function=self.embedding_function,
#         )

#     def add_embeddings(self, texts, metadatas):
#         try:
#             self.vector_store.add_texts(texts=texts, metadatas=metadatas)
#             self.vector_store.persist()
#         except Exception as e:
#             logger_app.error(f"Error al agregar embeddings a Chroma: {str(e)}")
#             raise e  # relanzar para que DocumentService también lo capture

#     def search(self, query, k=3):
#         try:
#             return self.vector_store.similarity_search(query, k=k)
#         except Exception as e:
#             logger_app.error(f"Error al buscar en Chroma: {str(e)}")
#             return []
from __future__ import annotations

from typing import List, Tuple, Optional
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from app.config import config
from app.extensions import logger_app


class ChromaService:
    """
    Servicio de acceso a ChromaDB vía LangChain.
    Requiere que el modelo de embeddings de Ollama esté disponible.
    """

    def __init__(self):
        self.persist_directory = getattr(config, "CHROMA_PATH", "./.chroma")
        self.collection_name = getattr(config, "CHROMA_COLLECTION", "rag_docs")
        self.embedding_model = getattr(config, "EMBEDDING_MODEL", "nomic-embed-text")
        self.ollama_host = getattr(config, "OLLAMA_HOST", "http://localhost:11434")

        # Debe ser un modelo de EMBEDDINGS
        self.embedding_function = OllamaEmbeddings(
            model=self.embedding_model,
            base_url=self.ollama_host,
        )

        # Inicializa/abre la colección persistente
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function,
        )

        logger_app.info(
            f"[ChromaService] init | collection='{self.collection_name}' | "
            f"path='{self.persist_directory}' | emb_model='{self.embedding_model}'"
        )

    # ---------- Ingesta ----------
    def add_embeddings(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        batch_size: int = 64,
    ) -> int:
        """
        Agrega textos + metadatos al índice. Persiste en disco.
        Retorna la cantidad agregada.
        """
        metadatas = metadatas or [{} for _ in texts]
        if len(metadatas) != len(texts):
            raise ValueError("texts y metadatas deben tener la misma longitud")

        n = len(texts)
        if n == 0:
            logger_app.warning("[ChromaService] add_embeddings: lista vacía")
            return 0

        try:
            for start in range(0, n, batch_size):
                end = min(start + batch_size, n)
                self.vector_store.add_texts(
                    texts=texts[start:end], metadatas=metadatas[start:end]
                )
                logger_app.info(
                    f"[ChromaService] add_embeddings: {end}/{n} chunks indexados..."
                )
            self.vector_store.persist()
            logger_app.info(f"[ChromaService] persist -> OK | total agregados: {n}")
            return n
        except Exception as e:
            logger_app.error(f"[ChromaService] Error al agregar embeddings: {e}")
            raise

    # ---------- Búsqueda ----------
    def search(self, query: str, k: int = 3) -> List[Document]:
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            logger_app.info(f"[ChromaService] search k={k} -> {len(docs)} docs")
            return docs
        except Exception as e:
            logger_app.error(f"[ChromaService] Error en search: {e}")
            return []

    def search_with_scores(
        self, query: str, k: int = 5
    ) -> List[Tuple[Document, float]]:
        """
        Búsqueda con scores. Nota: en Chroma vía LangChain, score más bajo suele ser más similar.
        """
        try:
            pairs = self.vector_store.similarity_search_with_score(
                query, k=k
            )  # List[(Document, score)]
            logger_app.info(
                f"[ChromaService] search_with_scores k={k} -> {len(pairs)} (min_score={min([s for _, s in pairs]) if pairs else 'n/a'})"
            )
            return pairs
        except Exception as e:
            logger_app.error(f"[ChromaService] Error en search_with_scores: {e}")
            return []

    # ---------- Utilidades ----------
    def count(self) -> Optional[int]:
        try:
            return self.vector_store._collection.count()  # type: ignore[attr-defined]
        except Exception as e:
            logger_app.warning(f"[ChromaService] count() no disponible: {e}")
            return None

    def as_retriever(self, k: int = 4):
        try:
            return self.vector_store.as_retriever(search_kwargs={"k": k})
        except Exception as e:
            logger_app.error(f"[ChromaService] Error creando retriever: {e}")
            raise

    def reset(self) -> None:
        try:
            self.vector_store.delete_collection()
            logger_app.info(
                f"[ChromaService] Colección '{self.collection_name}' eliminada."
            )
            # recrear para que quede lista
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_function,
            )
            logger_app.info(
                f"[ChromaService] Colección '{self.collection_name}' recreada."
            )
        except Exception as e:
            logger_app.error(f"[ChromaService] Error al resetear colección: {e}")
            raise
