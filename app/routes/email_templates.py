"""
Rutas para gestión de plantillas de correo
Autor: Anthony Martinez
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import EmailTemplate, EmailAccount
from app.schemas import (
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplateResponse,
)

router = APIRouter(prefix="/api/email-templates", tags=["Email Templates"])


@router.post("/", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_email_template(
    template: EmailTemplateCreate,
    db: Session = Depends(get_db),
):
    """Crear una nueva plantilla de correo"""
    # Verificar que la cuenta existe
    account = db.query(EmailAccount).filter(EmailAccount.id == template.account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta de correo no encontrada",
        )
    
    # Verificar si la plantilla ya existe
    existing = db.query(EmailTemplate).filter(
        (EmailTemplate.account_id == template.account_id) &
        (EmailTemplate.name == template.name)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La plantilla con este nombre ya existe para esta cuenta",
        )
    
    db_template = EmailTemplate(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return db_template


@router.get("/")
def list_email_templates(
    page: int = Query(1, ge=1, description="Número de página (comienza en 1)"),
    per_page: int = Query(10, ge=1, le=100, description="Elementos por página (máximo 100)"),
    account_id: int = Query(None, description="Filtrar por ID de cuenta"),
    db: Session = Depends(get_db),
):
    """
    Listar plantillas de correo con paginación
    
    **Parámetros:**
    - page: Número de página (por defecto 1)
    - per_page: Elementos por página (por defecto 10, máximo 100)
    - account_id: Filtrar por ID de cuenta - opcional
    
    **Respuesta:**
    - data: Lista de plantillas
    - total: Total de plantillas
    - page: Página actual
    - per_page: Elementos por página
    - total_pages: Total de páginas
    """
    query = db.query(EmailTemplate)
    
    if account_id:
        query = query.filter(EmailTemplate.account_id == account_id)
    
    # Obtener total
    total = query.count()
    
    # Calcular paginación
    skip = (page - 1) * per_page
    total_pages = (total + per_page - 1) // per_page
    
    # Obtener datos
    templates = query.offset(skip).limit(per_page).all()
    
    return {
        "data": templates,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.get("/{template_id}", response_model=EmailTemplateResponse)
def get_email_template(
    template_id: int,
    db: Session = Depends(get_db),
):
    """Obtener una plantilla de correo por ID"""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla de correo no encontrada",
        )
    
    return template


@router.put("/{template_id}", response_model=EmailTemplateResponse)
def update_email_template(
    template_id: int,
    template_update: EmailTemplateUpdate,
    db: Session = Depends(get_db),
):
    """Actualizar una plantilla de correo"""
    db_template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    
    if not db_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla de correo no encontrada",
        )
    
    # Actualizar solo los campos proporcionados
    update_data = template_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_template, field, value)
    
    db.commit()
    db.refresh(db_template)
    
    return db_template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email_template(
    template_id: int,
    db: Session = Depends(get_db),
):
    """Eliminar una plantilla de correo"""
    db_template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    
    if not db_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla de correo no encontrada",
        )
    
    db.delete(db_template)
    db.commit()
    
    return None


@router.get("/account/{account_id}/by-type")
def get_templates_by_account_and_type(
    account_id: int,
    page: int = Query(1, ge=1, description="Número de página (comienza en 1)"),
    per_page: int = Query(10, ge=1, le=100, description="Elementos por página (máximo 100)"),
    template_type: str = Query(None, description="Filtrar por tipo de plantilla"),
    db: Session = Depends(get_db),
):
    """
    Obtener plantillas por cuenta y tipo con paginación
    
    **Parámetros:**
    - account_id: ID de la cuenta (requerido)
    - page: Número de página (por defecto 1)
    - per_page: Elementos por página (por defecto 10, máximo 100)
    - template_type: Filtrar por tipo (registration_confirmation, password_reset, general) - opcional
    
    **Respuesta:**
    - data: Lista de plantillas
    - total: Total de plantillas
    - page: Página actual
    - per_page: Elementos por página
    - total_pages: Total de páginas
    """
    query = db.query(EmailTemplate).filter(EmailTemplate.account_id == account_id)
    
    if template_type:
        query = query.filter(EmailTemplate.template_type == template_type)
    
    # Obtener total
    total = query.count()
    
    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron plantillas",
        )
    
    # Calcular paginación
    skip = (page - 1) * per_page
    total_pages = (total + per_page - 1) // per_page
    
    # Obtener datos
    templates = query.offset(skip).limit(per_page).all()
    
    return {
        "data": templates,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }
