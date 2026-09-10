import math
from functools import wraps

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt, verify_jwt_in_request

from app.extensions import limiter, logger_app
from app.services.rag_service import RAGService
from app.services.service_registry import get_chroma_service
from app.utils.response import create_response


rag_blueprint = Blueprint("RAG", __name__, url_prefix="/rag")


def _rag_auth_required(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        if current_app.config["RAG_AUTH_ENABLED"]:
            verify_jwt_in_request()
        return function(*args, **kwargs)

    return decorated


def _safe_int(value, default, min_v=1, max_v=20):
    try:
        return max(min(int(value), max_v), min_v)
    except (TypeError, ValueError):
        return default


def _parse_bool(value, field="use_scores"):
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    raise ValueError(f"'{field}' debe ser true o false.")


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
    return get_chroma_service()


def _rag_service():
    if "rag_service" not in current_app.extensions:
        current_app.extensions["rag_service"] = RAGService(
            model_name=current_app.config["OLLAMA_MODEL"],
            base_url=current_app.config["OLLAMA_HOST"],
            max_chars=current_app.config["RAG_MAX_CHARS"],
            score_threshold=current_app.config["RAG_SCORE_THRESHOLD"],
            reasoning=current_app.config["OLLAMA_REASONING"],
            num_ctx=current_app.config["OLLAMA_NUM_CTX"],
            num_predict=current_app.config["OLLAMA_NUM_PREDICT"],
            keep_alive=current_app.config["OLLAMA_KEEP_ALIVE"],
            temperature=current_app.config["OLLAMA_TEMPERATURE"],
            top_k=current_app.config["OLLAMA_TOP_K"],
            top_p=current_app.config["OLLAMA_TOP_P"],
        )
    return current_app.extensions["rag_service"]


@rag_blueprint.post("/ask")
@limiter.limit("30 per minute")
@_rag_auth_required
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
        use_scores = _parse_bool(data.get("use_scores", False))
        include_context = _parse_bool(
            data.get("include_context", False), "include_context"
        )
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

    if include_context and (
        not current_app.config["RAG_AUTH_ENABLED"]
        or get_jwt().get("role") != "admin"
    ):
        return create_response(
            "error",
            message="El contexto de diagnóstico requiere autenticación de administrador.",
            status_code=403,
        )

    default_contexts = current_app.config["RAG_DEFAULT_CONTEXTS"]
    k = _safe_int(
        data.get("n_context", default_contexts),
        default=default_contexts,
        min_v=1,
        max_v=current_app.config["RAG_MAX_CONTEXTS"],
    )
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

        rag = _rag_service()
        result = rag.generate_answer(
            question,
            retrieved,
            use_scores=use_scores,
            score_threshold=score_threshold,
            include_excerpts=include_context,
        )
        return create_response("success", data=result, status_code=200)
    except Exception:
        logger_app.exception("Error en la consulta RAG")
        return create_response(
            "error",
            message="El servicio de consulta no está disponible.",
            status_code=503,
        )