# Email Notification Service

Servicio backend para gestión y envío de notificaciones por correo electrónico, construido con **FastAPI** y **PostgreSQL**. Expone una API REST completa para administrar cuentas de correo, plantillas reutilizables y el envío asincrónico o sincrónico de emails mediante SMTP o Microsoft Graph (Azure/O365).

## Stack

- **Python 3.12** · FastAPI · SQLAlchemy 2 · Pydantic v2
- **PostgreSQL** (schema configurable)
- **aiosmtplib** para envío SMTP asincrónico
- **Jinja2** para renderizado de plantillas

---

## Estructura del proyecto

```
notifications/
├── app/
│   ├── config.py          # Settings via pydantic-settings (.env)
│   ├── database.py        # Engine SQLAlchemy + sesiones
│   ├── dependencies.py    # Middleware autenticación X-API-Key
│   ├── models.py          # Modelos ORM
│   ├── schemas.py         # Esquemas Pydantic (request / response)
│   ├── routes/
│   │   ├── email_accounts.py
│   │   ├── email_templates.py
│   │   ├── send_email.py
│   │   └── email_history.py
│   └── services/
│       └── email_service.py   # Lógica de envío SMTP y Azure
├── tests/
├── main.py
├── requirements_optimized.txt
└── .env.example
```

---

## Instalación

### Requisitos previos

- Python 3.10+
- PostgreSQL (la base de datos debe existir antes de iniciar)

### Pasos

```bash
# 1. Crear entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# 2. Instalar dependencias
pip install -r requirements_optimized.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 4. Iniciar el servidor (las tablas se crean automáticamente al arrancar)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Configuración (.env)

```env
# Base de datos
DATABASE_TYPE=postgresql
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=email_notification_db
DATABASE_USER=postgres
DATABASE_PASSWORD=tu_password
DB_SCHEMA=public          # Schema de PostgreSQL

# Seguridad — requerido en todos los endpoints
API_KEY=tu_api_key_segura

