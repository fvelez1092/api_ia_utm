import math

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required

from app.extensions import limiter, logger_app
from app.services.chroma_service import ChromaService
from app.services.rag_service import RAGService
from app.utils.response import create_response


rag_blueprint = Blueprint("RAG", __name__, url_prefix="/rag")


def _safe_int(value, default, min_v=1, max_v=20):
    try:
        return max(min(int(value), max_v), min_v)
    except (TypeError, ValueError):
        return default


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    raise ValueError("'use_scores' debe ser true o false.")


def _is_greeting(question: str) -> bool:
    normalized = question.lower().strip(" ¡!¿?.")
    return normalized in {
        "hola",
        "buenos días",
        "buenas tardes",
        "buenas noches",
        "gracias",
        "adiós",
        "hasta luego",
    }


def _chroma_service():
    if "chroma_service" not in current_app.extensions:
        current_app.extensions["chroma_service"] = ChromaService(
            persist_directory=current_app.config["CHROMA_PATH"],
            collection_name=current_app.config["COLLECTION_NAME"],
            embedding_model=current_app.config["EMBEDDING_MODEL"],
            ollama_host=current_app.config["OLLAMA_HOST"],
        )
    return current_app.extensions["chroma_service"]


@rag_blueprint.post("/ask")
@limiter.limit("30 per minute")
@jwt_required()
def ask_question():
    if not request.is_json:
        return create_response("error", message="Se requiere JSON.", status_code=415)

    data = request.get_json(silent=True) or {}
    question = str(data.get("question") or "").strip()
    if not question:
        return create_response(
            "error", message="El campo 'question' es requerido.", status_code=400
        )
    if len(question) > current_app.config["RAG_MAX_QUESTION_LENGTH"]:
        return create_response("error", message="La pregunta es demasiado larga.", status_code=400)
    if _is_greeting(question):
        return create_response(
            "success",
            data={"answer": "¡Hola! ¿En qué puedo ayudarte?", "sources": []},
            status_code=200,
        )

    try:
        use_scores = _parse_bool(data.get("use_scores", True))
        threshold_value = data.get("score_threshold")
        score_threshold = (
            current_app.config["RAG_SCORE_THRESHOLD"]
            if threshold_value is None
            else float(threshold_value)
        )
        if not math.isfinite(score_threshold) or not 0 <= score_threshold <= 10:
            raise ValueError("'score_threshold' debe estar entre 0 y 10.")
    except (TypeError, ValueError) as error:
        return create_response("error", message=str(error), status_code=400)

    k = _safe_int(data.get("n_context", 5), default=5, min_v=1, max_v=15)
    try:
        chroma = _chroma_service()
        if chroma.count() == 0:
            return create_response(
                "success",
                data={"answer": "Aún no hay documentos indexados.", "sources": []},
                status_code=200,
            )
        retrieved = (
            chroma.search_with_scores(question, k=k)
            if use_scores
            else chroma.search(question, k=k)
        )
        if not retrieved:
            return create_response(
                "success",
                data={"answer": "No encontré información en los documentos.", "sources": []},
                status_code=200,
            )

        rag = RAGService(
            model_name=current_app.config["OLLAMA_MODEL"],
            base_url=current_app.config["OLLAMA_HOST"],
            max_chars=current_app.config["RAG_MAX_CHARS"],
            score_threshold=current_app.config["RAG_SCORE_THRESHOLD"],
        )
        result = rag.generate_answer(
            question, retrieved, use_scores=use_scores, score_threshold=score_threshold
        )
        return create_response("success", data=result, status_code=200)
    except Exception:
        logger_app.exception("Error en la consulta RAG")
        return create_response(
            "error",
            message="El servicio de consulta no está disponible.",
            status_code=503,
        )
