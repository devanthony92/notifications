CREATE TYPE email_provider_type AS ENUM ('SMTP', 'AZURE');
CREATE TYPE email_account_status AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED');
CREATE TYPE email_status AS ENUM ('PENDING', 'SENT', 'FAILED', 'QUEUED');
CREATE TYPE email_template_type AS ENUM ('REGISTRATION_CONFIRMATION', 'PASSWORD_RESET', 'GENERAL');


-- Volcando estructura para tabla public.email_accounts
CREATE TABLE IF NOT EXISTS email_accounts (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    provider_type email_provider_type NOT NULL,

    smtp_host VARCHAR(255),
    smtp_port INTEGER,
    smtp_user VARCHAR(255),
    smtp_password TEXT,

    azure_endpoint TEXT,
    azure_client_id TEXT,
    azure_client_secret TEXT,
    azure_tenant_id TEXT,

    from_name VARCHAR(255) NOT NULL,
    status email_account_status DEFAULT NULL,

    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX ix_email_accounts_id ON email_accounts (id);


-- Volcando estructura para tabla public.email_templates
CREATE TABLE email_templates (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id INTEGER NOT NULL,    
    name VARCHAR(255) NOT NULL,
    template_type email_template_type NOT NULL,
    subject VARCHAR(500) NOT NULL,
    html_content TEXT NOT NULL,
    text_content TEXT,
    variables TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),

    CONSTRAINT fk_email_templates_account
        FOREIGN KEY (account_id)
        REFERENCES email_accounts(id)
);

CREATE INDEX ix_email_templates_account_id
    ON email_templates (account_id);

CREATE INDEX ix_email_templates_name
    ON email_templates (name);



-- Volcando estructura para tabla public.sent_emails
CREATE TABLE sent_emails (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id INTEGER NOT NULL,
    template_id INTEGER,

    to_email VARCHAR(255) NOT NULL,
    cc TEXT,
    bcc TEXT,
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,

    status email_status,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),

    CONSTRAINT fk_sent_emails_account
        FOREIGN KEY (account_id)
        REFERENCES email_accounts(id),

    CONSTRAINT fk_sent_emails_template
        FOREIGN KEY (template_id)
        REFERENCES email_templates(id)
);



-- Volcando estructura para tabla public.email_attachments
CREATE TABLE email_attachments (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sent_email_id INTEGER NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_content BYTEA NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT now(),

    CONSTRAINT fk_email_attachments_sent_email
        FOREIGN KEY (sent_email_id)
        REFERENCES sent_emails(id)
        ON DELETE CASCADE
);


CREATE INDEX ix_email_attachments_sent_email_id
    ON email_attachments (sent_email_id);


-- Insert default email account

INSERT INTO email_accounts (
    name,
    email,
    provider_type,
    smtp_host,
    smtp_port,
    smtp_user,
    smtp_password,
    from_name,
    status
)
VALUES (
    'User',
    'user@example.com',
    'SMTP',
    'smtp.gmail.com',
    465,
    'user@example.com',
    'ExamplePassword123',
    'Notification service',
    'ACTIVE'
)
RETURNING id;

