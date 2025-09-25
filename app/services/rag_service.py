from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from app.config import config

PROMPT_TEMPLATE = """
Eres un asistente especializado en procesar y responder preguntas en español 

1. Analizar contexto proporcionado en español
2. Entender la pregunta en español
3. Generar una respuesta clara y concisa en español
4. Indica también en qué documento encontraste la información.

Si no encuentras la respuesta en el contexo simplemente indica que no lo sabes.

Limita tu respuesta a tres oraciones máximo

Pregunta: {question}
Contexto: {context}
Respuesta (en español):
"""


class RAGService:
    def __init__(self):
        self.model = OllamaLLM(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_HOST)
        self.prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    def generate_answer(self, question, documents):
        context = "\n\n".join([doc.page_content for doc in documents])
        chain = self.prompt | self.model
        return chain.invoke({"question": question, "context": context})
