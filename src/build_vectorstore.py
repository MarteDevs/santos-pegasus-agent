"""
build_vectorstore.py
---------------------
Convierte los fragmentos de texto en embeddings (vectores numéricos)
usando el modelo de embeddings de Google, y los guarda en una base
vectorial FAISS local para poder buscarlos rápidamente después.

Esto solo se ejecuta UNA VEZ (o cada vez que cambien los documentos).
El agente, en su día a día, solo lee esta base ya construida.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

from load_documents import cargar_pdfs, dividir_en_fragmentos

load_dotenv()  # lee las variables de entorno desde .env

VECTORSTORE_PATH = os.path.join("vectorstore", "faiss_index")


def construir_vectorstore():
    if not os.getenv("GOOGLE_API_KEY"):
        raise EnvironmentError(
            "No se encontró GOOGLE_API_KEY. Verifica tu archivo .env."
        )

    # 1. Cargar y dividir documentos
    documentos = cargar_pdfs()
    fragmentos = dividir_en_fragmentos(documentos)

    # 2. Crear el modelo de embeddings de Google
    print("\nGenerando embeddings (esto puede tardar un poco)...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # 3. Construir la base vectorial FAISS a partir de los fragmentos
    vectorstore = FAISS.from_documents(fragmentos, embeddings)

    # 4. Guardar la base vectorial en disco para no tener que
    #    regenerarla cada vez que usemos el agente
    os.makedirs("vectorstore", exist_ok=True)
    vectorstore.save_local(VECTORSTORE_PATH)

    print(f"\n✅ Base vectorial guardada en: {VECTORSTORE_PATH}")
    return vectorstore


def cargar_vectorstore():
    """Carga una base vectorial ya construida (sin regenerar embeddings)."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = FAISS.load_local(
        VECTORSTORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True,  # seguro aquí: el archivo lo generamos nosotros
    )
    return vectorstore


if __name__ == "__main__":
    # python src/build_vectorstore.py
    vectorstore = construir_vectorstore()

    # Prueba rápida: buscar fragmentos relevantes a una pregunta de ejemplo
    print("\n--- Prueba de búsqueda ---")
    pregunta_prueba = "¿Qué tecnologías se usan en el back-end?"
    resultados = vectorstore.similarity_search(pregunta_prueba, k=3)

    for i, doc in enumerate(resultados, 1):
        print(f"\nResultado {i} (fuente: {doc.metadata.get('fuente')}):")
        print(doc.page_content[:200], "...")