INSERT INTO email_templates (
    account_id,
    name,
    template_type,
    subject,
    html_content,
    is_active
)
VALUES (
    1, -- el id devuelto arriba
    'Restaurar contraseña',
    'PASSWORD_RESET',
    'Restaurar contraseña',
    '<!DOCTYPE html>
<html lang="es">
	<head>
		<meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width, initial-scale=1.0" />
		<title>Recuperar Contraseña</title>
		<style>
			* {
				margin: 0;
				padding: 0;
				box-sizing: border-box;
			}

			body {
				font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
				background-color: #f3f4f6;
				color: #333;
			}

			.container {
				max-width: 600px;
				margin: 0 auto;
				background-color: #ffffff;
				border-radius: 8px;
				overflow: hidden;
				box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
			}

			.header {
				background: linear-gradient(135deg, #2d5016 0%, #7fd700 100%);
				padding: 40px 20px;
				text-align: center;
				color: #f3f4f6;
			}

			.header h1 {
				font-size: 28px;
				margin-bottom: 10px;
				font-weight: 700;
			}

			.header p {
				font-size: 14px;
				opacity: 0.9;
			}

			.content {
				padding: 40px 30px;
			}

			.greeting {
				font-size: 18px;
				color: #2d5016;
				margin-bottom: 20px;
				font-weight: 600;
			}

			.message {
				font-size: 14px;
				line-height: 1.8;
				color: #555;
				margin-bottom: 30px;
			}

			.warning-box {
				background-color: #fef3c7;
				border-left: 4px solid #f59e0b;
				padding: 20px;
				margin: 30px 0;
				border-radius: 4px;
			}

			.warning-box p {
				font-size: 13px;
				color: #92400e;
				margin-bottom: 8px;
			}

			.warning-box strong {
				color: #92400e;
			}

			.cta-button {
				display: inline-block;
				background-color: #7fd700;
				color: #2d5016;
				padding: 14px 40px;
				text-decoration: none;
				border-radius: 4px;
				font-weight: 600;
				font-size: 14px;
				margin: 20px 0;
				transition: background-color 0.3s ease;
			}

			.cta-button:hover {
				background-color: #6fcc00;
			}

			.code-box {
				background-color: #f3f4f6;
				padding: 15px;
				border-radius: 4px;
				text-align: center;
				margin: 20px 0;
				font-family: "Courier New", monospace;
				font-size: 16px;
				font-weight: 600;
				color: #2d5016;
				letter-spacing: 2px;
			}

			.footer {
				background-color: #f9fafb;
				padding: 30px;
				text-align: center;
				border-top: 1px solid #e5e7eb;
				font-size: 12px;
				color: #6b7280;
			}

			.footer p {
				margin-bottom: 10px;
			}

			.social-links {
				margin-top: 15px;
			}

			.social-links a {
				display: inline-block;
				margin: 0 8px;
				color: #2d5016;
				text-decoration: none;
				font-size: 12px;
			}

			.divider {
				height: 1px;
				background-color: #e5e7eb;
				margin: 20px 0;
			}

			.highlight {
				color: #7fd700;
				font-weight: 600;
			}

			.steps {
				background-color: #f0fdf4;
				padding: 20px;
				border-radius: 4px;
				margin: 20px 0;
			}

			.steps ol {
				margin-left: 20px;
				font-size: 13px;
				line-height: 1.8;
				color: #2d5016;
			}

			.steps li {
				margin-bottom: 10px;
			}
		</style>
	</head>
	<body>
		<div class="container">
			<!-- Header -->
			<div class="header">
				<h1>🔐 Recuperar Contraseña</h1>
				<p>Solicitud de restablecimiento de contraseña</p>
			</div>
			<!-- Content -->
			<div class="content">
				<p class="greeting">¡Hola {{ user_name }}!</p>

				<p class="message">
					Hemos recibido una solicitud para restablecer la contraseña de tu
					cuenta. Si no fuiste tú quien realizó esta solicitud, ignora este
					correo y tu contraseña permanecerá sin cambios.
				</p>

				<div class="warning-box">
					<p><strong>⚠️ Importante:</strong></p>
					<p>
						Este enlace de recuperación es válido solo por
						<span class="highlight">{{ expiration_time }}</span>. Después de
						este tiempo, deberás solicitar un nuevo restablecimiento.
					</p>
				</div>

				<p class="message">
					Para restablecer tu contraseña, haz clic en el siguiente botón:
				</p>

				<div style="text-align: center; margin: 30px 0">
					<a href="{{ reset_link }}" class="cta-button"
						>Restablecer Contraseña</a
					>
				</div>

				<p class="message">
					Si el botón anterior no funciona, copia y pega el siguiente enlace en
					tu navegador:
				</p>

				<p
					style="
						font-size: 12px;
						word-break: break-all;
						background-color: #f3f4f6;
						padding: 10px;
						border-radius: 4px;
						color: #555;
					"
				>
					{{ reset_link }}
				</p>

				<div class="divider"></div>

				<p class="message">
					También puedes usar el siguiente código de recuperación:
				</p>

				<div class="code-box">{{ recovery_code }}</div>

				<div class="steps">
					<p style="font-weight: 600; margin-bottom: 10px; color: #2d5016">
						Pasos a seguir:
					</p>
					<ol>
						<li>
							Haz clic en el botón "Restablecer Contraseña" o copia el enlace en
							tu navegador
						</li>
						<li>Ingresa una nueva contraseña segura</li>
						<li>Confirma tu nueva contraseña</li>
						<li>¡Listo! Ya podrás acceder con tu nueva contraseña</li>
					</ol>
				</div>

				<div class="divider"></div>

				<p class="message" style="font-size: 13px; color: #6b7280">
					Si no solicitaste este restablecimiento de contraseña, por favor
					<a
						href="{{ support_link }}"
						style="color: #7fd700; text-decoration: none; font-weight: 600"
						>contacta a nuestro equipo de soporte</a
					>
					de inmediato.
				</p>
			</div>

			<!-- Footer -->
			<div class="footer">
				<p>© 2025 Email Notification Service. Todos los derechos reservados.</p>
				<p>
					Este es un correo automático, por favor no respondas a este mensaje.
				</p>
				<div class="social-links">
					<a href="#">Política de Privacidad</a> |
					<a href="#">Términos de Servicio</a> |
					<a href="#">Contacto</a>
				</div>
			</div>
		</div>
	</body>
</html>',
    TRUE
);