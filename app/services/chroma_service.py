from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from app.config import config
from app.extensions import logger_app


class ChromaService:
    def __init__(self):
        self.persist_directory = config.CHROMA_PATH
        # Embeddings con Ollama
        self.embedding_function = OllamaEmbeddings(
            model=config.EMBEDDING_MODEL, base_url=config.OLLAMA_HOST
        )
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function,
        )

    def add_embeddings(self, texts, metadatas):
        try:
            self.vector_store.add_texts(texts=texts, metadatas=metadatas)
            self.vector_store.persist()
        except Exception as e:
            logger_app.error(f"Error al agregar embeddings a Chroma: {str(e)}")
            raise e  # relanzar para que DocumentService también lo capture

    def search(self, query, k=3):
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            logger_app.error(f"Error al buscar en Chroma: {str(e)}")
            return []
