"""
Rutas para gestión de cuentas de correo
Autor: Anthony Martinez
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import EmailAccount, EmailAccountStatus, EmailProviderType
from app.schemas import (
    EmailAccountCreate,
    EmailAccountUpdate,
    EmailAccountResponse,
)

router = APIRouter(prefix="/api/email-accounts", tags=["Email Accounts"])


@router.post("/", response_model=EmailAccountResponse, status_code=status.HTTP_201_CREATED)
def create_email_account(
    account: EmailAccountCreate,
    db: Session = Depends(get_db),
):
    """Crear una nueva cuenta de correo (SMTP o Azure)"""
    # Verificar si la cuenta ya existe
    existing = db.query(EmailAccount).filter(
        (EmailAccount.email == account.email) | (EmailAccount.name == account.name)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta de correo o nombre ya existe",
        )
    
    # Validar que se proporcionen los campos necesarios según el proveedor
    if account.provider_type == EmailProviderType.SMTP:
        if not all([account.smtp_host, account.smtp_port, account.smtp_user, account.smtp_password]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para SMTP se requieren: smtp_host, smtp_port, smtp_user, smtp_password",
            )
    elif account.provider_type == EmailProviderType.AZURE:
        if not all([account.azure_client_id, account.azure_client_secret, account.azure_tenant_id]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para Azure se requieren: azure_client_id, azure_client_secret, azure_tenant_id",
            )
    
    db_account = EmailAccount(**account.model_dump())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    return db_account


@router.get("/")
def list_email_accounts(
    page: int = Query(1, ge=1, description="Número de página (comienza en 1)"),
    per_page: int = Query(10, ge=1, le=100, description="Elementos por página (máximo 100)"),
    provider_type: str = Query(None, description="Filtrar por tipo de proveedor (SMTP o AZURE)"),
    db: Session = Depends(get_db),
):
    """
    Listar todas las cuentas de correo con paginación
    
    **Parámetros:**
    - page: Número de página (por defecto 1)
    - per_page: Elementos por página (por defecto 10, máximo 100)
    - provider_type: Filtrar por tipo (SMTP o AZURE) - opcional
    
    **Respuesta:**
    - data: Lista de cuentas
    - total: Total de cuentas
    - page: Página actual
    - per_page: Elementos por página
    - total_pages: Total de páginas
    """
    query = db.query(EmailAccount)
    
    if provider_type:
        try:
            provider = EmailProviderType(provider_type)
            query = query.filter(EmailAccount.provider_type == provider)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Proveedor inválido. Debe ser 'SMTP' o 'AZURE'",
            )
    
    # Obtener total
    total = query.count()
    
    # Calcular paginación
    skip = (page - 1) * per_page
    total_pages = (total + per_page - 1) // per_page
    
    # Obtener datos
    accounts = query.offset(skip).limit(per_page).all()
    
    return {
        "data": accounts,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.get("/{account_id}", response_model=EmailAccountResponse)
def get_email_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    """Obtener una cuenta de correo por ID"""
    account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta de correo no encontrada",
        )
    
    return account


@router.put("/{account_id}", response_model=EmailAccountResponse)
def update_email_account(
    account_id: int,
    account_update: EmailAccountUpdate,
    db: Session = Depends(get_db),
):
    """Actualizar una cuenta de correo"""
    db_account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
    
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta de correo no encontrada",
        )
    
    # Verificar si el nuevo nombre o email ya existe
    if account_update.name and account_update.name != db_account.name:
        existing = db.query(EmailAccount).filter(EmailAccount.name == account_update.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de cuenta ya existe",
            )
    
    if account_update.email and account_update.email != db_account.email:
        existing = db.query(EmailAccount).filter(EmailAccount.email == account_update.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo ya existe",
            )
    
    # Actualizar solo los campos proporcionados
    update_data = account_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.commit()
    db.refresh(db_account)
    
    return db_account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    """Eliminar una cuenta de correo"""
    db_account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
    
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta de correo no encontrada",
        )
    
    db.delete(db_account)
    db.commit()
    
    return None


@router.patch("/{account_id}/status", response_model=EmailAccountResponse)
def update_account_status(
    account_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
):
    """Actualizar el estado de una cuenta de correo"""
    db_account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
    
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta de correo no encontrada",
        )
    
    db_account.status = status_update.get("status", db_account.status)
    db.commit()
    db.refresh(db_account)
    
    return db_account
