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
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict
    ) -> bool:
        """Send email using HTML template."""
        try:
            template_content = self._load_template(template_name)
            template = Template(template_content)
            html_content = template.render(**context)
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_resume_analysis_notification(
        self,
        user_email: str,
        resume_name: str,
        score: int
    ) -> bool:
        """Send resume analysis notification."""
        subject = f"Your resume analysis is ready! Score: {score}%"
        context = {
            'user_name': user_email.split('@')[0],
            'resume_name': resume_name,
            'score': score,
            'app_url': settings.APP_URL
        }
        return self.send_email(user_email, subject, 'resume_analysis', context)
    
    def send_job_match_notification(
        self,
        user_email: str,
        job_title: str,
        company: str,
        match_score: int
    ) -> bool:
        """Send job match notification."""
        subject = f"New job match found: {job_title} at {company}"
        context = {
            'user_name': user_email.split('@')[0],
            'job_title': job_title,
            'company': company,
            'match_score': match_score,
            'app_url': settings.APP_URL
        }
        return self.send_email(user_email, subject, 'job_match', context)
    
    def send_interview_reminder(
        self,
        user_email: str,
        job_title: str,
        company: str,
        interview_date: str,
        interview_time: str
    ) -> bool:
        """Send interview reminder."""
        subject = f"Interview reminder: {job_title} at {company}"
        context = {
            'user_name': user_email.split('@')[0],
            'job_title': job_title,
            'company': company,
            'interview_date': interview_date,
            'interview_time': interview_time,
            'app_url': settings.APP_URL
        }
        return self.send_email(user_email, subject, 'interview_reminder', context)
    
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
            """
        }
        return templates.get(template_name, "<html><body><p>{{ message }}</p></body></html>")

