"""
app.py
------
Interfaz web simple para el agente de Santos Pegasus, construida con Streamlit.

Para correrla localmente:
    streamlit run src/app.py

Streamlit vuelve a ejecutar este archivo completo en cada interacción,
por eso usamos @st.cache_resource: así el agente (y la conexión a la
base vectorial) se carga UNA sola vez y se reutiliza entre preguntas,
en vez de recrearse cada vez que el usuario escribe algo.
"""

import streamlit as st
from agente import crear_agente, preguntar

st.set_page_config(
    page_title="Agente Santos Pegasus",
    page_icon="🤖",
    layout="centered",
)


@st.cache_resource(show_spinner=False)
def obtener_agente():
    """Carga el agente una sola vez y lo reutiliza en toda la sesión."""
    return crear_agente()


st.title("🤖 Agente Santos Pegasus Soluciones")
st.caption(
    "Pregunta sobre la documentación interna de la empresa: onboarding, "
    "arquitectura, ingeniería back-end/front-end e incidentes."
)

# Inicializamos el historial de conversación en el estado de la sesión
if "historial" not in st.session_state:
    st.session_state.historial = []

# Cargamos el agente (con spinner mientras se prepara la primera vez)
with st.spinner("Cargando agente..."):
    agente = obtener_agente()

# Mostramos el historial de conversación previo
for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])

# Caja de entrada de texto para la nueva pregunta
pregunta = st.chat_input("Escribe tu pregunta sobre Santos Pegasus...")

if pregunta:
    # Mostramos la pregunta del usuario en el chat
    st.session_state.historial.append({"rol": "user", "contenido": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    # Generamos y mostramos la respuesta del agente
    with st.chat_message("assistant"):
        with st.spinner("Buscando en la documentación..."):
            respuesta, fuentes = preguntar(agente, pregunta)

        st.markdown(respuesta)
        if fuentes:
            st.caption(f"📄 Fuente(s): {', '.join(fuentes)}")

    contenido_completo = respuesta
    if fuentes:
        contenido_completo += f"\n\n📄 Fuente(s): {', '.join(fuentes)}"

    st.session_state.historial.append(
        {"rol": "assistant", "contenido": contenido_completo}
    )