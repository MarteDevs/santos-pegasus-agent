# Santos Pegasus AI Agent 🚀

Este proyecto implementa un **Asistente Virtual con Inteligencia Artificial (RAG)** diseñado para la empresa *Santos Pegasus Soluciones*. El agente es capaz de leer la documentación interna de la empresa (en formato PDF) y responder preguntas basándose estrictamente en esos documentos, evitando que el modelo de lenguaje "invente" información.

![Servidor Desplegado en OCI](./screenshot.png) *(Nota: Reemplaza `screenshot.png` con la imagen de tu servidor)*

## Arquitectura y Tecnologías 🏗️

* **Front-end:** [Streamlit](https://streamlit.io/) (Framework de Python para interfaces web interactivas).
* **Back-end y Orquestación:** Python, `langchain` y `langchain-google-genai`.
* **Modelo de Lenguaje (LLM):** Google Gemini 3.5 Flash.
* **Modelo de Embeddings:** Google `models/gemini-embedding-2`.
* **Base Vectorial (Vectorstore):** [FAISS](https://faiss.ai/) (Facebook AI Similarity Search) en memoria local.
* **Infraestructura Cloud:** Oracle Cloud Infrastructure (OCI).
* **Infraestructura como Código (IaC):** Terraform.

## Estructura del Proyecto 📂

```text
santos-pegasus-agent/
│
├── data/
│   └── pdfs/                   # Aquí se guardan los PDFs de la empresa
│
├── src/
│   ├── app.py                  # Interfaz gráfica de Streamlit
│   ├── agente.py               # Lógica del LLM y cadena RAG
│   ├── build_vectorstore.py    # Script para generar los embeddings (por lotes)
│   └── load_documents.py       # Extrae y divide el texto de los PDFs
│
├── terraform/
│   ├── main.tf                 # Define la Instancia y VCN en OCI
│   ├── variables.tf            # Variables de configuración
│   ├── outputs.tf              # Imprime la IP pública final
│   ├── cloud-init.yaml.tpl     # Script de inicialización del servidor
│   └── terraform.tfvars        # Tus credenciales privadas de OCI (Ignorado en git)
│
├── vectorstore/                # Contiene la base de datos compilada de FAISS
├── .env                        # Variables de entorno (GOOGLE_API_KEY)
└── requirements.txt            # Dependencias de Python
```

## Características Principales ✨

1. **RAG (Retrieval-Augmented Generation):** El agente extrae respuestas precisas de los manuales y arquitectura de microservicios de la empresa.
2. **Procesamiento de Embeddings por Lotes:** El script `build_vectorstore.py` procesa los documentos en lotes de 50 fragmentos y espera 65 segundos entre lotes para no saturar los límites gratuitos de la API de Google.
3. **Despliegue 100% Automatizado:** Gracias a Terraform y `cloud-init`, la creación de la red, firewall, máquina virtual y configuración del servicio de `systemd` se realiza de manera desatendida.

## Guía de Despliegue en OCI ☁️

### 1. Requisitos Previos
* Una cuenta en Oracle Cloud Infrastructure (OCI).
* Tener instalado **Terraform** y la **OCI CLI** configurada localmente.
* Una llave API de Google (Google AI Studio).
* Tener clonado este repositorio y asegurarte de **subir todos tus cambios a GitHub (git push)** antes de desplegar, ya que la instancia descarga el código de ahí.

### 2. Configuración de Terraform
Dentro de la carpeta `terraform/`, crea el archivo `terraform.tfvars` guiándote con el archivo `terraform.tfvars.example` e inserta tus credenciales de OCI, tu llave pública SSH y tu API Key de Google.

### 3. Ejecutar el Despliegue
Ejecuta los siguientes comandos en la terminal desde la carpeta `terraform/`:

```bash
terraform init
terraform plan
terraform apply --auto-approve
```

Terraform te devolverá la IP pública de tu nueva máquina virtual.

### 4. Acceder al Agente
Debido a la generación de la base vectorial (la cual incluye pausas de 65 segundos por lote), el servidor web tomará unos **20 a 30 minutos** en arrancar por primera vez.

Una vez finalizado, puedes acceder a la interfaz entrando a:
`http://<IP-PUBLICA>:8501`

### Solución de Problemas (Troubleshooting) 🛠️

Si la página no carga, puedes entrar por SSH a la máquina para revisar los logs:
```bash
ssh -i /ruta/a/tu/llave_privada ubuntu@<IP-PUBLICA>
```

Y verificar el estado de la instalación:
```bash
sudo tail -f /var/log/cloud-init-output.log
sudo systemctl status santos-pegasus.service
sudo journalctl -u santos-pegasus.service -n 50 --no-pager
```
