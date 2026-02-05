# Email notification service

**Autor:** Fabio Garcia

Servicio backend completo para gestión y envío de notificaciones por correo electrónico construido con FastAPI. Proporciona APIs CRUD para gestionar cuentas de correo, plantillas personalizadas y envío asincrónico mediante SMTP o Microsoft Graph (O365).

## Características principales

- **Gestión de cuentas de correo**: Crear, leer, actualizar y eliminar cuentas configuradas
- **Soporte dual de proveedores**: SMTP y Microsoft Graph (O365)
- **Gestión de plantillas**: Crear plantillas de correo reutilizables con variables dinámicas
- **Tipos de plantillas**: Confirmación de registro, recuperación de contraseña y plantilla general
- **Envío asincrónico**: Envío de correos en background para respuestas rápidas
- **Soporte de adjuntos**: Envío de correos con archivos adjuntos
- **CC y BCC**: Soporte para destinatarios en copia y copia oculta
- **Variables dinámicas**: Reemplazo de variables en plantillas usando Jinja2
- **Historial de correos**: Registro completo de todos los correos enviados
- **Base de datos flexible**: Soporte para PostgreSQL, MySQL y SQL Server
- **Pruebas completas**: Suite de pruebas unitarias con cobertura completa

## Estructura del proyecto

```
email-notification-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Aplicación principal FastAPI
│   ├── config.py              # Configuración de la aplicación
│   ├── database.py            # Configuración de base de datos
│   ├── models.py              # Modelos SQLAlchemy
│   ├── schemas.py             # Esquemas Pydantic
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── email_accounts.py  # APIs para cuentas de correo
│   │   ├── email_templates.py # APIs para plantillas
│   │   ├── send_email.py      # APIs para envío de correos
│   │   └── email_history.py   # APIs para historial
│   ├── services/
│   │   ├── __init__.py
│   │   └── email_service.py   # Servicio de envío (SMTP y O365)
│   └── templates/
│       ├── registration_confirmation.html
│       ├── password_reset.html
│       └── general.html
├── tests/
│   ├── __init__.py
│   ├── test_email_accounts.py
│   ├── test_email_templates.py
│   └── test_send_email.py
├── requirements.txt
├── .env.example
└── README.md
```

## Instalación

### Requisitos previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Una base de datos: PostgreSQL, MySQL o SQL Server

### Pasos de instalación

1. **Clonar o descargar el proyecto**

```bash
cd email-notification-service
```

2. **Crear un entorno virtual**

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Inicializar la base de datos**

```bash
python -c "from app.database import init_db; init_db()"
```

## Configuración

### Variables de entorno (.env)

#### Base de datos

Selecciona una de las siguientes opciones:

**PostgreSQL (recomendado):**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/email_notification_db
```

**MySQL:**
```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/email_notification_db
```

**SQL Server:**
```env
DATABASE_URL=mssql+pyodbc://user:password@localhost/email_notification_db?driver=ODBC+Driver+17+for+SQL+Server
```

#### SMTP (para envío vía SMTP)

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-contraseña-app
SMTP_FROM_EMAIL=tu-email@gmail.com
SMTP_FROM_NAME=Tu Nombre
```

#### Microsoft Graph / O365 (para envío vía O365)

```env
O365_CLIENT_ID=tu-client-id
O365_CLIENT_SECRET=tu-client-secret
O365_TENANT_ID=tu-tenant-id
```

**Cómo obtener las credenciales de O365:**

