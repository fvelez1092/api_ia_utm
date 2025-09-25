from app.utils.response import create_response
from flask import Blueprint, request
from app.services.embedding_service import EmbeddingService
from app.services.chroma_service import ChromaService
from app.services.rag_service import RAGService
from app.extensions import logger_app

rag_blueprint = Blueprint("RAG", __name__, url_prefix="/rag")
"""Entidad - RAG (consultas sobre documentos)"""

# Inicializar servicios
embedding_service = EmbeddingService()
chroma_service = ChromaService()
rag_service = RAGService()


@rag_blueprint.route("/ask", methods=["POST"])
def ask_question():
    """
    Endpoint para realizar preguntas basadas en los documentos indexados.
    Recibe JSON:
    {
        "question": "¿Cuál es la política de vacaciones?"
    }
    """
    try:
        data = request.get_json()
        if not data or "question" not in data:
            return create_response(
                "error",
                data={"message": "El campo 'question' es requerido"},
                status_code=400,
            )

        question = data["question"]
        k = data.get("n_context", 5)

        # Recuperar documentos similares desde Chroma
        docs = chroma_service.search(question, k=k)

        if not docs:
            return create_response(
                "success",
                data={"answer": "No encontré información en los documentos."},
                status_code=200,
            )

        # Generar respuesta con el modelo LLM
        answer = rag_service.generate_answer(question, docs)

        return create_response(
            "success",
            data={"answer": answer},
            status_code=200,
        )

    except Exception as e:
        logger_app.error(f"Error en RAG/ask: {str(e)}")
        return create_response(
            "error",
            data={"message": str(e)},
            status_code=500,
            message=str(e),
        )
