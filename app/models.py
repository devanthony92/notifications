"""
Modelos de base de datos para Email Notification Service
Autor: Anthony Martinez
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, LargeBinary
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.dialects.postgresql import ENUM
from datetime import datetime, timezone
from app.config import settings
import enum

class Base(DeclarativeBase):
    pass


class EmailProviderType(str, enum.Enum):
    """Tipos de proveedores de correo"""
    SMTP = "SMTP"
    AZURE = "AZURE"


class EmailAccountStatus(str, enum.Enum):
    """Estados posibles de una cuenta de correo"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class TemplateType(str, enum.Enum):
    """Tipos de plantillas disponibles"""
    REGISTRATION_CONFIRMATION = "REGISTRATION_CONFIRMATION"
    PASSWORD_RESET = "PASSWORD_RESET"
    GENERAL = "GENERAL"


class EmailStatus(str, enum.Enum):
    """Estados posibles de un correo enviado"""
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    QUEUED = "QUEUED"


_schema = settings.db_schema or None

EmailAccountStatusEnum = ENUM(
    "ACTIVE",
    "INACTIVE",
    "SUSPENDED",
    name="email_account_status",
    schema=_schema,
    create_type=True,
)

EmailStatusEnum = ENUM(
    "PENDING",
    "SENT",
    "FAILED",
    "QUEUED",
    name="email_status",
    schema=_schema,
    create_type=True,
)

EmailProviderTypeEnum = ENUM(
    "SMTP",
    "AZURE",
    name="email_provider_type",
    schema=_schema,
    create_type=True,
)

TemplateTypeEnum = ENUM(
    "REGISTRATION_CONFIRMATION",
    "PASSWORD_RESET",
    "GENERAL",
    name="template_type",
    schema=_schema,
    create_type=True,
)

class EmailAccount(Base):
    """Modelo para almacenar cuentas de correo configuradas"""
    __tablename__ = "email_accounts"
    __table_args__ = {"schema": _schema} if _schema else {}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    provider_type = Column(EmailProviderTypeEnum, default=EmailProviderType.SMTP.value, nullable=False)
    
    # Campos SMTP
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_user = Column(String(255), nullable=True)
    smtp_password = Column(String(500), nullable=True)  # Debería estar encriptado en producción
    
    # Campos Azure
    azure_endpoint = Column(String(500), nullable=True)
    azure_client_id = Column(String(500), nullable=True)
    azure_client_secret = Column(String(500), nullable=True)  # Debería estar encriptado en producción
    azure_tenant_id = Column(String(500), nullable=True)
    
    from_name = Column(String(255), nullable=False)
    status = Column(EmailAccountStatusEnum, nullable=False, default=EmailAccountStatus.ACTIVE.value)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    templates = relationship("EmailTemplate", back_populates="account", cascade="all, delete-orphan")
    sent_emails = relationship("SentEmail", back_populates="account", cascade="all, delete-orphan")


class EmailTemplate(Base):
    """Modelo para almacenar plantillas de correo"""
    __tablename__ = "email_templates"
    __table_args__ = {"schema": _schema} if _schema else {}

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey(f"{_schema}.email_accounts.id" if _schema else "email_accounts.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    template_type = Column(TemplateTypeEnum, default=TemplateType.GENERAL.value, nullable=False)
    subject = Column(String(500), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)
    variables = Column(Text, nullable=True)  # JSON con variables disponibles
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    account = relationship("EmailAccount", back_populates="templates")
    sent_emails = relationship("SentEmail", back_populates="template", cascade="all, delete-orphan")


class SentEmail(Base):
    """Modelo para registrar correos enviados"""
    __tablename__ = "sent_emails"
    __table_args__ = {"schema": _schema} if _schema else {}

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey(f"{_schema}.email_accounts.id" if _schema else "email_accounts.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey(f"{_schema}.email_templates.id" if _schema else "email_templates.id"), nullable=True, index=True)
    to_email = Column(String(255), nullable=False, index=True)
    cc = Column(Text, nullable=True)  # JSON con lista de correos CC
    bcc = Column(Text, nullable=True)  # JSON con lista de correos BCC
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(EmailStatusEnum, default=EmailStatus.PENDING.value, index=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    account = relationship("EmailAccount", back_populates="sent_emails")
    template = relationship("EmailTemplate", back_populates="sent_emails")
    attachments = relationship("EmailAttachment", back_populates="sent_email", cascade="all, delete-orphan")


class EmailAttachment(Base):
    """Modelo para almacenar adjuntos de correos"""
    __tablename__ = "email_attachments"
    __table_args__ = {"schema": _schema} if _schema else {}

    id = Column(Integer, primary_key=True, index=True)
    sent_email_id = Column(Integer, ForeignKey(f"{_schema}.sent_emails.id" if _schema else "sent_emails.id"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    file_content = Column(LargeBinary, nullable=False)
    mime_type = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    sent_email = relationship("SentEmail", back_populates="attachments")
