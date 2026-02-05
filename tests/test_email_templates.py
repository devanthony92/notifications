import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from app.database import get_db, Base

# Crear base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    """Limpiar la base de datos antes de cada prueba"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def create_test_account():
    """Crear una cuenta de prueba"""
    response = client.post(
        "/api/email-accounts/",
        json={
            "name": "Gmail Principal",
            "email": "test@gmail.com",
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "test@gmail.com",
            "smtp_password": "password123",
            "from_name": "Test User",
        },
    )
    return response.json()["id"]


class TestEmailTemplates:
    """Pruebas para la gestión de plantillas de correo"""
    
    def test_create_email_template(self):
        """Probar creación de una plantilla de correo"""
        account_id = create_test_account()
        
        response = client.post(
            "/api/email-templates/",
            json={
                "account_id": account_id,
                "name": "Confirmación de Registro",
                "template_type": "REGISTRATION_CONFIRMATION",
                "subject": "Confirma tu registro",
                "html_content": "<h1>Bienvenido</h1>",
                "text_content": "Bienvenido",
                "variables": '["user_name", "confirmation_link"]',
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Confirmación de Registro"
        assert data["template_type"] == "REGISTRATION_CONFIRMATION"
    
    def test_create_duplicate_template(self):
        """Probar que no se puede crear una plantilla con nombre duplicado"""
        account_id = create_test_account()
        
        # Crear primera plantilla
        client.post(
            "/api/email-templates/",
            json={
                "account_id": account_id,
                "name": "Confirmación de Registro",
                "template_type": "REGISTRATION_CONFIRMATION",
                "subject": "Confirma tu registro",
                "html_content": "<h1>Bienvenido</h1>",
            },
        )
        
        # Intentar crear segunda plantilla con mismo nombre
        response = client.post(
            "/api/email-templates/",
            json={
                "account_id": account_id,
                "name": "Confirmación de Registro",
                "template_type": "REGISTRATION_CONFIRMATION",
                "subject": "Confirma tu registro",
                "html_content": "<h1>Bienvenido</h1>",
            },
        )
        assert response.status_code == 400
    
    def test_list_email_templates(self):
        """Probar listado de plantillas de correo"""
        account_id = create_test_account()
        
        # Crear varias plantillas
        for i in range(3):
            client.post(
                "/api/email-templates/",
                json={
                    "account_id": account_id,
                    "name": f"Plantilla {i}",
                    "template_type": "GENERAL",
                    "subject": f"Asunto {i}",
                    "html_content": f"<h1>Contenido {i}</h1>",
                },
            )
        
        response = client.get("/api/email-templates/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["data"]) == 3
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    def test_get_email_template(self):
        """Probar obtención de una plantilla específica"""
        account_id = create_test_account()
        
        # Crear plantilla
        create_response = client.post(
            "/api/email-templates/",
            json={
                "account_id": account_id,
                "name": "Confirmación de Registro",
                "template_type": "REGISTRATION_CONFIRMATION",
                "subject": "Confirma tu registro",
                "html_content": "<h1>Bienvenido</h1>",
            },
        )
        template_id = create_response.json()["id"]
        
        # Obtener plantilla
        response = client.get(f"/api/email-templates/{template_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["name"] == "Confirmación de Registro"
    
    def test_get_nonexistent_template(self):
        """Probar obtención de una plantilla que no existe"""
        response = client.get("/api/email-templates/999")
        assert response.status_code == 404
    
    def test_update_email_template(self):
        """Probar actualización de una plantilla de correo"""
        account_id = create_test_account()
        
        # Crear plantilla
        create_response = client.post(
            "/api/email-templates/",
            json={
                "account_id": account_id,
                "name": "Confirmación de Registro",
                "template_type": "REGISTRATION_CONFIRMATION",
                "subject": "Confirma tu registro",
                "html_content": "<h1>Bienvenido</h1>",
            },
        )
        template_id = create_response.json()["id"]
        
        # Actualizar plantilla
        response = client.put(
            f"/api/email-templates/{template_id}",
            json={
                "subject": "Nuevo asunto",
                "html_content": "<h1>Nuevo contenido</h1>",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "Nuevo asunto"
        assert data["html_content"] == "<h1>Nuevo contenido</h1>"
    
    def test_delete_email_template(self):
        """Probar eliminación de una plantilla de correo"""
        account_id = create_test_account()
        
        # Crear plantilla
        create_response = client.post(
            "/api/email-templates/",
            json={
                "account_id": account_id,
                "name": "Confirmación de Registro",
                "template_type": "REGISTRATION_CONFIRMATION",
                "subject": "Confirma tu registro",
                "html_content": "<h1>Bienvenido</h1>",
            },
        )
        template_id = create_response.json()["id"]
        
        # Eliminar plantilla
        response = client.delete(f"/api/email-templates/{template_id}")
        assert response.status_code == 204
        
        # Verificar que fue eliminada
        response = client.get(f"/api/email-templates/{template_id}")
        assert response.status_code == 404
    
    def test_get_templates_by_account_and_type(self):
        """Probar obtención de plantillas por cuenta y tipo"""
        account_id = create_test_account()
        
        # Crear plantillas de diferentes tipos
        client.post(
            "/api/email-templates/",
            json={
                "account_id": account_id,
                "name": "Confirmación",
                "template_type": "REGISTRATION_CONFIRMATION",
                "subject": "Confirma tu registro",
                "html_content": "<h1>Bienvenido</h1>",
            },
        )
        
        client.post(
            "/api/email-templates/",
            json={
                "account_id": account_id,
                "name": "Recuperar Contraseña",
                "template_type": "PASSWORD_RESET",
                "subject": "Recupera tu contraseña",
                "html_content": "<h1>Recuperar</h1>",
            },
        )
        
        # Obtener solo plantillas de confirmación
        response = client.get(
            f"/api/email-templates/account/{account_id}/by-type?template_type=REGISTRATION_CONFIRMATION"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["template_type"] == "REGISTRATION_CONFIRMATION"
