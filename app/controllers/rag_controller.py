# from app.utils.response import create_response
# from flask import Blueprint, request
# from app.services.embedding_service import EmbeddingService
# from app.services.chroma_service import ChromaService
# from app.services.rag_service import RAGService
# from app.extensions import logger_app

# rag_blueprint = Blueprint("RAG", __name__, url_prefix="/rag")
# """Entidad - RAG (consultas sobre documentos)"""

# # Inicializar servicios
# embedding_service = EmbeddingService()
# chroma_service = ChromaService()
# rag_service = RAGService()


# @rag_blueprint.route("/ask", methods=["POST"])
# def ask_question():
#     """
#     Endpoint para realizar preguntas basadas en los documentos indexados.
#     Recibe JSON:
#     {
#         "question": "¿Cuál es la política de vacaciones?"
#     }
#     """
#     try:
#         data = request.get_json()
#         if not data or "question" not in data:
#             return create_response(
#                 "error",
#                 data={"message": "El campo 'question' es requerido"},
#                 status_code=400,
#             )

#         question = data["question"]
#         k = data.get("n_context", 5)

#         # Recuperar documentos similares desde Chroma
#         docs = chroma_service.search(question, k=k)

#         if not docs:
#             return create_response(
#                 "success",
#                 data={"answer": "No encontré información en los documentos."},
#                 status_code=200,
#             )

#         # Generar respuesta con el modelo LLM
#         answer = rag_service.generate_answer(question, docs)

#         return create_response(
#             "success",
#             data={"answer": answer},
#             status_code=200,
#         )

#     except Exception as e:
#         logger_app.error(f"Error en RAG/ask: {str(e)}")
#         return create_response(
#             "error",
#             data={"message": str(e)},
#             status_code=500,
#             message=str(e),
#         )
from flask import Blueprint, request
from app.utils.response import create_response
from app.services.embedding_service import EmbeddingService
from app.services.chroma_service import ChromaService

# from app.services.rag_service import RAGService
from app.extensions import logger_app

# Inicializar servicios (solo una vez)
embedding_service = EmbeddingService()
chroma_service = ChromaService()
# rag_service = RAGService()

# Crear blueprint
rag_blueprint = Blueprint("RAG", __name__, url_prefix="/rag")


def _safe_int(value, default, min_v=1, max_v=20):
    try:
        v = int(value)
        return max(min(v, max_v), min_v)
    except Exception:
        return default


@rag_blueprint.route("/ask", methods=["POST"])
def ask_question():
    from app.services.rag_service import RAGService  # Importación perezosa

    rag_service = RAGService()
    """
    Endpoint para realizar preguntas basadas en los documentos indexados.
    Recibe un JSON con los siguientes parámetros:
    {
        "question": "¿Cuál es la política de vacaciones?",
        "n_context": 5,                 # opcional, default 5
        "score_threshold": 0.8,         # opcional, default config.RAG_SCORE_THRESHOLD
        "use_scores": true              # opcional, default true
    }
    """
    try:
        # Validar que la petición sea JSON
        if not request.is_json:
            return create_response(
                "error",
                data={"message": "Se requiere JSON (Content-Type: application/json)"},
                status_code=400,
            )

        # Obtener datos de la solicitud
        data = request.get_json(silent=True) or {}
        question = (data.get("question") or "").strip()
        if not question:
            return create_response(
                "error",
                data={"message": "El campo 'question' es requerido"},
                status_code=400,
            )

        # Configurar parámetros de contexto y puntuación
        k = _safe_int(data.get("n_context", 5), default=5, min_v=1, max_v=15)
        use_scores = bool(data.get("use_scores", True))
        score_threshold = data.get("score_threshold", None)

        # Verificar la cantidad de documentos indexados
        try:
            total_docs = chroma_service.count()
            logger_app.info(f"[RAG] Documentos indexados en Chroma: {total_docs}")
            if total_docs is not None and total_docs == 0:
                return create_response(
                    "success",
                    data={"answer": "Aún no hay documentos indexados.", "sources": []},
                    status_code=200,
                )
        except Exception as e_count:
            logger_app.warning(f"[RAG] No se pudo obtener count(): {e_count}")

        # Recuperación de documentos y puntuaciones
        try:
            if use_scores:
                pairs = chroma_service.search_with_scores(question, k=k)
                retrieval_items = pairs  # [(Document, score)]
            else:
                docs = chroma_service.search(question, k=k)
                retrieval_items = docs
        except Exception as e_search:
            logger_app.error(f"[RAG] Error en búsqueda Chroma: {e_search}")
            return create_response(
                "error",
                data={"message": f"Error en la búsqueda de contexto: {e_search}"},
                status_code=500,
            )

        # Verificar si se encontraron documentos
        if not retrieval_items:
            return create_response(
                "success",
                data={
                    "answer": "No encontré información en los documentos.",
                    "sources": [],
                },
                status_code=200,
            )

        # Generar respuesta utilizando el modelo RAG
        result = rag_service.generate_answer(
            question=question,
            documents_or_pairs=retrieval_items,
            use_scores=use_scores,
            score_threshold=score_threshold,
        )

        return create_response("success", data=result, status_code=200)

    except Exception as e:
        logger_app.error(f"Error en RAG/ask: {str(e)}", exc_info=True)
        return create_response(
            "error", data={"message": str(e)}, status_code=500, message=str(e)
        )
