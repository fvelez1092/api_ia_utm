# from langchain_community.document_loaders import PDFPlumberLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_ollama import OllamaEmbeddings
# from app.config import config


# class EmbeddingService:
#     def __init__(self):
#         self.ollama_host = config.OLLAMA_HOST
#         self.model = config.EMBEDDING_MODEL
#         self.embeddings = OllamaEmbeddings(model=self.model, base_url=self.ollama_host)

#     def get_embeddings(self):
#         return self.embeddings

#     def generate_embeddings(self, file_path, batch_size=5):
#         loader = PDFPlumberLoader(file_path)
#         documents = loader.load()
#         splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000, chunk_overlap=200, add_start_index=True
#         )
#         chunks = splitter.split_documents(documents)

#         texts = [chunk.page_content for chunk in chunks]
#         metadatas = [
#             {"source": file_path, "chunk": i} for i, chunk in enumerate(chunks)
#         ]

#         return texts, metadatas
from typing import List, Tuple
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from app.config import config
from app.extensions import logger_app


class EmbeddingService:
    """
    Prepara chunks y metadatos desde un PDF para indexarlos en Chroma.
    Usa un modelo de embeddings de Ollama (DEBE ser un modelo de embeddings).
    """

    def __init__(self):
        self.ollama_host = getattr(config, "OLLAMA_HOST", "http://localhost:11434")
        # Ejemplo recomendado: "nomic-embed-text" o "bge-m3"
        self.model = getattr(config, "EMBEDDING_MODEL", "nomic-embed-text")

        self.embeddings = OllamaEmbeddings(
            model=self.model,
            base_url=self.ollama_host,
        )

    def get_embeddings(self) -> OllamaEmbeddings:
        return self.embeddings

    def _split_pdf(self, file_path: str) -> List[Document]:
        """
        Carga y trocea el PDF en documentos conservando metadatos útiles.
        """
        loader = PDFPlumberLoader(file_path)
        documents = loader.load()  # 1 doc por página con metadata {"source", "page"}

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True,
            separators=["\n\n", "\n", " ", ""],
        )

        chunks = splitter.split_documents(documents)
        for i, c in enumerate(chunks):
            meta = c.metadata or {}
            meta.setdefault("source", file_path)
            meta.setdefault("chunk_index", i)
            # Estandarizar nombre de la página
            if "page" not in meta and "page_number" in meta:
                meta["page"] = meta.get("page_number")
            c.metadata = meta
        return chunks

    def generate_embeddings(
        self, file_path: str, batch_size: int = 64
    ) -> Tuple[List[str], List[dict]]:
        """
        Devuelve texts y metadatas. LangChain-Chroma calculará los embeddings en add_texts().
        """
        try:
            chunks = self._split_pdf(file_path)
        except Exception as e:
            logger_app.error(f"[EmbeddingService] Error cargando/troceando PDF: {e}")
            raise

        texts = [c.page_content for c in chunks]
        metadatas = [c.metadata for c in chunks]

        logger_app.info(
            f"[EmbeddingService] '{file_path}' -> {len(texts)} chunks | emb_model='{self.model}'"
        )
        return texts, metadatas

    def ingest_pdf_into_chroma(
        self, chroma_service, file_path: str, batch_size: int = 64
    ) -> int:
        """
        Trocea el PDF y lo ingresa en Chroma en lotes. Retorna la cantidad de chunks indexados.
        """
        texts, metadatas = self.generate_embeddings(file_path, batch_size=batch_size)
        n = len(texts)
        if n == 0:
            logger_app.warning(
                f"[EmbeddingService] No se generaron chunks de '{file_path}'."
            )
            return 0

        chroma_service.add_embeddings(texts, metadatas, batch_size=batch_size)
        return n
