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


def create_test_template(account_id):
    """Crear una plantilla de prueba"""
    response = client.post(
        "/api/email-templates/",
        json={
            "account_id": account_id,
            "name": "Confirmación de Registro",
            "template_type": "registration_confirmation",
            "subject": "Confirma tu registro",
            "html_content": "<h1>Bienvenido {{ user_name }}</h1>",
            "variables": '["user_name", "confirmation_link"]',
        },
    )
    return response.json()["id"]


class TestSendEmail:
    """Pruebas para el envío de correos"""
    
    def test_send_email_with_template(self):
        """Probar envío de correo con plantilla"""
        account_id = create_test_account()
        template_id = create_test_template(account_id)
        
        response = client.post(
            "/api/send/email",
            json={
                "account_id": account_id,
                "template_id": template_id,
                "to": ["recipient@example.com"],
                "variables": {
                    "user_name": "John Doe",
                    "confirmation_link": "https://example.com/confirm/123",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Correo encolado para envío"
        assert data["status"] == "queued"
    
    def test_send_email_without_template(self):
        """Probar envío de correo sin plantilla"""
        account_id = create_test_account()
        
        response = client.post(
            "/api/send/email",
            json={
                "account_id": account_id,
                "to": ["recipient@example.com"],
                "subject": "Asunto del correo",
                "body": "<h1>Contenido del correo</h1>",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
    
    def test_send_email_with_cc_and_bcc(self):
        """Probar envío de correo con CC y BCC"""
        account_id = create_test_account()
        
        response = client.post(
            "/api/send/email",
            json={
                "account_id": account_id,
                "to": ["recipient@example.com"],
                "cc": ["cc@example.com"],
                "bcc": ["bcc@example.com"],
                "subject": "Asunto del correo",
                "body": "<h1>Contenido del correo</h1>",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
    
    def test_send_email_invalid_account(self):
        """Probar envío de correo con cuenta inválida"""
        response = client.post(
            "/api/send/email",
            json={
                "account_id": 999,
                "to": ["recipient@example.com"],
                "subject": "Asunto del correo",
                "body": "<h1>Contenido del correo</h1>",
            },
        )
        assert response.status_code == 404
    
    def test_send_email_invalid_template(self):
        """Probar envío de correo con plantilla inválida"""
        account_id = create_test_account()
        
        response = client.post(
            "/api/send/email",
            json={
                "account_id": account_id,
                "template_id": 999,
                "to": ["recipient@example.com"],
            },
        )
        assert response.status_code == 404
    
    def test_send_email_missing_subject_and_body(self):
        """Probar envío de correo sin asunto ni cuerpo"""
        account_id = create_test_account()
        
        response = client.post(
            "/api/send/email",
            json={
                "account_id": account_id,
                "to": ["recipient@example.com"],
            },
        )
        assert response.status_code == 400
    
    def test_send_email_with_multiple_recipients(self):
        """Probar envío de correo a múltiples destinatarios"""
        account_id = create_test_account()
        
        response = client.post(
            "/api/send/email",
            json={
                "account_id": account_id,
                "to": ["recipient1@example.com", "recipient2@example.com", "recipient3@example.com"],
                "subject": "Asunto del correo",
                "body": "<h1>Contenido del correo</h1>",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
    
    def test_get_email_history(self):
        """Probar obtención del historial de correos"""
        account_id = create_test_account()
        
        # Enviar un correo
        client.post(
            "/api/send/email",
            json={
                "account_id": account_id,
                "to": ["recipient@example.com"],
                "subject": "Asunto del correo",
                "body": "<h1>Contenido del correo</h1>",
            },
        )
        
        # Obtener historial
        response = client.get("/api/email-history/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        assert len(data["data"]) > 0
    
    def test_get_account_stats(self):
        """Probar obtención de estadísticas de una cuenta"""
        account_id = create_test_account()
        
        # Enviar varios correos
        for i in range(3):
            client.post(
                "/api/send/email",
                json={
                    "account_id": account_id,
                    "to": [f"recipient{i}@example.com"],
                    "subject": "Asunto del correo",
                    "body": "<h1>Contenido del correo</h1>",
                },
            )
        
        # Obtener estadísticas
        response = client.get(f"/api/email-history/account/{account_id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        # Los correos fallan porque no hay conexión SMTP real, pero se registran
        assert data["FAILED"] == 3 or data["QUEUED"] == 3 or data["PENDING"] == 3
