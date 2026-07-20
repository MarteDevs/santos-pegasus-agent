"""
agente.py
---------
El corazón del proyecto: el agente RAG (Retrieval-Augmented Generation).

Flujo:
1. El usuario hace una pregunta.
2. Buscamos en la base vectorial los fragmentos de los PDFs más relevantes
   para esa pregunta (retrieval).
3. Le pasamos esos fragmentos + la pregunta al LLM (Gemini).
4. El LLM genera una respuesta en lenguaje natural, basada SOLO en esos
   fragmentos (generation).

Esto evita que el modelo "invente" información (alucine) y hace que
las respuestas estén ancladas en los documentos reales de la empresa.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

from build_vectorstore import cargar_vectorstore

load_dotenv()

# Plantilla de instrucciones para el LLM.
# Le decimos explícitamente que responda SOLO con la info del contexto,
# y que sea honesto si no la encuentra.
PLANTILLA_PROMPT = """Eres el asistente virtual de Santos Pegasus Soluciones,
una empresa de desarrollo de software y soluciones de IA.

Responde la pregunta del usuario basándote ÚNICAMENTE en el siguiente contexto,
extraído de la documentación interna de la empresa. Si la respuesta no se
encuentra en el contexto, di claramente que no tienes esa información en
los documentos disponibles, en vez de inventar una respuesta.

Contexto:
{context}

Pregunta: {question}

Respuesta clara y concisa:"""


def crear_agente():
    """Construye y devuelve el agente RAG listo para responder preguntas."""

    if not os.getenv("GOOGLE_API_KEY"):
        raise EnvironmentError(
            "No se encontró GOOGLE_API_KEY. Verifica tu archivo .env."
        )

    # 1. Cargar la base vectorial ya construida (Fase 3)
    vectorstore = cargar_vectorstore()

    # El "retriever" es el componente que busca los fragmentos relevantes.
    # k=4 significa: trae los 4 fragmentos más parecidos a la pregunta.
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # 2. Configurar el modelo de lenguaje (Gemini)
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",  # rápido y con buena capa gratuita
        temperature=0.2,  # baja temperatura = respuestas más precisas y menos creativas
    )

    # 3. Conectar el prompt personalizado
    prompt = PromptTemplate(
        template=PLANTILLA_PROMPT,
        input_variables=["context", "question"],
    )

    # 4. Crear la cadena RAG que une retriever + LLM + prompt
    cadena_qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # "stuff" = mete todos los fragmentos encontrados en un solo prompt
        retriever=retriever,
        return_source_documents=True,  # para poder mostrar de qué PDF vino la respuesta
        chain_type_kwargs={"prompt": prompt},
    )

    return cadena_qa


def preguntar(agente, pregunta: str):
    """Hace una pregunta al agente y devuelve la respuesta junto con las fuentes."""
    resultado = agente.invoke({"query": pregunta})

    respuesta = resultado["result"]
    fuentes = {doc.metadata.get("fuente") for doc in resultado["source_documents"]}

    return respuesta, fuentes


if __name__ == "__main__":
    # python src/agente.py
    print("Cargando agente de Santos Pegasus... (esto puede tardar unos segundos)\n")
    agente = crear_agente()

    print("✅ Agente listo. Escribe 'salir' para terminar.\n")

    while True:
        pregunta = input("Tu pregunta: ").strip()
        if pregunta.lower() in ("salir", "exit", "quit"):
            print("¡Hasta luego!")
            break
        if not pregunta:
            continue

        respuesta, fuentes = preguntar(agente, pregunta)

        print(f"\nRespuesta: {respuesta}")
        print(f"Fuente(s): {', '.join(fuentes)}\n")