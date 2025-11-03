# from typing import List, Dict, Any, Tuple, Union
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_ollama.llms import OllamaLLM
# from langchain_core.output_parsers import StrOutputParser
# from app.config import config
# from app.extensions import logger_app


# PROMPT_TEMPLATE = """
# Eres un asistente que responde EXCLUSIVAMENTE con base en el contexto dado.
# Reglas:
# 1) Analiza el contexto (en español).
# 2) Responde a la pregunta (en español) con claridad y concisión.
# 3) Cita las fuentes usando el índice entre corchetes (por ejemplo: [1], [2]).
# 4) Si no encuentras la respuesta en el contexto, responde literalmente: "No lo sé."
# 5) Máximo TRES oraciones.
# 6) Sé cordial ante saludos/despedidas, pero respeta (4).

# Pregunta: {question}

# Contexto (fragmentos numerados):
# {context}

# Responde en español (máx. 3 oraciones) citando fuentes como [n]:
# """


# class RAGService:
#     """
#     Genera respuestas RAG con citas. Puede recibir documentos o (documento, score) para filtrar por umbral.
#     """

#     def __init__(self):
#         self.model_name = getattr(config, "OLLAMA_MODEL", "llama3.1:8b-instruct")
#         self.base_url = getattr(config, "OLLAMA_HOST", "http://localhost:11434")
#         self.max_chars = int(getattr(config, "RAG_MAX_CHARS", 8000))
#         # Umbral de similitud (menor es más similar). Ajusta a tu data: 0.6–1.0 es un inicio razonable.
#         self.score_threshold = float(getattr(config, "RAG_SCORE_THRESHOLD", 0.8))

#         self.model = OllamaLLM(
#             model=self.model_name,
#             base_url=self.base_url,
#             temperature=0.0,
#             num_ctx=4096,
#             top_k=40,
#             top_p=0.9,
#         )
#         self.prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
#         self.parser = StrOutputParser()

#     # --------- helpers ---------
#     def _normalize_one(self, d: Any) -> Dict[str, Any]:
#         if hasattr(d, "page_content"):
#             content = d.page_content
#             meta = getattr(d, "metadata", {}) or {}
#         elif isinstance(d, dict):
#             content = d.get("page_content") or d.get("content") or d.get("text")
#             meta = d.get("metadata", {}) or {}
#         else:
#             return {}
#         if not content:
#             return {}

#         source = (
#             meta.get("source")
#             or meta.get("filename")
#             or meta.get("path")
#             or "desconocido"
#         )
#         page = (
#             meta.get("page")
#             or meta.get("page_number")
#             or meta.get("loc")
#             or meta.get("position")
#         )
#         return {"text": content.strip(), "source": source, "page": page, "meta": meta}

#     def _normalize_docs(self, items: List[Any]) -> List[Dict[str, Any]]:
#         norm = []
#         for d in items:
#             normed = self._normalize_one(d)
#             if normed:
#                 norm.append(normed)
#         return norm

#     def _format_context(
#         self, docs: List[Dict[str, Any]], max_chars: int
#     ) -> Tuple[str, List[Dict[str, Any]]]:
#         parts, sources, total = [], [], 0
#         for i, d in enumerate(docs, start=1):
#             header = f"[{i}] Fuente: {d['source']}" + (
#                 f" · Página: {d['page']}" if d["page"] else ""
#             )
#             block = f"{header}\n{d['text']}\n"
#             if total + len(block) > max_chars and i > 1:
#                 break
#             parts.append(block)
#             total += len(block)
#             sources.append({"idx": i, "source": d["source"], "page": d["page"]})
#         return "\n".join(parts), sources

#     # --------- pública ---------
#     def generate_answer(
#         self,
#         question: str,
#         documents_or_pairs: List[Union[Any, Tuple[Any, float]]],
#         use_scores: bool = True,
#         score_threshold: float = None,
#     ) -> Dict[str, Any]:
#         """
#         Retorna dict: {"answer": str, "sources": [{idx, source, page}]}
#         - Si `use_scores=True` y la entrada son pares (doc, score), filtrará por umbral.
#         """
#         try:
#             score_thr = (
#                 self.score_threshold
#                 if score_threshold is None
#                 else float(score_threshold)
#             )

#             # Acepta lista de docs o lista de (doc, score)
#             docs: List[Any] = []
#             scores: List[float] = []
#             for item in documents_or_pairs:
#                 if use_scores and isinstance(item, (list, tuple)) and len(item) == 2:
#                     d, s = item
#                     docs.append(d)
#                     scores.append(s)
#                 else:
#                     docs.append(item)

#             # Filtrar por score si procede (menor es más similar)
#             if use_scores and scores:
#                 filtered = [(d, s) for d, s in zip(docs, scores) if s <= score_thr]
#                 if not filtered:
#                     logger_app.info(
#                         f"[RAGService] Ningún documento pasa el umbral ({score_thr})."
#                     )
#                     return {"answer": "No lo sé.", "sources": []}
#                 docs = [d for d, _ in filtered]

#             norm_docs = self._normalize_docs(docs)
#             if not norm_docs:
#                 logger_app.info("[RAGService] Sin documentos útiles -> No lo sé.")
#                 return {"answer": "No lo sé.", "sources": []}

#             # Heurística simple: ordena por longitud (densidad)
#             norm_docs.sort(key=lambda x: len(x["text"]), reverse=True)

#             context, sources = self._format_context(norm_docs, max_chars=self.max_chars)
#             if not context.strip():
#                 return {"answer": "No lo sé.", "sources": []}

#             chain = self.prompt | self.model | self.parser
#             answer = chain.invoke(
#                 {"question": question.strip(), "context": context}
#             ).strip()

