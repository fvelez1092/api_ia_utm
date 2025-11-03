# from app.utils.response import create_response
# from flask import Blueprint, request
# from app.services.document_service import DocumentService
# from app.extensions import logger_app

# document_blueprint = Blueprint("Document", __name__, url_prefix="/document")
# document_service = DocumentService()


# @document_blueprint.route("/", methods=["POST"])
# def upload_document():
#     if "file" not in request.files:
#         return create_response("error", {"message": "No file part"}, 400)

#     file = request.files["file"]
#     if file.filename == "":
#         return create_response("error", {"message": "No selected file"}, 400)

#     try:
#         result = document_service.upload_and_vectorize(file)
#         if result["status"] == "duplicate":
#             return create_response("error", result, 409, result["message"])
#         return create_response("success", result, 201)
#     except Exception as e:
#         logger_app.error(f"Error en carga de documento: {str(e)}")
#         return create_response("error", {"message": str(e)}, 500, str(e))


# @document_blueprint.route("/", methods=["GET"])
# def list_documents():
#     try:
#         page = int(request.args.get("page", 1))
#         per_page = int(request.args.get("per_page", 10))
#         if page < 1 or per_page < 1:
#             return create_response("error", {"message": "Parámetros inválidos"}, 400)

#         result = document_service.list_documents(page, per_page)
#         return create_response("success", result, 200)
#     except Exception as e:
#         logger_app.error(f"Error al listar documentos: {str(e)}")
#         return create_response("error", {"message": str(e)}, 500, str(e))
from flask import (
    Blueprint,
    request,
    current_app,
    send_from_directory,
    abort,
)  # Añadir `current_app` para acceder a la configuración de Flask
from werkzeug.utils import secure_filename, safe_join  # Agregar esta importación
from app.utils.response import create_response
from app.services.embedding_service import EmbeddingService
from app.services.chroma_service import ChromaService
from app.services.document_service import DocumentService
from app.extensions import logger_app
import os

# Crear el servicio de documentos
document_service = DocumentService()

# Crear blueprint
document_blueprint = Blueprint("Document", __name__, url_prefix="/document")


@document_blueprint.route("/", methods=["POST"])
def upload_document():
    """
    Sube un archivo y lo vectoriza (indexa en Chroma).
    Requisitos:
      - Campo 'file' en multipart/form-data
      - Solo PDF (mimetype y extensión)
      - Tamaño máx: MAX_UPLOAD_MB
    Respuestas:
      - 201 success: { status, id, filename, chunks, message }
      - 409 duplicate
      - 400 error de validación
      - 500 error interno
    """
    try:
        # Validar que sea multipart/form-data con 'file'
        if "file" not in request.files:
            return create_response(
                "error", {"message": "Se requiere el campo 'file'."}, 400
            )

        # Límite de tamaño (obteniendo de la configuración de Flask)
        content_len = request.content_length or 0
        max_content_length = current_app.config.get(
            "MAX_CONTENT_LENGTH", 16 * 1024 * 1024
        )  # 16 MB por defecto

        if content_len > 0 and content_len > max_content_length:
            return create_response(
                "error",
                {
                    "message": f"El archivo excede el límite de {max_content_length / (1024 * 1024)} MB."
                },
                413,
                f"Tamaño: {content_len} bytes",
            )

        file = request.files["file"]

        # Nombre de archivo
        if not file or file.filename == "":
            return create_response(
                "error", {"message": "No se seleccionó archivo."}, 400
            )

        filename = secure_filename(
            file.filename
        )  # Usar secure_filename para sanear el nombre del archivo

        # Validaciones de extensión y mimetype
        if not filename.lower().endswith(".pdf"):
            return create_response(
                "error",
                {"message": "Extensión no permitida. Solo se aceptan archivos .pdf"},
                400,
            )

        # Algunos navegadores pueden enviar mimetype genérico; validamos si está disponible
        if file.mimetype and file.mimetype != "application/pdf":
            logger_app.warning(
                f"[Document] Mimetype no estándar: {file.mimetype} para '{filename}'"
            )

        logger_app.info(
            f"[Document] Subiendo '{filename}' (Content-Length={content_len} bytes)"
        )

        # Delegar al servicio (debe gestionar duplicados y vectorización)
        result = document_service.upload_and_vectorize(file, original_filename=filename)

        # Convención: el servicio devuelve {"status": "duplicate", "message": "..."} para duplicados
        if isinstance(result, dict) and result.get("status") == "duplicate":
            logger_app.info(f"[Document] Duplicado detectado: {filename} -> 409")
            return create_response("error", result, 409, result.get("message"))

        # Éxito
        return create_response("success", result, 201)

    except Exception as e:
        logger_app.error(f"Error en carga de documento: {e}", exc_info=True)
        return create_response(
            "error", {"message": "Error interno al procesar el documento."}, 500, str(e)
        )


@document_blueprint.route("/", methods=["GET"])
def list_documents():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        if page < 1 or per_page < 1:
            return create_response("error", {"message": "Parámetros inválidos"}, 400)

        result = document_service.list_documents(page, per_page)
        return create_response("success", result, 200)
    except Exception as e:
        logger_app.error(f"Error al listar documentos: {str(e)}")
        return create_response("error", {"message": str(e)}, 500, str(e))


@document_blueprint.route("/view", methods=["GET"])
def view_document():
    name = request.args.get("name")
    if not name:
        return create_response("error", {"message": "Falta el parámetro 'name'."}, 400)

    # lista blanca: sólo archivos realmente en el directorio
    files = set(os.listdir(document_service.pdfs_directory))
    if name not in files:
        return create_response("error", {"message": "Documento no encontrado."}, 404)

    # safe join para evitar path traversal
    safe_path = safe_join(document_service.pdfs_directory, name)
    if not safe_path or not os.path.isfile(safe_path):
        return create_response("error", {"message": "Ruta inválida."}, 400)

    # servir como PDF inline
    return send_from_directory(
        directory=document_service.pdfs_directory,
        path=name,
        mimetype="application/pdf",
        as_attachment=False,
        conditional=True,
        max_age=0,  # desactiva cache si prefieres
    )
