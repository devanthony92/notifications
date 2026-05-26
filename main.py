from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings
from app.database import init_db, get_db
from app.routes import email_accounts, email_templates, send_email, email_history
from app.dependencies import verify_api_key
from app.schemas import HealthCheck
import logging

# Configurar logging
logging.basicConfig(
    level=logging.WARNING if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Iniciando aplicación...")
    init_db()
    logger.info("Base de datos inicializada")
    yield


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas — todos los routers requieren X-API-Key
_auth = [Depends(verify_api_key)]
app.include_router(email_accounts.router, dependencies=_auth)
app.include_router(email_templates.router, dependencies=_auth)
app.include_router(send_email.router, dependencies=_auth)
app.include_router(email_history.router, dependencies=_auth)


# Rutas de utilidad
@app.get("/health", response_model=HealthCheck)
async def health_check(db = Depends(get_db)):
    """Verificar el estado de la API"""
    try:
        # Verificar conexión a base de datos
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Error en base de datos: {e}")
        db_status = "unhealthy"
  
    return HealthCheck(
        status="healthy",
        version=settings.api_version,
        database=db_status,
        redis="unknown",
    )

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Bienvenido a Email Notification Service",
        "version": settings.api_version,
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
