"""
Configuración de base de datos y sesiones
Autor: Anthony Martinez
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from app.config import settings
from app.models import Base
import logging

logger = logging.getLogger(__name__)

# Obtener URL de base de datos (se construye automáticamente si es necesario)
database_url = settings.get_database_url()

logger.info(f"Conectando a base de datos: {settings.database_type.upper()}")

# Configurar el motor de base de datos con pool de conexiones
if settings.database_type.lower() == "sqlite":
    # Para SQLite, usar StaticPool para evitar problemas de conexión
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug,
    )
else:
    # Para MySQL, PostgreSQL y SQL Server, usar QueuePool con configuración optimizada
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,  # Verificar conexiones antes de usarlas
        pool_recycle=3600,   # Reciclar conexiones cada hora
        echo=settings.debug,
        connect_args={
         "options": f"-c search_path={settings.db_schema}"
    }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependencia para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializar la base de datos creando todas las tablas"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        raise


def drop_db():
    """Eliminar todas las tablas de la base de datos (solo para desarrollo)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Base de datos eliminada correctamente")
    except Exception as e:
        logger.error(f"Error al eliminar la base de datos: {e}")
        raise
