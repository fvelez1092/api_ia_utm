from app.utils.response import create_response
from flask import Blueprint, request
from app.services.document_service import DocumentService
from app.extensions import logger_app

document_blueprint = Blueprint("Document", __name__, url_prefix="/document")
document_service = DocumentService()


@document_blueprint.route("/", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return create_response("error", {"message": "No file part"}, 400)

    file = request.files["file"]
    if file.filename == "":
        return create_response("error", {"message": "No selected file"}, 400)

    try:
        result = document_service.upload_and_vectorize(file)
        if result["status"] == "duplicate":
            return create_response("error", result, 409, result["message"])
        return create_response("success", result, 201)
    except Exception as e:
        logger_app.error(f"Error en carga de documento: {str(e)}")
        return create_response("error", {"message": str(e)}, 500, str(e))


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
