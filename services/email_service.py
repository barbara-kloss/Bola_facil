import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

class EmailService:
    @staticmethod
    def send_email(to_email, subject, html_content):
        """
        Envia um e-mail. Requer configuração de SMTP no config.py / variáveis de ambiente.
        """
        smtp_server = current_app.config.get("SMTP_SERVER")
        smtp_port = current_app.config.get("SMTP_PORT", 587)
        smtp_username = current_app.config.get("SMTP_USERNAME")
        smtp_password = current_app.config.get("SMTP_PASSWORD")
        smtp_sender = current_app.config.get("SMTP_SENDER", "noreply@bolaofacil.com")
        
        if not smtp_server or not smtp_username or not smtp_password:
            # Em modo de desenvolvimento, se não houver SMTP configurado, apenas logamos
            current_app.logger.warning(f"[EMAIL SIMULADO para {to_email}] Assunto: {subject}")
            current_app.logger.info(f"Conteúdo:\n{html_content}")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_sender
            msg["To"] = to_email
            
            part = MIMEText(html_content, "html")
            msg.attach(part)
            
            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(smtp_sender, to_email, msg.as_string())
            
            current_app.logger.info(f"E-mail enviado com sucesso para {to_email}")
            return True
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar e-mail para {to_email}: {e}")
            return False

    @staticmethod
    def send_group_invite(to_email, inviter_name, group_name, register_url):
        subject = f"Convite para participar do grupo {group_name} no BolãoFácil!"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <h2>Olá!</h2>
            <p>Você foi convidado por <strong>{inviter_name}</strong> para participar do grupo <strong>{group_name}</strong> no BolãoFácil.</p>
            <p>Para aceitar o convite e começar a dar seus palpites, basta criar sua conta clicando no link abaixo:</p>
            <a href="{register_url}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Criar Conta e Aceitar Convite</a>
            <p>Se você já tiver uma conta registrada com este e-mail ({to_email}), o convite será aceito automaticamente no seu próximo login.</p>
            <hr style="border: 0; border-top: 1px solid #ccc; margin-top: 20px;">
            <p style="font-size: 0.8em; color: #777;">Equipe BolãoFácil</p>
        </body>
        </html>
        """
        return EmailService.send_email(to_email, subject, html)
