# Despliegue en OCI con Terraform — Guía Completa

Esta guía explica qué archivos componen la infraestructura como código (IaC) del proyecto, qué hace cada uno, y los pasos exactos para desplegar el agente de Santos Pegasus en OCI usando Terraform.

## ¿Por qué Terraform en vez de crear todo a mano?

Cuando creas recursos manualmente en la consola de OCI (instancia, red, reglas de firewall), ese proceso no queda documentado ni es repetible: si la instancia se borra, hay que rehacer todo a mano y es fácil olvidar un paso (como abrir un puerto).

Con Terraform, describes la infraestructura en archivos de texto (`.tf`). Esos archivos son la fuente de verdad: puedes destruir todo y recrearlo idéntico con dos comandos, y además el código queda versionado en tu repositorio de GitHub como evidencia de tu arquitectura.

## Estructura de archivos

```
terraform/
├── main.tf                      # Infraestructura: red + instancia
├── variables.tf                 # Parámetros configurables
├── outputs.tf                   # Datos que se muestran al terminar
├── cloud-init.yaml.tpl          # Script de instalación automática
└── terraform.tfvars.example     # Plantilla de valores (la copias y completas)
```

---

## 1. `variables.tf` — los parámetros del proyecto

Define qué datos necesita Terraform para trabajar, sin tenerlos escritos directamente en el código (así el mismo código sirve para cualquier persona, cambiando solo sus valores).

| Variable | Qué es | Dónde lo consigues |
|---|---|---|
| `tenancy_ocid` | Identificador único de tu cuenta OCI | Consola OCI → tu perfil → Tenancy |
| `compartment_ocid` | Dónde se crean los recursos (usamos el root, mismo valor que `tenancy_ocid`) | Igual que arriba |
| `region` | Región donde se despliega (ej. `sa-saopaulo-1`) | La que elegiste en `oci setup config` |
| `ssh_public_key_path` | Ruta a tu llave pública SSH | La que generaste con `ssh-keygen` |
| `instance_shape` | El "tamaño" de la instancia (CPU/RAM) | `VM.Standard.E2.1.Micro` = nivel gratuito (Always Free) |
| `google_api_key` | Tu API key de Gemini | https://aistudio.google.com/app/apikey |
| `github_repo_url` | URL de tu repo con el código del agente | Tu repositorio en GitHub |
| `app_port` | Puerto donde corre Streamlit | `8501` por defecto |

Estos valores **no** van escritos directamente aquí — se completan en `terraform.tfvars` (ver sección 5).

---

## 2. `main.tf` — la infraestructura

Este archivo describe, en orden, todo lo que se va a crear en OCI:

### a) Red (VCN, subred, gateway, rutas)
Una instancia en OCI no puede existir sin una red virtual (VCN) que la contenga. Se crean:
- **VCN**: la red virtual privada, como el "terreno" donde vive todo.
- **Internet Gateway**: la puerta que permite tráfico desde/hacia internet.
- **Route Table**: le dice a la red "todo el tráfico que no sea interno, sale por el Internet Gateway".
- **Subnet**: una subdivisión de la VCN donde se conecta la instancia.

### b) Security List (firewall a nivel de red)
Define qué puertos pueden recibir tráfico desde afuera:
- **Puerto 22** (SSH) — para que puedas conectarte a administrar la instancia.
- **Puerto 8501** (Streamlit) — para que cualquier persona pueda acceder a tu agente desde el navegador.

Esto reemplaza el paso manual de "Security List" que se haría desde la consola web.

### c) Selección automática de imagen
En vez de escribir a mano el OCID de una imagen de Ubuntu (que cambia con cada actualización), un bloque `data "oci_core_images"` busca automáticamente la versión más reciente de **Ubuntu 22.04** compatible con la forma de instancia elegida.

### d) La instancia de cómputo
Crea la máquina virtual en sí, y le pasa dos cosas clave en su `metadata`:
- `ssh_authorized_keys`: tu llave pública SSH, para poder conectarte después.
- `user_data`: el script de `cloud-init` (ver sección 3) que se ejecuta automáticamente la primera vez que la instancia arranca.

---

## 3. `cloud-init.yaml.tpl` — instalación 100% automática

Este es el corazón de la "Opción B" (infraestructura + instalación automática). Es un script que la instancia ejecuta sola, sin que tengas que conectarte por SSH a hacer nada a mano. En orden, hace:

1. **Instala paquetes del sistema**: Python, pip, git, y `iptables-persistent` (para guardar reglas de firewall).
2. **Escribe el archivo de servicio `systemd`** (`santos-pegasus.service`), que define cómo debe correr la app y que se reinicie sola si falla.
3. **Abre el puerto 8501** en el firewall interno de Ubuntu (el segundo firewall que mencionamos antes, distinto al de la Security List de OCI — hay que abrir ambos).
4. **Clona tu repositorio de GitHub** dentro de la instancia.
5. **Crea el entorno virtual e instala las dependencias** (`requirements.txt`).
6. **Escribe el archivo `.env`** con tu API key de Google — inyectada de forma segura por Terraform, nunca queda expuesta en el código del repositorio.
7. **Construye la base vectorial** (ejecuta `build_vectorstore.py`) usando los PDFs que están en el repo.
8. **Activa y arranca el servicio** con `systemctl`, para que la app quede corriendo de forma permanente.

