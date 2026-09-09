"""Inicialización segura de los servicios compartidos por la API."""

from threading import RLock

from flask import current_app

from app.services.chroma_service import ChromaService
from app.services.document_service import DocumentService


_chroma_lock = RLock()
_document_lock = RLock()


def get_chroma_service():
    """Devuelve una única instancia de Chroma por aplicación, incluso con hilos."""
    service = current_app.extensions.get("chroma_service")
    if service is not None:
        return service

    with _chroma_lock:
        service = current_app.extensions.get("chroma_service")
        if service is None:
            service = ChromaService(
                persist_directory=current_app.config["CHROMA_PATH"],
                collection_name=current_app.config["COLLECTION_NAME"],
                embedding_model=current_app.config["EMBEDDING_MODEL"],
                ollama_host=current_app.config["OLLAMA_HOST"],
            )
            current_app.extensions["chroma_service"] = service
    return service


def get_document_service():
    """Devuelve una única instancia del servicio documental por aplicación."""
    service = current_app.extensions.get("document_service")
    if service is not None:
        return service

    with _document_lock:
        service = current_app.extensions.get("document_service")
        if service is None:
            service = DocumentService(
                upload_folder=current_app.config["UPLOAD_FOLDER"],
                chroma_service=get_chroma_service(),
            )
            current_app.extensions["document_service"] = service
    return service