# SMTP (para cuentas de tipo SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password
SMTP_FROM_EMAIL=tu-email@gmail.com
SMTP_FROM_NAME=Email Notification Service
```

> **Gmail:** Activa la autenticación en dos pasos y genera una [contraseña de aplicación](https://myaccount.google.com/apppasswords) para usar en `SMTP_PASSWORD`.

---

## Autenticación

Todos los endpoints (excepto `/` y `/health`) requieren el header:

```
X-API-Key: <tu_api_key>
```

Respuesta sin clave o clave inválida: `401 Unauthorized`.

---

## API Reference

La documentación interactiva está disponible en:

- **Swagger UI** → http://localhost:8000/docs
- **ReDoc** → http://localhost:8000/redoc

### Cuentas de correo — `/api/email-accounts`

| Método   | Endpoint              | Descripción                        |
|----------|-----------------------|------------------------------------|
| `POST`   | `/`                   | Crear cuenta (SMTP)                |
| `GET`    | `/`                   | Listar cuentas (paginado, filtros) |
| `GET`    | `/{id}`               | Obtener cuenta por ID              |
| `PUT`    | `/{id}`               | Actualizar cuenta                  |
| `DELETE` | `/{id}`               | Eliminar cuenta                    |
| `PATCH`  | `/{id}/status`        | Cambiar estado (ACTIVE / INACTIVE / SUSPENDED) |

**Query params** en `GET /`:
- `page` (default `1`)
- `per_page` (default `10`, max `100`)
- `provider_type` (`SMTP`)

### Plantillas de correo — `/api/email-templates`

| Método   | Endpoint                        | Descripción                             |
|----------|---------------------------------|-----------------------------------------|
| `POST`   | `/`                             | Crear plantilla                         |
| `GET`    | `/`                             | Listar plantillas (paginado)            |
| `GET`    | `/{id}`                         | Obtener plantilla por ID                |
| `PUT`    | `/{id}`                         | Actualizar plantilla                    |
| `DELETE` | `/{id}`                         | Eliminar plantilla                      |
| `GET`    | `/account/{id}/by-type`         | Obtener plantillas de cuenta por tipo   |

**Tipos de plantilla:** `REGISTRATION_CONFIRMATION` · `PASSWORD_RESET` · `GENERAL`

### Envío de correos — `/api/send`

| Método | Endpoint       | Descripción                                                    |
|--------|----------------|----------------------------------------------------------------|
| `POST` | `/email`       | Envío **asincrónico** — responde `QUEUED` inmediatamente       |
| `POST` | `/email/sync`  | Envío **sincrónico** — espera el resultado (`SENT` / `FAILED`) |

**Body:**

```json
{
  "account_id": 1,
  "to": ["destinatario@example.com"],
  "cc": ["copia@example.com"],
  "bcc": ["oculto@example.com"],
  "template_id": 1,
  "variables": { "user_name": "Ana", "reset_link": "https://..." },
  "subject": "Asunto (solo si no hay plantilla)",
  "body": "<h1>HTML (solo si no hay plantilla)</h1>",
  "attachments": [
    {
      "filename": "adjunto.pdf",
      "content": "<base64>",
      "mime_type": "application/pdf"
    }
  ]
}
```

- Si se usa `template_id`, `subject` y `body` son opcionales (se toman de la plantilla).
- Si no se usa `template_id`, `subject` y `body` son requeridos.

### Historial — `/api/email-history`

| Método | Endpoint                   | Descripción                             |
|--------|----------------------------|-----------------------------------------|
| `GET`  | `/`                        | Listar correos enviados (paginado)      |
| `GET`  | `/{id}`                    | Detalle de un correo                    |
| `GET`  | `/account/{id}/stats`      | Estadísticas por cuenta                 |

**Query params** en `GET /`:
- `page`, `per_page`
- `account_id` — filtrar por cuenta
- `email_status` — `PENDING` · `SENT` · `FAILED` · `QUEUED`

**Respuesta de stats:**

```json
{ "total": 120, "SENT": 110, "FAILED": 5, "PENDING": 3, "QUEUED": 2 }
```

### Utilidades

| Método | Endpoint   | Auth | Descripción                                |
|--------|------------|------|--------------------------------------------|
| `GET`  | `/`        | No   | Bienvenida y links a docs                  |
| `GET`  | `/health`  | No   | Estado del servicio y conexión a BD        |

---

## Ejemplos con curl

### Crear cuenta SMTP

```bash
curl -X POST http://localhost:8000/api/email-accounts/ \
  -H "X-API-Key: <tu_api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gmail Principal",
    "email": "tu-email@gmail.com",
    "provider_type": "SMTP",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "tu-email@gmail.com",
    "smtp_password": "tu-app-password",
    "from_name": "Mi Servicio"
  }'
```

### Crear plantilla

```bash
curl -X POST http://localhost:8000/api/email-templates/ \
  -H "X-API-Key: <tu_api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "name": "Bienvenida",
    "template_type": "GENERAL",
    "subject": "Bienvenido, {{ user_name }}",
    "html_content": "<h1>Hola {{ user_name }}</h1>",
    "variables": "[\"user_name\"]"
  }'
```

### Enviar correo (asincrónico)

```bash
curl -X POST http://localhost:8000/api/send/email \
  -H "X-API-Key: <tu_api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "template_id": 1,
    "to": ["destinatario@example.com"],
    "variables": { "user_name": "Ana" }
  }'
```

### Enviar correo libre (sincrónico)

```bash
curl -X POST http://localhost:8000/api/send/email/sync \
  -H "X-API-Key: <tu_api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "to": ["destinatario@example.com"],
    "subject": "Prueba directa",
    "body": "<p>Hola desde el servicio.</p>"
  }'
```

---

## Pruebas

```bash
# Todas las pruebas
python -m pytest tests/ -v

# Con cobertura
python -m pytest tests/ --cov=app --cov-report=html
```

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `401 Unauthorized` | Header `X-API-Key` ausente o incorrecto | Incluir el header con la clave del `.env` |
| `string index out of range` al iniciar | `DB_SCHEMA` vacío en `.env` | Establecer `DB_SCHEMA=public` |
| Error de conexión SMTP | Credenciales o puerto incorrecto | Verificar `SMTP_*` en `.env`; Gmail requiere contraseña de app |
| Tablas no creadas | La BD no existe al iniciar | Crear la base de datos en PostgreSQL antes de arrancar |