**Nota importante:** para que el paso 4 funcione, tu código y tus PDFs ya deben estar subidos a GitHub *antes* de correr Terraform.

---

## 4. `outputs.tf` — qué te muestra al terminar

Cuando el despliegue termina, Terraform imprime automáticamente:
- La **IP pública** de la instancia.
- La **URL completa** para abrir la app en el navegador.
- El **comando SSH** listo para copiar y pegar si necesitas conectarte a revisar algo.

Esto te ahorra tener que buscar la IP manualmente en la consola de OCI.

---

## 5. `terraform.tfvars` — tus valores reales

`terraform.tfvars.example` es solo una plantilla. Antes de desplegar, debes:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Y editar `terraform.tfvars` con tus valores reales:

```hcl
tenancy_ocid     = "ocid1.tenancy.oc1..tu_ocid_real"
compartment_ocid = "ocid1.tenancy.oc1..tu_ocid_real"  # igual al de arriba (root compartment)
region           = "sa-saopaulo-1"

ssh_public_key_path = "~/.ssh/oci_instance_key.pub"

google_api_key   = "tu_api_key_real_de_gemini"
github_repo_url  = "https://github.com/tu-usuario/tu-repo.git"

app_port = 8501
```

⚠️ **Este archivo nunca se sube a GitHub** — ya está incluido en `.gitignore` porque contiene tu API key en texto plano.

---

## 6. Pasos para desplegar

### Requisito previo
Tu código (incluyendo los PDFs en `data/pdfs/`) debe estar ya subido a GitHub, porque `cloud-init` hace `git clone` de ese repositorio.

### Comandos

```bash
cd terraform

# 1. Descarga el provider de OCI y prepara el directorio
terraform init

# 2. Muestra un preview de qué se va a crear (revisa que no haya errores)
terraform plan

# 3. Crea todo de verdad en OCI
terraform apply
```

Terraform te mostrará un resumen y preguntará `Enter a value:` — escribe **`yes`** para confirmar.

El proceso de creación de la instancia toma 1-2 minutos, pero **el `cloud-init` sigue instalando cosas en segundo plano después de eso** (clonar repo, instalar dependencias, construir embeddings). Espera 2-3 minutos adicionales antes de probar la URL.

### Verificar que funcionó

Cuando `apply` termine, verás algo como:

```
Outputs:

app_url = "http://140.238.x.x:8501"
instance_public_ip = "140.238.x.x"
ssh_command = "ssh -i ~/.ssh/oci_instance_key ubuntu@140.238.x.x"
```

Abre `app_url` en tu navegador. Si aún no carga, espera un minuto más (cloud-init puede seguir corriendo) o conéctate por SSH para revisar el progreso:

```bash
ssh -i ~/.ssh/oci_instance_key ubuntu@<IP>
sudo tail -f /var/log/cloud-init-output.log
```

Ese log te muestra en tiempo real qué está haciendo `cloud-init` — útil si algo tarda más de lo esperado o falla.

### Verificar el estado del servicio de la app

Ya conectado por SSH:

```bash
sudo systemctl status santos-pegasus
```

Si dice `active (running)`, todo está en orden.

---

## 7. Destruir la infraestructura (cuando ya no la necesites)

Para no dejar recursos corriendo sin uso (aunque sea nivel gratuito, es buena práctica):

```bash
terraform destroy
```

Esto elimina la instancia y toda la red asociada. Puedes volver a crear todo idéntico en cualquier momento con `terraform apply`.

---

## 8. Solución de problemas comunes

| Problema | Causa probable | Solución |
|---|---|---|
| `terraform plan` da error de autenticación | El provider no encuentra tu config de OCI | Verifica que `~/.oci/config` existe y el fingerprint coincide con la llave subida en la consola |
| La app no carga después de varios minutos | `cloud-init` sigue corriendo o falló en algún paso | Conéctate por SSH y revisa `/var/log/cloud-init-output.log` |
| Error "repository not found" en el log de cloud-init | El repo de GitHub es privado o la URL está mal escrita | Verifica que el repo sea público, o usa una URL con token si es privado |
| El servicio systemd no arranca | Falta el `.env`, o los PDFs no estaban en el repo al clonar | Revisa `sudo journalctl -u santos-pegasus -f` para ver el error exacto |
| `terraform apply` fallla creando la instancia | Ya usaste tu cupo Always Free en esa forma/región | Prueba con otra `instance_shape` (ej. Ampere A1) o revisa cuotas en la consola OCI |

---

## Resumen para tu README del challenge

Para el entregable, puedes mencionar en tu README que el deploy se realizó mediante **Infraestructura como Código (Terraform)**, incluyendo:
- Aprovisionamiento automático de red, seguridad y cómputo en OCI.
- Instalación y configuración automática de la aplicación vía `cloud-init`.
- Reproducibilidad completa: cualquier persona con las credenciales correctas puede recrear el despliegue exacto con `terraform apply`.

Esto suele valorarse muy bien en un desafío técnico, porque demuestra buenas prácticas de DevOps más allá del deploy manual básico.
