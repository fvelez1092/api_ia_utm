from flask import Blueprint, current_app, request, send_from_directory
from flask_jwt_extended import jwt_required

from app.extensions import limiter, logger_app
from app.services.chroma_service import ChromaService
from app.services.document_service import DocumentService
from app.utils.auth import admin_required
from app.utils.response import create_response


document_blueprint = Blueprint("Document", __name__, url_prefix="/document")


def _service():
    if "document_service" not in current_app.extensions:
        if "chroma_service" not in current_app.extensions:
            current_app.extensions["chroma_service"] = ChromaService(
                persist_directory=current_app.config["CHROMA_PATH"],
                collection_name=current_app.config["COLLECTION_NAME"],
                embedding_model=current_app.config["EMBEDDING_MODEL"],
                ollama_host=current_app.config["OLLAMA_HOST"],
            )
        current_app.extensions["document_service"] = DocumentService(
            upload_folder=current_app.config["UPLOAD_FOLDER"],
            chroma_service=current_app.extensions["chroma_service"],
        )
    return current_app.extensions["document_service"]


@document_blueprint.post("/")
@limiter.limit("10 per hour")
@admin_required()
def upload_document():
    if "file" not in request.files or not request.files["file"].filename:
        return create_response(
            "error", message="Se requiere un archivo en el campo 'file'.", status_code=400
        )

    file = request.files["file"]
    try:
        result = _service().upload_and_vectorize(file, file.filename)
    except ValueError as error:
        return create_response("error", message=str(error), status_code=400)
    except Exception:
        logger_app.exception("Error al procesar el documento")
        return create_response(
            "error", message="No se pudo procesar el documento.", status_code=500
        )

    if result["status"] == "duplicate":
        return create_response("error", data=result, message=result["message"], status_code=409)
    return create_response("success", data=result, status_code=201)


@document_blueprint.get("/")
@jwt_required()
def list_documents():
    try:
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 10)), 100)
    except (TypeError, ValueError):
        return create_response("error", message="Paginación inválida.", status_code=400)
    if page < 1 or per_page < 1:
        return create_response("error", message="Paginación inválida.", status_code=400)
    return create_response(
        "success", data=_service().list_documents(page, per_page), status_code=200
    )


@document_blueprint.get("/view")
@jwt_required()
def view_document():
    name = request.args.get("name", "")
    path = _service().resolve_document(name)
    if path is None:
        return create_response("error", message="Documento no encontrado.", status_code=404)
    return send_from_directory(
        directory=str(path.parent),
        path=path.name,
        mimetype="application/pdf",
        as_attachment=False,
        conditional=True,
        max_age=0,
    )
