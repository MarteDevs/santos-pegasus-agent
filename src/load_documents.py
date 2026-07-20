"""
load_documents.py
------------------
Carga todos los PDFs de data/pdfs/, extrae su texto y los divide
en fragmentos (chunks) pequeños para poder buscarlos después.

Por qué dividimos en chunks:
Un LLM no puede "leer" un PDF entero de forma eficiente en cada pregunta.
En su lugar, partimos el documento en trozos manejables (~1000 caracteres)
para luego encontrar solo los trozos relevantes a cada pregunta.
"""

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

PDF_FOLDER = os.path.join("data", "pdfs")


def cargar_pdfs(carpeta: str = PDF_FOLDER):
    """Lee todos los PDFs de la carpeta y devuelve una lista de documentos
    con su texto y metadata (nombre del archivo, número de página)."""
    documentos = []

    archivos_pdf = [f for f in os.listdir(carpeta) if f.lower().endswith(".pdf")]

    if not archivos_pdf:
        raise FileNotFoundError(
            f"No se encontraron PDFs en '{carpeta}'. "
            "Verifica que copiaste los archivos ahí."
        )

    print(f"Encontrados {len(archivos_pdf)} PDFs:")
    for nombre_archivo in archivos_pdf:
        ruta = os.path.join(carpeta, nombre_archivo)
        print(f"  - Cargando: {nombre_archivo}")

        loader = PyPDFLoader(ruta)
        paginas = loader.load()

        # Añadimos el nombre del archivo como metadata, para saber luego
        # de qué documento vino cada respuesta
        for pagina in paginas:
            pagina.metadata["fuente"] = nombre_archivo

        documentos.extend(paginas)

    print(f"\nTotal de páginas cargadas: {len(documentos)}")
    return documentos


def dividir_en_fragmentos(documentos, tamano_fragmento: int = 1000, superposicion: int = 200):
    """Divide los documentos en fragmentos (chunks) más pequeños.

    tamano_fragmento: cuántos caracteres tiene cada fragmento aproximadamente.
    superposicion: cuántos caracteres se repiten entre fragmentos consecutivos,
                   para no cortar una idea a la mitad.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=tamano_fragmento,
        chunk_overlap=superposicion,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    fragmentos = splitter.split_documents(documentos)
    print(f"Documentos divididos en {len(fragmentos)} fragmentos.")
    return fragmentos


if __name__ == "__main__":
    # Esto permite probar este archivo de forma independiente:
    # python src/load_documents.py
    documentos = cargar_pdfs()
    fragmentos = dividir_en_fragmentos(documentos)

    print("\n--- Ejemplo del primer fragmento ---")
    print(f"Fuente: {fragmentos[0].metadata.get('fuente')}")
    print(f"Contenido:\n{fragmentos[0].page_content[:300]}...")