1. Ir a [Azure Portal](https://portal.azure.com)
2. Buscar "App registrations"
3. Crear una nueva aplicación
4. Copiar el **Client ID** y **Tenant ID**
5. Crear un **Client Secret**
6. Agregar permisos: `Mail.Send`

### Configuración de Gmail para SMTP

Para usar Gmail como proveedor SMTP:

1. Habilitar la autenticación de dos factores en tu cuenta de Google
2. Generar una contraseña de aplicación específica
3. Usar esa contraseña en la variable `SMTP_PASSWORD`

## Uso

### Iniciar el servidor

```bash
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en `http://localhost:8000`

### Documentación interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## APIs disponibles

### Cuentas de correo

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/email-accounts/` | Crear nueva cuenta |
| GET | `/api/email-accounts/` | Listar todas las cuentas |
| GET | `/api/email-accounts/{id}` | Obtener cuenta por ID |
| PUT | `/api/email-accounts/{id}` | Actualizar cuenta |
| DELETE | `/api/email-accounts/{id}` | Eliminar cuenta |
| PATCH | `/api/email-accounts/{id}/status` | Cambiar estado de cuenta |

### Plantillas de correo

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/email-templates/` | Crear nueva plantilla |
| GET | `/api/email-templates/` | Listar todas las plantillas |
| GET | `/api/email-templates/{id}` | Obtener plantilla por ID |
| PUT | `/api/email-templates/{id}` | Actualizar plantilla |
| DELETE | `/api/email-templates/{id}` | Eliminar plantilla |
| GET | `/api/email-templates/account/{id}/by-type` | Obtener por tipo |

### Envío de correos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/send/email` | Enviar correo (asincrónico) |
| POST | `/api/send/email/sync` | Enviar correo (sincrónico) |

### Historial

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/email-history/` | Listar correos enviados |
| GET | `/api/email-history/{id}` | Obtener correo por ID |
| GET | `/api/email-history/account/{id}/stats` | Estadísticas de cuenta |

## Ejemplos de uso

### 1. Crear una cuenta SMTP

```bash
curl -X POST "http://localhost:8000/api/email-accounts/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gmail Principal",
    "email": "tu-email@gmail.com",
    "provider_type": "smtp",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "tu-email@gmail.com",
    "smtp_password": "tu-contraseña-app",
    "from_name": "Tu Nombre"
  }'
```

### 2. Crear una cuenta O365

```bash
curl -X POST "http://localhost:8000/api/email-accounts/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "O365 Corporativo",
    "email": "tu-email@empresa.com",
    "provider_type": "azure",
    "azure_client_id": "tu-client-id",
    "azure_client_secret": "tu-client-secret",
    "azure_tenant_id": "tu-tenant-id",
    "from_name": "Tu Nombre"
  }'
```

### 3. Crear una plantilla

```bash
curl -X POST "http://localhost:8000/api/email-templates/" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "name": "Confirmación de Registro",
    "template_type": "registration_confirmation",
    "subject": "Confirma tu registro",
    "html_content": "<h1>Bienvenido {{ user_name }}</h1>",
    "variables": "[\"user_name\", \"confirmation_link\"]"
  }'
```

### 4. Enviar un correo

```bash
curl -X POST "http://localhost:8000/api/send/email" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "template_id": 1,
    "to": ["destinatario@example.com"],
    "variables": {
      "user_name": "John Doe",
      "confirmation_link": "https://example.com/confirm/123"
    }
  }'
```

### 5. Enviar correo sin plantilla

```bash
curl -X POST "http://localhost:8000/api/send/email" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "to": ["destinatario@example.com"],
    "cc": ["cc@example.com"],
    "bcc": ["bcc@example.com"],
    "subject": "Hola desde Email Service",
    "body": "<h1>¡Bienvenido!</h1><p>Este es un correo de prueba.</p>"
  }'
```

## Pruebas

### Ejecutar todas las pruebas

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

### Ejecutar pruebas específicas

```bash
# Pruebas de cuentas de correo
python -m pytest tests/test_email_accounts.py -v

# Pruebas de plantillas
python -m pytest tests/test_email_templates.py -v

