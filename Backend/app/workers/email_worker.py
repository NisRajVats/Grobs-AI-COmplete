"""
Email Worker - Handles asynchronous email sending.

This worker processes email jobs from the queue.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

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
        
        # Import email service
        from app.utils.email_service import send_email
        
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
            return {
                "success": True,
                "message_id": result.get("message_id"),
                "recipient": recipient_email
            }
        else:
            logger.error(f"[EmailWorker] Failed to send email to {recipient_email}: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error")
            }
            
    except Exception as e:
        logger.error(f"[EmailWorker] Error sending email to {recipient_email}: {str(e)}")
        return {"success": False, "error": str(e)}


def process_interview_reminder(
    recipient_email: str,
    user_name: str,
    interview_date: str,
    company: str,
    position: str
) -> dict:
    """
    Send interview reminder email.
    
    Args:
        recipient_email: Recipient's email
        user_name: User's name
        interview_date: Interview date/time
        company: Company name
        position: Position title
        
    Returns:
        Result dictionary
    """
    return process_email(
        recipient_email=recipient_email,
        subject=f"Interview Reminder: {position} at {company}",
        template_name="interview_reminder",
        template_data={
            "user_name": user_name,
            "interview_date": interview_date,
            "company": company,
            "position": position
        }
    )


def process_job_match_notification(
    recipient_email: str,
    user_name: str,
    job_title: str,
    company: str,
    match_score: int
) -> dict:
    """
    Send job match notification email.
    
    Args:
        recipient_email: Recipient's email
        user_name: User's name
        job_title: Job title
        company: Company name
        match_score: Match percentage
        
    Returns:
        Result dictionary
    """
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
    """
    Send resume analysis completion notification.
    
    Args:
        recipient_email: Recipient's email
        user_name: User's name
        resume_title: Resume title
        ats_score: ATS score
        
    Returns:
        Result dictionary
    """
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


# Celery task wrapper (if Celery is available)
try:
    from celery import Celery
    celery_app = Celery('email_worker')
    
    @celery_app.task(name='email_worker.send')
    def celery_process_email(
        recipient_email: str,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        attachments: Optional[list] = None
    ):
        return process_email(recipient_email, subject, template_name, template_data, attachments)
    
    @celery_app.task(name='email_worker.interview_reminder')
    def celery_process_interview_reminder(
        recipient_email: str,
        user_name: str,
        interview_date: str,
        company: str,
        position: str
    ):
        return process_interview_reminder(recipient_email, user_name, interview_date, company, position)
    
    @celery_app.task(name='email_worker.job_match')
    def celery_process_job_match_notification(
        recipient_email: str,
        user_name: str,
        job_title: str,
        company: str,
        match_score: int
    ):
        return process_job_match_notification(recipient_email, user_name, job_title, company, match_score)
    
    @celery_app.task(name='email_worker.resume_analysis')
    def celery_process_resume_analysis_notification(
        recipient_email: str,
        user_name: str,
        resume_title: str,
        ats_score: int
    ):
        return process_resume_analysis_notification(recipient_email, user_name, resume_title, ats_score)
        
except ImportError:
    pass

