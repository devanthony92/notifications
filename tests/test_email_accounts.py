import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from app.database import get_db, Base
from app.models import EmailAccount, EmailAccountStatus

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


class TestEmailAccounts:
    """Pruebas para la gestión de cuentas de correo"""
    
    def test_create_email_account(self):
        """Probar creación de una cuenta de correo"""
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
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@gmail.com"
        assert data["name"] == "Gmail Principal"
        assert data["status"] == "ACTIVE"
    
    def test_create_duplicate_email_account(self):
        """Probar que no se puede crear una cuenta con email duplicado"""
        # Crear primera cuenta
        client.post(
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
        
        # Intentar crear segunda cuenta con mismo email
        response = client.post(
            "/api/email-accounts/",
            json={
                "name": "Gmail Secundario",
                "email": "test@gmail.com",
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_user": "test@gmail.com",
                "smtp_password": "password123",
                "from_name": "Test User",
            },
        )
        assert response.status_code == 400
    
    def test_list_email_accounts(self):
        """Probar listado de cuentas de correo"""
        # Crear varias cuentas
        for i in range(3):
            client.post(
                "/api/email-accounts/",
                json={
                    "name": f"Gmail {i}",
                    "email": f"test{i}@gmail.com",
                    "smtp_host": "smtp.gmail.com",
                    "smtp_port": 587,
                    "smtp_user": f"test{i}@gmail.com",
                    "smtp_password": "password123",
                    "from_name": "Test User",
                },
            )
        
        response = client.get("/api/email-accounts/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["data"]) == 3
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    def test_get_email_account(self):
        """Probar obtención de una cuenta específica"""
        # Crear cuenta
        create_response = client.post(
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
        account_id = create_response.json()["id"]
        
        # Obtener cuenta
        response = client.get(f"/api/email-accounts/{account_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == account_id
        assert data["email"] == "test@gmail.com"
    
    def test_get_nonexistent_email_account(self):
        """Probar obtención de una cuenta que no existe"""
        response = client.get("/api/email-accounts/999")
        assert response.status_code == 404
    
    def test_update_email_account(self):
        """Probar actualización de una cuenta de correo"""
        # Crear cuenta
        create_response = client.post(
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
        account_id = create_response.json()["id"]
        
        # Actualizar cuenta
        response = client.put(
            f"/api/email-accounts/{account_id}",
            json={
                "from_name": "Updated Name",
                "status": "INACTIVE",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["from_name"] == "Updated Name"
        assert data["status"] == "INACTIVE"
    
    def test_delete_email_account(self):
        """Probar eliminación de una cuenta de correo"""
        # Crear cuenta
        create_response = client.post(
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
        account_id = create_response.json()["id"]
        
        # Eliminar cuenta
        response = client.delete(f"/api/email-accounts/{account_id}")
        assert response.status_code == 204
        
        # Verificar que fue eliminada
        response = client.get(f"/api/email-accounts/{account_id}")
        assert response.status_code == 404
    
    def test_update_account_status(self):
        """Probar actualización del estado de una cuenta"""
        # Crear cuenta
        create_response = client.post(
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
        account_id = create_response.json()["id"]
        
        # Cambiar estado
        response = client.patch(
            f"/api/email-accounts/{account_id}/status",
            json={"status": "SUSPENDED"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUSPENDED"
