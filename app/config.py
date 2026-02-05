"""
Configuración de la aplicación Email Notification Service
Autor: Anthony Martinez
"""

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
    api_description: str = "API para gestionar notificaciones por correo electrónico con soporte SMTP y Microsoft Graph (O365)"
    
    # ==================== SMTP CONFIGURATION ====================
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Email Notification Service"
    
    # ==================== MICROSOFT GRAPH / O365 CONFIGURATION ====================
    o365_client_id: str = ""
    o365_client_secret: str = ""
    o365_tenant_id: str = ""
    
    # ==================== REDIS ====================
    redis_url: str = "redis://localhost:6379/0"
    
    # ==================== CONFIGURACIÓN DE LA APLICACIÓN ====================
    max_upload_size: int = 10485760  # 10MB
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # ==================== CONFIGURACIÓN DE CORREOS ====================
    email_timeout: int = 30
    max_retries: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_database_url(self) -> str:
        """
        Construir la URL de la base de datos automáticamente
        
        Si database_url está definido, lo usa.
        Si no, construye la URL usando los parámetros individuales.
        
        Soporta:
        - SQLite: sqlite:///./email_notification.db
        - PostgreSQL: postgresql://user:password@host:port/dbname
        - MySQL: mysql+pymysql://user:password@host:port/dbname
        - SQL Server: mssql+pyodbc://user:password@host:port/dbname?driver=...
        """
        # Si se proporciona database_url explícitamente, usarlo
        if self.database_url:
            return self.database_url
        
        # Construir URL automáticamente basado en el tipo de BD
        db_type = self.database_type.lower()
        
        if db_type == "sqlite":
            return f"sqlite:///./{self.database_name}"
        
        elif db_type == "postgresql":
            return (
                f"postgresql://{self.database_user}:{self.database_password}@"
                f"{self.database_host}:{self.database_port}/{self.database_name}"
            )
        
        elif db_type == "mysql":
            return (
                f"mysql+pymysql://{self.database_user}:{self.database_password}@"
                f"{self.database_host}:{self.database_port}/{self.database_name}"
            )
        
        elif db_type == "mssql":
            return (
                f"mssql+pyodbc://{self.database_user}:{self.database_password}@"
                f"{self.database_host}:{self.database_port}/{self.database_name}"
                f"?driver=ODBC+Driver+17+for+SQL+Server"
            )
        
        else:
            raise ValueError(
                f"Tipo de base de datos no soportado: {db_type}. "
                f"Soportados: sqlite, postgresql, mysql, mssql"
            )


@lru_cache()
def get_settings() -> Settings:
    """Obtener instancia de configuración (cached)"""
    return Settings()


settings = get_settings()
