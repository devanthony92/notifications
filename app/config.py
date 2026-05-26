"""
Configuración de la aplicación Email Notification Service
Autor: Anthony Martinez
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # ==================== BASE DE DATOS ====================
    # Tipo de base de datos: sqlite, postgresql, mysql, mssql
    database_type: str = ""
    
    # Parámetros individuales de la BD
    database_host: str = ""
    database_port: int 
    database_name: str = ""
    database_user: str = ""
    database_password: str = ""
    
    # URL de base de datos (si se proporciona, se usa en lugar de los parámetros individuales)
    database_url: Optional[str] = None
    db_schema: str = ""  # Schema para PostgreSQL

    # Configuración de pool de conexiones
    database_pool_size: int = 20
    database_max_overflow: int = 40
    
    # ==================== FASTAPI ====================
    debug: bool = True
    api_title: str = "Email Notification Service"
    api_version: str = "1.0.0"
    api_description: str = "API para gestionar notificaciones por correo electrónico con soporte SMTP"
    
    # ==================== SMTP CONFIGURATION ====================
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Email Notification Service"
    
    
    # ==================== SEGURIDAD ====================
    api_key: str = ""   # X-API-Key requerida en todos los endpoints protegidos

    # ==================== CONFIGURACIÓN DE LA APLICACIÓN ====================
    max_upload_size: int = 10485760  # 10MB
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # ==================== CONFIGURACIÓN DE CORREOS ====================
    email_timeout: int = 30
    max_retries: int = 3
    
    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str) and v:
            return v
        data = info.data
        return f"postgresql://{data.get('database_user')}:{data.get('database_password')}@{data.get('database_host')}:{data.get('database_port')}/{data.get('database_name')}"


    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """Obtener instancia de configuración (cached)"""
    return Settings()


settings = get_settings()
