"""
Esquemas Pydantic para Email Notification Service
Autor: Anthony Martinez
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
from email.utils import parseaddr
from html import escape
from enum import Enum
import re
import bleach

ALLOWED_TAGS = [
    "a", "p", "br", "strong", "em", "ul", "ol", "li",
    "h1", "h2", "h3", "span", "div", "table", "tr", "td"
]

ALLOWED_ATTRS = {
    "a": ["href", "title"],
    "*": ["style"]
}


class EmailProviderType(str, Enum):
    SMTP = "SMTP"
    AZURE = "AZURE"


class EmailAccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class TemplateType(str, Enum):
    REGISTRATION_CONFIRMATION = "REGISTRATION_CONFIRMATION"
    PASSWORD_RESET = "PASSWORD_RESET"
    GENERAL = "GENERAL"


class EmailStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    QUEUED = "QUEUED"


# ==================== Email Account Schemas ====================

class EmailAccountCreateSMTP(BaseModel):
    """Schema para crear una cuenta de correo con SMTP"""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    smtp_host: str = Field(..., min_length=1, max_length=255)
    smtp_port: int = Field(..., ge=1, le=65535)
    smtp_user: str = Field(..., min_length=1, max_length=255)
    smtp_password: str = Field(..., min_length=1, max_length=500)
    from_name: str = Field(..., min_length=1, max_length=255)


class EmailAccountCreateAzure(BaseModel):
    """Schema para crear una cuenta de correo con Azure"""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    azure_endpoint: str = Field(..., min_length=1, max_length=500)
    azure_client_id: str = Field(..., min_length=1, max_length=500)
    azure_client_secret: str = Field(..., min_length=1, max_length=500)
    azure_tenant_id: str = Field(..., min_length=1, max_length=500)
    from_name: str = Field(..., min_length=1, max_length=255)


class EmailAccountCreate(BaseModel):
    """Schema para crear una nueva cuenta de correo (flexible)"""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    provider_type: EmailProviderType = EmailProviderType.SMTP
    # Campos SMTP
    smtp_host: Optional[str] = Field(None, min_length=1, max_length=255)
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_user: Optional[str] = Field(None, min_length=1, max_length=255)
    smtp_password: Optional[str] = Field(None, min_length=1, max_length=500)
    # Campos Azure
    azure_endpoint: Optional[str] = Field(None, min_length=1, max_length=500)
    azure_client_id: Optional[str] = Field(None, min_length=1, max_length=500)
    azure_client_secret: Optional[str] = Field(None, min_length=1, max_length=500)
    azure_tenant_id: Optional[str] = Field(None, min_length=1, max_length=500)
    from_name: str = Field(..., min_length=1, max_length=255)


class EmailAccountUpdate(BaseModel):
    """Schema para actualizar una cuenta de correo"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    provider_type: Optional[EmailProviderType] = None
    # Campos SMTP
    smtp_host: Optional[str] = Field(None, min_length=1, max_length=255)
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_user: Optional[str] = Field(None, min_length=1, max_length=255)
    smtp_password: Optional[str] = Field(None, min_length=1, max_length=500)
    # Campos Azure
    azure_endpoint: Optional[str] = Field(None, min_length=1, max_length=500)
    azure_client_id: Optional[str] = Field(None, min_length=1, max_length=500)
    azure_client_secret: Optional[str] = Field(None, min_length=1, max_length=500)
    azure_tenant_id: Optional[str] = Field(None, min_length=1, max_length=500)
    from_name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[EmailAccountStatus] = None


class EmailAccountResponse(BaseModel):
    """Schema para respuesta de cuenta de correo"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    provider_type: EmailProviderType
    smtp_host: Optional[str]
    smtp_port: Optional[int]
    azure_endpoint: Optional[str]
    from_name: str
    status: EmailAccountStatus
    created_at: datetime
    updated_at: datetime


# ==================== Email Template Schemas ====================

class EmailTemplateCreate(BaseModel):
    """Schema para crear una nueva plantilla de correo"""
    account_id: int
    name: str = Field(..., min_length=1, max_length=255)
    template_type: TemplateType
    subject: str = Field(..., min_length=1, max_length=500)
    html_content: str = Field(..., min_length=1)
    text_content: Optional[str] = None
    variables: Optional[str] = None

    @field_validator("subject")
    @classmethod
    def sanitize_subject(cls, v: str) -> str:
        # Evita header injection
        v = re.sub(r"[\r\n]+", " ", v)
        return escape(v.strip())
    
    @field_validator("html_content")
    @classmethod
    def sanitize_html(cls, v: str) -> str:
        return bleach.clean(
            v,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            strip=True
        )


class EmailTemplateUpdate(BaseModel):
    """Schema para actualizar una plantilla de correo"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    template_type: Optional[TemplateType] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    variables: Optional[str] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(BaseModel):
    """Schema para respuesta de plantilla de correo"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    name: str
    template_type: TemplateType
    subject: str
    html_content: str
    text_content: Optional[str]
    variables: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ==================== Email Sending Schemas ====================

class EmailAttachmentCreate(BaseModel):
    """Schema para adjuntos de correo"""
    filename: str = Field(..., min_length=1, max_length=500)
    content: str  # Base64 encoded content
    mime_type: str = Field(..., min_length=1, max_length=100)


class SendEmailRequest(BaseModel):
    """Schema para solicitud de envío de correo"""
    account_id: int
    template_id: Optional[int] = None
    to: List[EmailStr]
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    variables: Optional[dict] = None
    attachments: Optional[List[EmailAttachmentCreate]] = None

    @field_validator("to", "cc", "bcc", mode="before")
    @classmethod
    def normalize_emails(cls, v):
        if not v:
            return v
        normalized = []
        for email in v:
            _, addr = parseaddr(str(email))
            normalized.append(addr.lower().strip())
        return list(set(normalized))


class SentEmailResponse(BaseModel):
    """Schema para respuesta de correo enviado"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    template_id: Optional[int]
    to_email: str
    cc: Optional[str]
    bcc: Optional[str]
    subject: str
    status: EmailStatus
    error_message: Optional[str]
    retry_count: int
    sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SendEmailResponse(BaseModel):
    """Schema para respuesta de envío de correo"""
    message: str
    email_id: int
    status: EmailStatus


# ==================== Utility Schemas ====================

class PaginatedResponse(BaseModel):
    """Schema para respuestas paginadas"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: Any = Field(..., description="Lista de elementos")
    total: int = Field(..., description="Total de elementos en la BD")
    page: int = Field(..., description="Página actual")
    per_page: int = Field(..., description="Elementos por página")
    total_pages: int = Field(..., description="Total de páginas")


class HealthCheck(BaseModel):
    """Schema para verificación de salud de la API"""
    status: str
    version: str
    database: str
    redis: str
