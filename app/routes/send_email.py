"""
Rutas para envío de correos electrónicos
Autor: Anthony Martinez

Proporciona dos endpoints:
1. /api/send/email (asincrónico): Retorna inmediatamente, envía en background
2. /api/send/email/sync (sincrónico): Espera a que se complete el envío
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import EmailAccount, EmailTemplate
from app.schemas import SendEmailRequest, SendEmailResponse
from app.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/send", tags=["Send Email"])


@router.post("/email", response_model=SendEmailResponse)
async def send_email(
    request: SendEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Enviar un correo electrónico de forma ASINCRÓNICA
    
    **Diferencia con /email/sync:**
    - Retorna inmediatamente con estado "queued"
    - El envío se realiza en background
    - Ideal para aplicaciones que necesitan respuesta rápida
    - El correo se envía después de retornar la respuesta
    
    **Parámetros:**
    - account_id: ID de la cuenta de correo a usar
    - to: Lista de destinatarios
    - subject: Asunto del correo (opcional si usa plantilla)
    - body: Cuerpo del correo (opcional si usa plantilla)
    - template_id: ID de plantilla (opcional)
    - cc: Destinatarios en copia (opcional)
    - bcc: Destinatarios en copia oculta (opcional)
    - variables: Variables para reemplazar en plantilla (opcional)
    - attachments: Adjuntos (opcional)
    
    **Respuesta:**
    - message: Descripción del resultado
    - email_id: ID del correo (0 si aún no se asignó)
    - status: "queued" (encolado para envío)
    """
    # Validar que la cuenta existe
    email_account = db.query(EmailAccount).filter(
        EmailAccount.id == request.account_id
    ).first()
    
    if not email_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta de correo no encontrada",
        )
    
    # Si se especifica una plantilla, obtenerla
    template = None
    if request.template_id:
        template = db.query(EmailTemplate).filter(
            EmailTemplate.id == request.template_id
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plantilla de correo no encontrada",
            )
        
        # Si no se especifica asunto o body, usar los de la plantilla
        subject = request.subject or template.subject
        body = request.body or template.html_content
    else:
        if not request.subject or not request.body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere subject y body si no se especifica una plantilla",
            )
        subject = request.subject
        body = request.body
    
    # Agregar tarea de envío en background
    background_tasks.add_task(
        EmailService.send_email,
        db=db,
        email_account=email_account,
        to_emails=request.to,
        subject=subject,
        body=body,
        cc_emails=request.cc,
        bcc_emails=request.bcc,
        attachments=request.attachments,
        template_id=request.template_id,
        variables=request.variables,
    )
    
    return SendEmailResponse(
        message="Correo encolado para envío",
        email_id=None,
        status="QUEUED",
    )


@router.post("/email/sync", response_model=SendEmailResponse)
async def send_email_sync(
    request: SendEmailRequest,
    db: Session = Depends(get_db),
):
    """
    Enviar un correo electrónico de forma SINCRÓNICA
    
    **Diferencia con /email:**
    - Espera a que se complete el envío antes de responder
    - Retorna el estado final (sent o failed)
    - Más lento pero garantiza el resultado inmediato
    - Ideal para validar que el correo se envió correctamente
    
    **Parámetros:**
    - account_id: ID de la cuenta de correo a usar
    - to: Lista de destinatarios
    - subject: Asunto del correo (opcional si usa plantilla)
    - body: Cuerpo del correo (opcional si usa plantilla)
    - template_id: ID de plantilla (opcional)
    - cc: Destinatarios en copia (opcional)
    - bcc: Destinatarios en copia oculta (opcional)
    - variables: Variables para reemplazar en plantilla (opcional)
    - attachments: Adjuntos (opcional)
    
    **Respuesta:**
    - message: Descripción del resultado
    - email_id: ID del correo
    - status: "SENT" (enviado) o "FAILED" (falló)
    """
    # Validar que la cuenta existe
    email_account = db.query(EmailAccount).filter(
        EmailAccount.id == request.account_id
    ).first()
    
    if not email_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta de correo no encontrada",
        )
    
    # Si se especifica una plantilla, obtenerla
    template = None
    if request.template_id:
        template = db.query(EmailTemplate).filter(
            EmailTemplate.id == request.template_id
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plantilla de correo no encontrada",
            )
        
        # Si no se especifica asunto o body, usar los de la plantilla
        subject = request.subject or template.subject
        body = request.body or template.html_content
    else:
        if not request.subject or not request.body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere subject y body si no se especifica una plantilla",
            )
        subject = request.subject
        body = request.body
    
    # Enviar correo
    success, message, email_id = await EmailService.send_email(
        db=db,
        email_account=email_account,
        to_emails=request.to,
        subject=subject,
        body=body,
        cc_emails=request.cc,
        bcc_emails=request.bcc,
        attachments=request.attachments,
        template_id=request.template_id,
        variables=request.variables,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
        )
    
    return SendEmailResponse(
        message=message,
        email_id=email_id,
        status="SENT" if success else "FAILED",
    )
