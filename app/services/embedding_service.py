from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from app.config import config


class EmbeddingService:
    def __init__(self):
        self.ollama_host = config.OLLAMA_HOST
        self.model = config.EMBEDDING_MODEL
        self.embeddings = OllamaEmbeddings(model=self.model, base_url=self.ollama_host)

    def get_embeddings(self):
        return self.embeddings

    def generate_embeddings(self, file_path, batch_size=5):
        loader = PDFPlumberLoader(file_path)
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, add_start_index=True
        )
        chunks = splitter.split_documents(documents)

        texts = [chunk.page_content for chunk in chunks]
        metadatas = [
            {"source": file_path, "chunk": i} for i, chunk in enumerate(chunks)
        ]

        return texts, metadatas
