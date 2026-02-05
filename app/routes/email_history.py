"""
Rutas para historial de correos enviados
Autor: Anthony Martinez
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import SentEmail, EmailStatus
from app.schemas import SentEmailResponse

router = APIRouter(prefix="/api/email-history", tags=["Email History"])


@router.get("/")
def list_sent_emails(
    page: int = Query(1, ge=1, description="Número de página (comienza en 1)"),
    per_page: int = Query(10, ge=1, le=100, description="Elementos por página (máximo 100)"),
    account_id: int = Query(None, description="Filtrar por ID de cuenta"),
    email_status: str = Query(None, description="Filtrar por estado (PENDING, SENT, FAILED, QUEUED)"),
    db: Session = Depends(get_db),
):
    """
    Listar correos enviados con paginación y filtros
    
    **Parámetros:**
    - page: Número de página (por defecto 1)
    - per_page: Elementos por página (por defecto 10, máximo 100)
    - account_id: Filtrar por ID de cuenta - opcional
    - email_status: Filtrar por estado (PENDING, SENT, FAILED, QUEUED) - opcional
    
    **Respuesta:**
    - data: Lista de correos
    - total: Total de correos
    - page: Página actual
    - per_page: Elementos por página
    - total_pages: Total de páginas
    """
    query = db.query(SentEmail)
    
    if account_id:
        query = query.filter(SentEmail.account_id == account_id)
    
    if email_status:
        try:
            status_enum = EmailStatus(email_status)
            query = query.filter(SentEmail.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado inválido. Debe ser: PENDING, SENT, FAILED o QUEUED",
            )
    
    # Obtener total
    total = query.count()
    
    # Calcular paginación
    skip = (page - 1) * per_page
    total_pages = (total + per_page - 1) // per_page
    
    # Obtener datos ordenados por fecha descendente
    emails = query.order_by(SentEmail.created_at.desc()).offset(skip).limit(per_page).all()
    
    return {
        "data": emails,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.get("/{email_id}", response_model=SentEmailResponse)
def get_sent_email(
    email_id: int,
    db: Session = Depends(get_db),
):
    """Obtener detalles de un correo enviado"""
    email = db.query(SentEmail).filter(SentEmail.id == email_id).first()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correo no encontrado",
        )
    
    return email


@router.get("/account/{account_id}/stats")
def get_account_stats(
    account_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtener estadísticas de envíos de una cuenta
    
    **Parámetros:**
    - account_id: ID de la cuenta
    
    **Respuesta:**
    - total: Total de correos enviados
    - sent: Correos enviados exitosamente
    - failed: Correos que fallaron
    - pending: Correos pendientes
    - queued: Correos encolados
    """
    total = db.query(SentEmail).filter(SentEmail.account_id == account_id).count()
    sent = db.query(SentEmail).filter(
        (SentEmail.account_id == account_id) &
        (SentEmail.status == EmailStatus.SENT)
    ).count()
    failed = db.query(SentEmail).filter(
        (SentEmail.account_id == account_id) &
        (SentEmail.status == EmailStatus.FAILED)
    ).count()
    pending = db.query(SentEmail).filter(
        (SentEmail.account_id == account_id) &
        (SentEmail.status == EmailStatus.PENDING)
    ).count()
    queued = db.query(SentEmail).filter(
        (SentEmail.account_id == account_id) &
        (SentEmail.status == EmailStatus.QUEUED)
    ).count()
    
    return {
        "total": total,
        "SENT": sent,
        "FAILED": failed,
        "PENDING": pending,
        "QUEUED": queued,
    }
