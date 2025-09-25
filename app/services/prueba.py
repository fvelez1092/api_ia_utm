import streamlit as st
import os
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

template = """
Eres un asistente especializado en procesar y responder preguntas en español 

1. Analizar contexto proporcionado en español
2. Entender la pregunta en español
3. Generar una respuesta clara y concisa en español

Si no encuentras la respuesta en el contexo simplemente indica que no lo sabes.

Limita tu respuesta a tres oraciones máximo

Pregunta: {question}
Contexto: {context}
Respuesta (en español):
"""
pdfs_directory = "pdfs/"
db_directory = "db/"

# Asegurar que los directorios existen
os.makedirs(pdfs_directory, exist_ok=True)

embeddings = OllamaEmbeddings(
    model="deepseek-r1:14b", base_url="http://172.20.51.50:11434"
)
vector_store = Chroma(persist_directory=db_directory, embedding_function=embeddings)
model = OllamaLLM(model="deepseek-r1:14b", base_url="http://172.20.51.50:11434")


def upload_pdf(file):
    with open(os.path.join(pdfs_directory, file.name), "wb") as f:
        f.write(file.getbuffer())


def load_pdf(file_path):
    loader = PDFPlumberLoader(file_path)
    documents = loader.load()
    return documents


def split_text(documents):
    """Divide el texto en fragmentos manejables"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
        # separators=["\n\n", "\n", " ", ""],
    )
    texts = text_splitter.split_documents(documents)
    return texts


def index_docs(documents):
    vector_store.add_documents(documents)
    vector_store.persist()


def retrieve_docs(query):
    return vector_store.similarity_search(query)


def answer_question(question, documents):
    context = "\n\n".join([doc.page_content for doc in documents])
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    return chain.invoke({"question": question, "context": context})


upoload_file = st.file_uploader(
    "Sube un archivo PDF", type=["pdf"], accept_multiple_files=False
)

if upoload_file:
    upload_pdf(upoload_file)
    documents = load_pdf(os.path.join(pdfs_directory, upoload_file.name))
    chunked_documents = split_text(documents)
    index_docs(chunked_documents)

    question = st.chat_input("Escribe tu pregunta aquí:")

    if question:
        st.chat_message("user").write(question)
        related_documents = retrieve_docs(question)
        answer = answer_question(question, related_documents)
        st.chat_message("assistant").write(answer)
