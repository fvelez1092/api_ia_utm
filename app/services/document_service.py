"""Almacenamiento e indexación segura de documentos PDF."""

import hashlib
import os
import tempfile
import uuid
from pathlib import Path

from werkzeug.utils import secure_filename

from app.config import config
from app.extensions import logger_app
from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService


class DocumentService:
    def __init__(self, upload_folder=None, embedding_service=None, chroma_service=None):
        self.pdfs_directory = Path(upload_folder or config.UPLOAD_FOLDER).resolve()
        self.pdfs_directory.mkdir(parents=True, exist_ok=True)
        self.embedding_service = embedding_service or EmbeddingService()
        self.chroma_service = chroma_service or ChromaService()

    @staticmethod
    def _hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def _file_hash(path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _existing_hashes(self):
        for path in self.pdfs_directory.glob("*.pdf"):
            if path.is_file():
                yield path, self._file_hash(path)

    def _destination(self, filename: str, document_hash: str) -> Path:
        candidate = self.pdfs_directory / filename
        if not candidate.exists():
            return candidate
        stem, suffix = candidate.stem, candidate.suffix
        return self.pdfs_directory / f"{stem}-{document_hash[:8]}{suffix}"

    def upload_and_vectorize(self, file, original_filename=None):
        filename = secure_filename(original_filename or file.filename or "")
        if not filename or not filename.lower().endswith(".pdf"):
            raise ValueError("Solo se aceptan archivos PDF.")

        content = file.read()
        if not content.startswith(b"%PDF-"):
            raise ValueError("El contenido no corresponde a un PDF válido.")

        document_hash = self._hash(content)
        for existing, existing_hash in self._existing_hashes():
            if existing_hash == document_hash:
                return {
                    "status": "duplicate",
                    "message": "El documento ya existe.",
                    "filename": existing.name,
                }

        destination = self._destination(filename, document_hash)
        temp_path = None
        index_started = False
        try:
            with tempfile.NamedTemporaryFile(
                dir=self.pdfs_directory, suffix=".pdf.tmp", delete=False
            ) as temporary:
                temporary.write(content)
                temp_path = Path(temporary.name)

            texts, metadatas = self.embedding_service.generate_embeddings(str(temp_path))
            if not texts:
                raise ValueError("El PDF no contiene texto indexable.")

            for index, metadata in enumerate(metadatas):
                metadata["source"] = destination.name
                metadata["filename"] = destination.name
                metadata["document_hash"] = document_hash
                metadata["chunk_index"] = index

            ids = [f"{document_hash}:{index}" for index in range(len(texts))]
            index_started = True
            self.chroma_service.add_embeddings(texts, metadatas, ids=ids)
            os.replace(temp_path, destination)
            temp_path = None

            return {
                "status": "success",
                "message": "Documento subido y vectorizado correctamente.",
                "filename": destination.name,
                "document_hash": document_hash,
                "num_chunks": len(texts),
            }
        except Exception:
            if index_started:
                try:
                    self.chroma_service.delete_by_document_hash(document_hash)
                except Exception:
                    logger_app.exception("No se pudo revertir la indexación del documento")
            raise
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()

    def list_documents(self, page=1, per_page=10):
        files = sorted(
            path for path in self.pdfs_directory.glob("*.pdf") if path.is_file()
        )
        start = (page - 1) * per_page
        documents = [
            {"filename": path.name, "modified_at": path.stat().st_mtime}
            for path in files[start : start + per_page]
        ]
        return {
            "page": page,
            "per_page": per_page,
            "total": len(files),
            "documents": documents,
        }

    def stats(self):
        """Resume el estado de los PDF y del índice vectorial."""
        files = [
            path for path in self.pdfs_directory.glob("*.pdf") if path.is_file()
        ]
        return {
            "documents": len(files),
            "indexed_chunks": self.chroma_service.count(),
            "total_size_bytes": sum(path.stat().st_size for path in files),
            "embedding_model": self.chroma_service.embedding_model,
            "collection_name": self.chroma_service.collection_name,
        }

    def delete_document(self, name: str):
        """Elimina un PDF y todos sus vectores, restaurándolo si Chroma falla."""
        path = self.resolve_document(name)
        if path is None:
            return None

        document_hash = self._file_hash(path)
        pending_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.deleting")
        os.replace(path, pending_path)
        try:
            self.chroma_service.delete_by_document_hash(document_hash)
        except Exception:
            os.replace(pending_path, path)
            raise

        try:
            pending_path.unlink()
        except OSError:
            logger_app.exception(
                "El PDF quedó pendiente de limpieza después de eliminar sus vectores: %s",
                pending_path,
            )
            raise
        return {"filename": path.name, "document_hash": document_hash}

    def reindex_all(self):
        """Reconstruye Chroma desde los PDF conservados en uploads."""
        prepared = []
        for path in sorted(self.pdfs_directory.glob("*.pdf")):
            if not path.is_file():
                continue
            document_hash = self._file_hash(path)
            texts, metadatas = self.embedding_service.generate_embeddings(str(path))
            if not texts:
                logger_app.warning("Se omitió el PDF sin texto: %s", path.name)
                continue
            for index, metadata in enumerate(metadatas):
                metadata["source"] = path.name
                metadata["filename"] = path.name
                metadata["document_hash"] = document_hash
                metadata["chunk_index"] = index
            ids = [f"{document_hash}:{index}" for index in range(len(texts))]
            prepared.append((path.name, texts, metadatas, ids))

        if not prepared:
            raise ValueError("No hay documentos PDF con texto para reindexar.")

        # Comprueba que el nuevo modelo responde antes de reemplazar el índice anterior.
        self.chroma_service.embedding_function.embed_query("prueba de conexión")
        self.chroma_service.reset()
        total_chunks = 0
        for filename, texts, metadatas, ids in prepared:
            total_chunks += self.chroma_service.add_embeddings(
                texts, metadatas, ids=ids
            )
            logger_app.info("Documento reindexado: %s (%s chunks)", filename, len(texts))
        return {"documents": len(prepared), "chunks": total_chunks}

    def resolve_document(self, name: str):
        safe_name = secure_filename(name)
        if safe_name != name or not safe_name.lower().endswith(".pdf"):
            return None
        path = (self.pdfs_directory / safe_name).resolve()
        if path.parent != self.pdfs_directory or not path.is_file():
            return None
        return path
