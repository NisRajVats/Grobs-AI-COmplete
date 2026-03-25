"""
Models package - exports all models for easy importing.
"""
from app.models.user import User, SubscriptionPlan, UserSubscription
from app.models.resume import Resume, ResumeVersion, ResumeAnalysis, ResumeContent, ResumeEmbedding
from app.models.jobs import Job, JobApplication, SavedJob, JobSkill, JobEmbedding
from app.models.education import Education
from app.models.experience import Experience
from app.models.projects import Project
from app.models.skills import Skill
from app.models.notification import Notification
from app.models.interview import InterviewSession, InterviewQuestion, InterviewAnswer

# Export all models
__all__ = [
    "User",
    "SubscriptionPlan", 
    "UserSubscription",
    "Resume",
    "ResumeVersion",
    "ResumeAnalysis",
    "ResumeContent",
    "ResumeEmbedding",
    "Job",
    "JobApplication",
    "SavedJob",
    "JobSkill",
    "JobEmbedding",
    "Education",
    "Experience",
    "Project",
    "Skill",
    "Notification",
    "InterviewSession",
    "InterviewQuestion",
    "InterviewAnswer",
]