# Pruebas de envío
python -m pytest tests/test_send_email.py -v
```

### Cobertura de pruebas

```bash
python -m pytest tests/ --cov=app --cov-report=html
```

## Modelos de base de datos

### EmailAccount

Almacena las cuentas de correo configuradas.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | ID único |
| name | String | Nombre de la cuenta |
| email | String | Dirección de correo |
| provider_type | Enum | Tipo de proveedor (smtp, azure) |
| smtp_host | String | Host SMTP (solo para SMTP) |
| smtp_port | Integer | Puerto SMTP (solo para SMTP) |
| smtp_user | String | Usuario SMTP (solo para SMTP) |
| smtp_password | String | Contraseña SMTP (solo para SMTP) |
| azure_client_id | String | Client ID de O365 (solo para Azure) |
| azure_client_secret | String | Client Secret de O365 (solo para Azure) |
| azure_tenant_id | String | Tenant ID de O365 (solo para Azure) |
| from_name | String | Nombre para mostrar |
| status | Enum | Estado (active, inactive, suspended) |
| created_at | DateTime | Fecha de creación |
| updated_at | DateTime | Fecha de actualización |

### EmailTemplate

Almacena las plantillas de correo.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | ID único |
| account_id | Integer | ID de la cuenta |
| name | String | Nombre de la plantilla |
| template_type | Enum | Tipo (registration_confirmation, password_reset, general) |
| subject | String | Asunto del correo |
| html_content | Text | Contenido HTML |
| text_content | Text | Contenido de texto |
| variables | Text | Variables disponibles (JSON) |
| is_active | Boolean | Si está activa |
| created_at | DateTime | Fecha de creación |
| updated_at | DateTime | Fecha de actualización |

### SentEmail

Registro de correos enviados.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | ID único |
| account_id | Integer | ID de la cuenta |
| template_id | Integer | ID de la plantilla |
| to_email | String | Destinatario principal |
| cc | Text | Destinatarios CC (JSON) |
| bcc | Text | Destinatarios BCC (JSON) |
| subject | String | Asunto |
| body | Text | Cuerpo del correo |
| status | Enum | Estado (pending, sent, failed, queued) |
| error_message | Text | Mensaje de error |
| retry_count | Integer | Número de reintentos |
| sent_at | DateTime | Fecha de envío |
| created_at | DateTime | Fecha de creación |
| updated_at | DateTime | Fecha de actualización |

## Plantillas incluidas

### 1. Confirmación de registro

Plantilla para confirmar registros de nuevos usuarios con colores de Ambiente Bogotá.

**Variables disponibles:**
- `user_name`: Nombre del usuario
- `user_email`: Correo del usuario
- `registration_date`: Fecha de registro
- `confirmation_link`: Enlace de confirmación

### 2. Recuperación de contraseña

Plantilla para recuperación de contraseña con instrucciones claras.

**Variables disponibles:**
- `user_name`: Nombre del usuario
- `reset_link`: Enlace para restablecer contraseña
- `recovery_code`: Código de recuperación
- `support_link`: Enlace de soporte

### 3. Plantilla general

Plantilla flexible para cualquier tipo de correo.

**Variables disponibles:**
- `title`: Título del correo
- `subtitle`: Subtítulo
- `greeting`: Saludo personalizado
- `body`: Cuerpo del correo
- `cta_text`: Texto del botón
- `cta_link`: Enlace del botón
- `info_box_content`: Contenido de caja informativa
- `footer_note`: Nota al pie

## Solución de problemas

### Error de conexión SMTP

Si obtienes errores de conexión SMTP:

1. Verifica que las credenciales sean correctas
2. Asegúrate de que el puerto SMTP sea correcto (587 para TLS)
3. Para Gmail, usa contraseña de aplicación específica
4. Comprueba que el firewall no bloquee la conexión

### Error de autenticación O365

Si obtienes errores de autenticación con O365:

1. Verifica que el Client ID y Secret sean correctos
2. Asegúrate de que el Tenant ID sea correcto
3. Comprueba que la aplicación tenga permisos `Mail.Send`
4. Verifica que no haya expirado el Client Secret

### Error de base de datos

Si obtienes errores de base de datos:

1. Asegúrate de que la base de datos esté inicializada
2. Verifica la URL de conexión en `.env`
3. Comprueba los permisos de acceso a la base de datos
4. Para SQL Server, asegúrate de tener el driver ODBC instalado

### Pruebas fallando

Si las pruebas fallan:

1. Asegúrate de que todas las dependencias estén instaladas
2. Ejecuta `python -m pytest tests/ -v` para ver detalles
3. Verifica que no haya procesos usando el puerto 8000

## Desarrollo

### Agregar nuevas plantillas

1. Crear archivo HTML en `app/templates/`
2. Usar variables con sintaxis `{{ variable_name }}`
3. Crear entrada en la base de datos con tipo correspondiente

### Agregar nuevas rutas

1. Crear archivo en `app/routes/`
2. Definir router y endpoints
3. Incluir router en `app/main.py`

### Agregar nuevas pruebas

1. Crear archivo en `tests/`
2. Usar `TestClient` de FastAPI
3. Ejecutar con `pytest`

## Licencia

Este proyecto está disponible bajo licencia MIT.

## Soporte

Para reportar problemas o sugerencias, por favor contacta al equipo de desarrollo.

## Changelog

### v2.0.0 (2025-12-19)

- Soporte para múltiples bases de datos (PostgreSQL, MySQL, SQL Server)
- Integración con Microsoft Graph (O365) usando python-o365
- Configuración flexible de proveedores (SMTP o O365)
- Documentación mejorada
- Pruebas completas

### v1.0.0 (2025-12-19)

- Versión inicial del servicio
- APIs CRUD completas para cuentas y plantillas
- Envío asincrónico de correos vía SMTP
- Soporte para adjuntos
- Plantillas personalizadas
- Suite de pruebas completa
