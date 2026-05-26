"""
isa Servicio de envío de correos electrónicos
Soporta: SMTP
Autor: Anthony Martinez
"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import EmailAccount, SentEmail, EmailStatus, EmailAttachment
from app.schemas import SendEmailRequest
from datetime import datetime, timezone
import base64
from jinja2 import Template

logger = logging.getLogger(__name__)


class EmailService:
    """
    Servicio para enviar correos electrónicos vía SMTP
    Autor: Anthony Martinez
    """
    
    @staticmethod
    async def send_email(
        db: Session,
        email_account: EmailAccount,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List] = None,
        template_id: Optional[int] = None,
        variables: Optional[dict] = None,
    ) -> tuple[bool, str, Optional[int]]:
        """
        Enviar correo electrónico de forma asíncrona
        
        Args:
            db: Sesión de base de datos
            email_account: Cuenta de correo a usar
            to_emails: Lista de correos destinatarios
            subject: Asunto del correo
            body: Cuerpo del correo (HTML)
            cc_emails: Lista de correos CC
            bcc_emails: Lista de correos BCC
            attachments: Lista de adjuntos
            template_id: ID de la plantilla (opcional)
            variables: Variables para reemplazar en la plantilla
            
        Returns:
            Tupla (éxito, mensaje, email_id)
        """
        try:
            # Procesar variables si existen
            if variables:
                body = EmailService._replace_variables(body, variables)
                subject = EmailService._replace_variables(subject, variables)
            
            # Crear registro en base de datos
            cc_str = ",".join(cc_emails) if cc_emails else None
            bcc_str = ",".join(bcc_emails) if bcc_emails else None
            
            sent_email = SentEmail(
                account_id=email_account.id,
                template_id=template_id,
                to_email=to_emails[0] if to_emails else "",
                cc=cc_str,
                bcc=bcc_str,
                subject=subject,
                body=body,
                status=EmailStatus.PENDING,
                
            )
            db.add(sent_email)
            db.commit()
            db.refresh(sent_email)
            
            # Agregar adjuntos si existen
            if attachments:
                for attachment in attachments:
                    email_attachment = EmailAttachment(
                        sent_email_id=sent_email.id,
                        filename=attachment.filename,
                        file_content=base64.b64decode(attachment.content),
                        mime_type=attachment.mime_type,
                    )
                    db.add(email_attachment)
                db.commit()
            
            # Enviar correo vía SMTP
            success, message = await EmailService._send_smtp(
                email_account=email_account,
                to_emails=to_emails,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                subject=subject,
                body=body,
                attachments=attachments,
            )
            
            # Actualizar estado
            if success:
                sent_email.status = EmailStatus.SENT
                sent_email.sent_at = datetime.now(timezone.utc)
            else:
                sent_email.status = EmailStatus.FAILED
                sent_email.error_message = message
                sent_email.retry_count += 1
            
            db.commit()
            
            return success, message, sent_email.id
            
        except Exception as e:
            logger.error(f"Error al enviar correo: {str(e)}")
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    async def _send_smtp(
        email_account: EmailAccount,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List] = None,
    ) -> tuple[bool, str]:
        """
        Enviar correo a través de SMTP
        Autor: Anthony Martinez
        """
        try:
            # Crear mensaje
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{email_account.from_name} <{email_account.email}>"
            message["To"] = ", ".join(to_emails)
            
            if cc_emails:
                message["Cc"] = ", ".join(cc_emails)
            
            # Agregar cuerpo HTML
            message.attach(MIMEText(body, "html"))
            
            # Agregar adjuntos
            if attachments:
                for attachment in attachments:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(base64.b64decode(attachment.content))
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {attachment.filename}",
                    )
                    message.attach(part)
            
            # Enviar correo
            async with aiosmtplib.SMTP(
                hostname=email_account.smtp_host,
                port=email_account.smtp_port,
                use_tls=True,
            ) as smtp:
                await smtp.login(email_account.smtp_user, email_account.smtp_password)
                
                all_recipients = to_emails.copy()
                if cc_emails:
                    all_recipients.extend(cc_emails)
                if bcc_emails:
                    all_recipients.extend(bcc_emails)
                
                await smtp.sendmail(
                    email_account.email,
                    all_recipients,
                    message.as_string(),
                )
            
            logger.info(f"Correo enviado exitosamente vía SMTP a {to_emails}")
            return True, "Correo enviado exitosamente"
            
        except Exception as e:
            logger.error(f"Error al enviar correo SMTP: {str(e)}")
            return False, f"Error SMTP: {str(e)}"
    
    @staticmethod
    def _replace_variables(text: str, variables: dict) -> str:
        """
        Reemplazar variables en el texto usando Jinja2
        Autor: Anthony Martinez
        """
        try:
            template = Template(text)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Error al reemplazar variables: {str(e)}")
            return text
