"""
Email service for sending notifications.
"""
import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending notifications."""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_HOST or 'smtp.gmail.com'
        self.smtp_port = settings.SMTP_PORT or 587
        self.email_user = settings.SMTP_USER
        self.email_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL or "noreply@grobsai.com"
        self.from_name = settings.SMTP_FROM_NAME or "GrobsAI"
        
    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
        attachments: Optional[list] = None
    ) -> dict:
        """Send email using HTML template."""
        try:
            # Check if SMTP is configured
            if not self.email_user or not self.email_password:
                logger.warning(f"SMTP not configured. Mocking email to {to_email}")
                if settings.ENVIRONMENT == "development":
                    logger.info(f"MOCK EMAIL CONTENT: {context}")
                    return {"success": True, "message_id": "mock_id_dev", "mock": True}
                return {"success": False, "error": "SMTP not configured"}

            template_content = self._load_template(template_name)
            template = Template(template_content)
            
            # Add common context
            full_context = {
                **context,
                "app_url": settings.APP_URL,
                "app_name": settings.APP_NAME,
            }
            
            html_content = template.render(**full_context)
            
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Handle attachments
            if attachments:
                from email.mime.application import MIMEApplication
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                            msg.attach(part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {to_email}")
            return {"success": True, "message_id": msg.get("Message-ID")}
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {"success": False, "error": str(e)}
    
    def send_resume_analysis_notification(
        self,
        user_email: str,
        resume_name: str,
        score: int
    ) -> dict:
        """Send resume analysis notification."""
        subject = f"Your resume analysis is ready! Score: {score}%"
        context = {
            'user_name': user_email.split('@')[0],
            'resume_name': resume_name,
            'score': score
        }
        return self.send_email(user_email, subject, 'resume_analysis', context)
    
    def send_job_match_notification(
        self,
        user_email: str,
        job_title: str,
        company: str,
        match_score: int
    ) -> dict:
        """Send job match notification."""
        subject = f"New job match found: {job_title} at {company}"
        context = {
            'user_name': user_email.split('@')[0],
            'job_title': job_title,
            'company': company,
            'match_score': match_score
        }
        return self.send_email(user_email, subject, 'job_match', context)
    
    def send_interview_reminder(
        self,
        user_email: str,
        job_title: str,
        company: str,
        interview_date: str,
        interview_time: str
    ) -> dict:
        """Send interview reminder."""
        subject = f"Interview reminder: {job_title} at {company}"
        context = {
            'user_name': user_email.split('@')[0],
            'job_title': job_title,
            'company': company,
            'interview_date': interview_date,
            'interview_time': interview_time
        }
        return self.send_email(user_email, subject, 'interview_reminder', context)

    def send_welcome_email(self, user_email: str, user_name: str) -> dict:
        """Send welcome email to new users."""
        subject = f"Welcome to {settings.APP_NAME}!"
        context = {
            'user_name': user_name,
        }
        return self.send_email(user_email, subject, 'welcome', context)

    def _load_template(self, template_name: str) -> str:
        """Load HTML email template."""
        template_dir = os.path.join(
            os.path.dirname(__file__),
            '../../templates/emails'
        )
        template_file = os.path.join(template_dir, f'{template_name}.html')
        
        try:
            with open(template_file, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Template not found: {template_file}")
            return self._get_fallback_template(template_name)
    
    def _get_fallback_template(self, template_name: str) -> str:
        """Fallback template if file doesn't exist."""
        templates = {
            'resume_analysis': """
            <html><body>
                <h2>Resume Analysis Complete</h2>
                <p>Hello {{ user_name }},</p>
                <p>Your resume "{{ resume_name }}" has been analyzed.</p>
                <p>Score: {{ score }}%</p>
            </body></html>
            """,
            'job_match': """
            <html><body>
                <h2>Job Match Found</h2>
                <p>Hello {{ user_name }},</p>
                <p>New match: {{ job_title }} at {{ company }}</p>
                <p>Match Score: {{ match_score }}%</p>
            </body></html>
            """,
            'interview_reminder': """
            <html><body>
                <h2>Interview Reminder</h2>
                <p>Hello {{ user_name }},</p>
                <p>Interview: {{ job_title }} at {{ company }}</p>
                <p>Date: {{ interview_date }} at {{ interview_time }}</p>
            </body></html>
            """,
            'welcome': """
            <html><body>
                <h2>Welcome to {{ app_name }}!</h2>
                <p>Hello {{ user_name }},</p>
                <p>Thank you for joining us. We're excited to help you in your career journey.</p>
                <p><a href="{{ app_url }}">Get started now</a></p>
            </body></html>
            """,
            'password_reset': """
            <html><body>
                <h2>Password Reset Request</h2>
                <p>Hello {{ user_name }},</p>
                <p>We received a request to reset your password. Click the link below to set a new one:</p>
                <p><a href="{{ reset_link }}">Reset Password</a></p>
                <p>If you didn't request this, you can safely ignore this email.</p>
            </body></html>
            """
        }
        return templates.get(template_name, "<html><body><p>{{ message }}</p></body></html>")


# Convenience function for external use
def send_email(
    to_email: str,
    subject: str,
    template_name: str,
    template_data: dict,
    attachments: Optional[list] = None
) -> dict:
    """Helper function to send email without instantiating service."""
    service = EmailService()
    return service.send_email(
        to_email=to_email,
        subject=subject,
        template_name=template_name,
        context=template_data,
        attachments=attachments
    )

