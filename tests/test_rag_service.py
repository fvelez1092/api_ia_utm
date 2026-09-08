import unittest

from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from app.services.rag_service import RAGService


class RAGServiceTestCase(unittest.TestCase):
    @staticmethod
    def _service(answer="Debe aprobar el trabajo de titulación [1]."):
        model = RunnableLambda(lambda _: AIMessage(content=answer))
        return RAGService(
            chat_model=model,
            max_chars=4000,
            score_threshold=0.8,
        )

    def test_generates_answer_with_chat_messages_and_reports_distance(self):
        service = self._service()
        document = Document(
            page_content="Para obtener el título debe aprobar el trabajo de titulación.",
            metadata={"filename": "reglamento.pdf", "page": 12},
        )

        result = service.generate_answer("¿Cómo me gradúo?", [(document, 0.42)])

        self.assertEqual(result["answer"], "Debe aprobar el trabajo de titulación [1].")
        self.assertEqual(result["sources"][0]["distance"], 0.42)

    def test_returns_unknown_when_all_documents_exceed_threshold(self):
        service = self._service()
        document = Document(page_content="Contenido", metadata={})

        result = service.generate_answer("Pregunta", [(document, 1.5)])

        self.assertEqual(result, {"answer": "No lo sé.", "sources": []})


if __name__ == "__main__":
    unittest.main()
