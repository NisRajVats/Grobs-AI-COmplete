"""
Email Worker - Handles asynchronous email sending.

This worker processes email jobs from the queue.
"""
import logging
from typing import Dict, Any, Optional
from app.utils.email_service import send_email

logger = logging.getLogger(__name__)


def process_email(
    recipient_email: str,
    subject: str,
    template_name: str,
    template_data: Dict[str, Any],
    attachments: Optional[list] = None
) -> dict:
    """
    Send an email using the email service.
    
    Args:
        recipient_email: Email address of recipient
        subject: Email subject
        template_name: Name of email template
        template_data: Data for template rendering
        attachments: Optional list of file paths to attach
        
    Returns:
        Dictionary with email sending result
    """
    try:
        logger.info(f"[EmailWorker] Sending email to {recipient_email}")
        
        # Send email
        result = send_email(
            to_email=recipient_email,
            subject=subject,
            template_name=template_name,
            template_data=template_data,
            attachments=attachments
        )
        
        if result.get("success"):
            logger.info(f"[EmailWorker] Email sent successfully to {recipient_email}")
        else:
            logger.error(f"[EmailWorker] Failed to send email to {recipient_email}: {result.get('error')}")
            
        return result
            
    except Exception as e:
        logger.error(f"[EmailWorker] Error sending email to {recipient_email}: {str(e)}")
        return {"success": False, "error": str(e)}


# Alias for generic process call
process = process_email


def process_interview_reminder(
    recipient_email: str,
    user_name: str,
    job_title: str,
    company: str,
    interview_date: str,
    interview_time: str
) -> dict:
    """Send interview reminder email."""
    return process_email(
        recipient_email=recipient_email,
        subject=f"Interview Reminder: {job_title} at {company}",
        template_name="interview_reminder",
        template_data={
            "user_name": user_name,
            "job_title": job_title,
            "company": company,
            "interview_date": interview_date,
            "interview_time": interview_time
        }
    )


def process_job_match_notification(
    recipient_email: str,
    user_name: str,
    job_title: str,
    company: str,
    match_score: int
) -> dict:
    """Send job match notification email."""
    return process_email(
        recipient_email=recipient_email,
        subject=f"New Job Match: {job_title} at {company}",
        template_name="job_match",
        template_data={
            "user_name": user_name,
            "job_title": job_title,
            "company": company,
            "match_score": match_score
        }
    )


def process_resume_analysis_notification(
    recipient_email: str,
    user_name: str,
    resume_title: str,
    ats_score: int
) -> dict:
    """Send resume analysis completion notification."""
    return process_email(
        recipient_email=recipient_email,
        subject=f"Resume Analysis Complete: {resume_title}",
        template_name="resume_analysis",
        template_data={
            "user_name": user_name,
            "resume_title": resume_title,
            "ats_score": ats_score
        }
    )


from app.workers.celery_app import celery

# Celery task wrapper
if celery:
    @celery.task(name='email_worker.process')
    def celery_process_email(
        recipient_email: str,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        attachments: Optional[list] = None
    ):
        return process_email(recipient_email, subject, template_name, template_data, attachments)
    
    @celery.task(name='email_worker.interview_reminder')
    def celery_process_interview_reminder(
        recipient_email: str,
        user_name: str,
        job_title: str,
        company: str,
        interview_date: str,
        interview_time: str
    ):
        return process_interview_reminder(recipient_email, user_name, job_title, company, interview_date, interview_time)
    
    @celery.task(name='email_worker.job_match')
    def celery_process_job_match_notification(
        recipient_email: str,
        user_name: str,
        job_title: str,
        company: str,
        match_score: int
    ):
        return process_job_match_notification(recipient_email, user_name, job_title, company, match_score)
    
    @celery.task(name='email_worker.resume_analysis')
    def celery_process_resume_analysis_notification(
        recipient_email: str,
        user_name: str,
        resume_title: str,
        ats_score: int
    ):
        return process_resume_analysis_notification(recipient_email, user_name, resume_title, ats_score)