#             # Si no citó, fuerza [1] para mantener trazabilidad mínima
#             if "[" not in answer and "]" not in answer and sources:
#                 answer = f"{answer} [1]"

#             return {"answer": answer, "sources": sources}

#         except Exception as e:
#             logger_app.error(f"[RAGService] Error en generate_answer: {e}")
#             return {"answer": "No lo sé.", "sources": []}

from typing import List, Dict, Any, Tuple, Union
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_core.output_parsers import StrOutputParser
from app.config import config
from app.extensions import logger_app


PROMPT_TEMPLATE = """
Eres un asistente que responde basándote en el contexto proporcionado, salvo cuando el usuario te saluda o se despide.
Reglas:
1) Si el usuario saluda o se despide (por ejemplo: "hola", "buenos días", "gracias", "adiós"), responde de forma cordial en español, sin usar el contexto.
2) En los demás casos, responde únicamente con base en el contexto proporcionado.
3) Cita las fuentes usando el índice entre corchetes (por ejemplo: [1], [2]) solo cuando uses el contexto.
4) Si no encuentras la respuesta en el contexto, responde literalmente: "No lo sé."
5) Máximo TRES oraciones.

Pregunta: {question}

Contexto (fragmentos numerados):
{context}

Responde en español (máx. 3 oraciones) citando fuentes como [n]:
"""


class RAGService:
    """Genera respuestas RAG con citas. Puede recibir documentos o (documento, score) para filtrar por umbral."""

    def __init__(self):
        self.model_name = getattr(config, "OLLAMA_MODEL", "llama3.1:8b-instruct")
        self.base_url = getattr(config, "OLLAMA_HOST", "http://localhost:11434")
        self.max_chars = int(getattr(config, "RAG_MAX_CHARS", 8000))
        self.score_threshold = float(getattr(config, "RAG_SCORE_THRESHOLD", 0.8))

        # ✅ Modelo Ollama
        self.model = OllamaLLM(
            model=self.model_name,
            base_url=self.base_url,
            temperature=0.0,
            num_ctx=4096,
            top_k=40,
            top_p=0.9,
        )

        # ✅ ChatPromptTemplate correcto
        self.prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        self.parser = StrOutputParser()

    # ---------------- helpers ----------------
    def _normalize_one(self, d: Any) -> Dict[str, Any]:
        if hasattr(d, "page_content"):
            content = d.page_content
            meta = getattr(d, "metadata", {}) or {}
        elif isinstance(d, dict):
            content = d.get("page_content") or d.get("content") or d.get("text")
            meta = d.get("metadata", {}) or {}
        else:
            return {}
        if not content:
            return {}

        source = (
            meta.get("source")
            or meta.get("filename")
            or meta.get("path")
            or "desconocido"
        )
        page = (
            meta.get("page")
            or meta.get("page_number")
            or meta.get("loc")
            or meta.get("position")
        )
        return {"text": content.strip(), "source": source, "page": page, "meta": meta}

    def _normalize_docs(self, items: List[Any]) -> List[Dict[str, Any]]:
        norm = []
        for d in items:
            normed = self._normalize_one(d)
            if normed:
                norm.append(normed)
        return norm

    def _format_context(
        self, docs: List[Dict[str, Any]], max_chars: int
    ) -> Tuple[str, List[Dict[str, Any]]]:
        parts, sources, total = [], [], 0
        for i, d in enumerate(docs, start=1):
            header = f"[{i}] Fuente: {d['source']}" + (
                f" · Página: {d['page']}" if d["page"] else ""
            )
            block = f"{header}\n{d['text']}\n"
            if total + len(block) > max_chars and i > 1:
                break
            parts.append(block)
            total += len(block)
            sources.append({"idx": i, "source": d["source"], "page": d["page"]})
        return "\n".join(parts), sources

    # ---------------- pública ----------------
    def generate_answer(
        self,
        question: str,
        documents_or_pairs: List[Union[Any, Tuple[Any, float]]],
        use_scores: bool = True,
        score_threshold: float = None,
    ) -> Dict[str, Any]:
        """Retorna dict: {"answer": str, "sources": [{idx, source, page}]}"""
        try:
            score_thr = (
                self.score_threshold
                if score_threshold is None
                else float(score_threshold)
            )

            docs, scores = [], []
            for item in documents_or_pairs:
                if use_scores and isinstance(item, (list, tuple)) and len(item) == 2:
                    d, s = item
                    docs.append(d)
                    scores.append(s)
                else:
                    docs.append(item)

            if use_scores and scores:
                filtered = [(d, s) for d, s in zip(docs, scores) if s <= score_thr]
                if not filtered:
                    logger_app.info(
                        f"[RAGService] Ningún documento pasa el umbral ({score_thr})."
                    )
                    return {"answer": "No lo sé.", "sources": []}
                docs = [d for d, _ in filtered]

            norm_docs = self._normalize_docs(docs)
            if not norm_docs:
                logger_app.info("[RAGService] Sin documentos útiles -> No lo sé.")
                return {"answer": "No lo sé.", "sources": []}

            norm_docs.sort(key=lambda x: len(x["text"]), reverse=True)
            context, sources = self._format_context(norm_docs, max_chars=self.max_chars)
            if not context.strip():
                return {"answer": "No lo sé.", "sources": []}

            chain = self.prompt | self.model | self.parser
            answer = chain.invoke(
                {"question": question.strip(), "context": context}
            ).strip()

            if "[" not in answer and "]" not in answer and sources:
                answer = f"{answer} [1]"

            return {"answer": answer, "sources": sources}

        except Exception as e:
            logger_app.error(f"[RAGService] Error en generate_answer: {e}")
            return {"answer": "No lo sé.", "sources": []}
