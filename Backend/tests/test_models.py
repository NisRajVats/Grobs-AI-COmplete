"""
Comprehensive tests for database models - ensuring data integrity, relationships, and constraints.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from app.models import (
    User, Resume, ResumeVersion, ResumeAnalysis, ResumeContent, ResumeEmbedding,
    Skill, Education, Experience, Project, Job, JobSkill, JobEmbedding, JobApplication,
    SavedJob, InterviewSession, InterviewQuestion, InterviewAnswer, Notification,
    SubscriptionPlan, UserSubscription, UserSettings, CalendarEvent
)
from app.database.session import Base
from app.core.security import get_password_hash


class TestUserModel:
    """Tests for User model."""
    
    def test_user_creation(self, db_session):
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_unique_email(self, db_session):
        # Create first user
        user1 = User(
            email="unique@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="User 1"
        )
        db_session.add(user1)
        db_session.commit()
        
        # Try to create user with same email
        user2 = User(
            email="unique@example.com",
            hashed_password=get_password_hash("password456"),
            full_name="User 2"
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_user_relationships(self, db_session):
        user = User(
            email="relationships@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        # Test that user has relationships initialized
        assert user.resumes is not None
        assert user.applications is not None
        assert user.saved_jobs is not None
        assert user.interview_sessions is not None
        assert user.notifications is not None


class TestResumeModel:
    """Tests for Resume model."""
    
    def test_resume_creation(self, db_session):
        user = User(
            email="resumeuser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Resume User"
        )
        db_session.add(user)
        db_session.commit()
        
        resume = Resume(
            user_id=user.id,
            full_name="John Doe",
            email="john@example.com",
            title="Software Engineer Resume",
            summary="Experienced software engineer",
            target_role="Senior Software Engineer"
        )
        db_session.add(resume)
        db_session.commit()
        
        assert resume.id is not None
        assert resume.user_id == user.id
        assert resume.full_name == "John Doe"
        assert resume.email == "john@example.com"
        assert resume.title == "Software Engineer Resume"
        assert resume.summary == "Experienced software engineer"
        assert resume.target_role == "Senior Software Engineer"
        assert resume.created_at is not None
        assert resume.updated_at is not None
    
    def test_resume_user_relationship(self, db_session):
        user = User(
            email="reluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        resume = Resume(
            user_id=user.id,
            full_name="Jane Doe",
            email="jane@example.com",
            title="Test Resume"
        )
        db_session.add(resume)
        db_session.commit()
        
        # Test relationship
        assert resume.user == user
        assert resume in user.resumes
    
    def test_resume_versions_relationship(self, db_session):
        user = User(
            email="versionuser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Version User"
        )
        db_session.add(user)
        db_session.commit()
        
        resume = Resume(
            user_id=user.id,
            full_name="Test User",
            email="test@example.com",
            title="Test Resume"
        )
        db_session.add(resume)
        db_session.commit()
        
        # Create version
        version = ResumeVersion(
            resume_id=resume.id,
            version_number=1,
            changes="Initial version"
        )
        db_session.add(version)
        db_session.commit()
        
        assert version.resume == resume
        assert version in resume.versions
    
    def test_resume_skills_relationship(self, db_session):
        user = User(
            email="skilluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Skill User"
        )
        db_session.add(user)
        db_session.commit()
        
        resume = Resume(
            user_id=user.id,
            full_name="Test User",
            email="test@example.com",
            title="Test Resume"
        )
        db_session.add(resume)
        db_session.commit()
        
        # Create skills
        skill1 = Skill(name="Python", category="Technical")
        skill2 = Skill(name="JavaScript", category="Technical")
        db_session.add_all([skill1, skill2])
        db_session.commit()
        
        # Associate skills with resume
        resume.skills = [skill1, skill2]
        db_session.commit()
        
        assert skill1 in resume.skills
        assert skill2 in resume.skills
        assert resume in skill1.resumes
        assert resume in skill2.resumes


class TestSkillModel:
    """Tests for Skill model."""
    
    def test_skill_creation(self, db_session):
        skill = Skill(name="Python", category="Technical")
        db_session.add(skill)
        db_session.commit()
        
        assert skill.id is not None
        assert skill.name == "Python"
        assert skill.category == "Technical"
        assert skill.created_at is not None
    
    def test_skill_unique_name(self, db_session):
        skill1 = Skill(name="Python", category="Technical")
        db_session.add(skill1)
        db_session.commit()
        
        skill2 = Skill(name="Python", category="Programming")
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.add(skill2)
            db_session.commit()


class TestEducationModel:
    """Tests for Education model."""
    
    def test_education_creation(self, db_session):
        user = User(
            email="eduuser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Education User"
        )
        db_session.add(user)
        db_session.commit()
        
        resume = Resume(
            user_id=user.id,
            full_name="Test User",
            email="test@example.com",
            title="Test Resume"
        )
        db_session.add(resume)
        db_session.commit()
        
        education = Education(
            resume_id=resume.id,
            school="Tech University",
            degree="B.S.",
            major="Computer Science",
            start_date="2010",
            end_date="2014",
            gpa="3.8"
        )
        db_session.add(education)
        db_session.commit()
        
        assert education.id is not None
        assert education.resume_id == resume.id
        assert education.school == "Tech University"
        assert education.degree == "B.S."
        assert education.major == "Computer Science"
        assert education.start_date == "2010"
        assert education.end_date == "2014"
        assert education.gpa == "3.8"
    
    def test_education_resume_relationship(self, db_session):
        user = User(
            email="edureluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Education Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        resume = Resume(
            user_id=user.id,
            full_name="Test User",
            email="test@example.com",
            title="Test Resume"
        )
        db_session.add(resume)
        db_session.commit()
        
        education = Education(
            resume_id=resume.id,
            school="Tech University",
            degree="B.S.",
            major="Computer Science"
        )
        db_session.add(education)
        db_session.commit()
        
        assert education.resume == resume
        assert education in resume.education


class TestExperienceModel:
    """Tests for Experience model."""
    
    def test_experience_creation(self, db_session):
        user = User(
            email="expuser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Experience User"
        )
        db_session.add(user)
        db_session.commit()
        
        resume = Resume(
            user_id=user.id,
            full_name="Test User",
            email="test@example.com",
            title="Test Resume"
        )
        db_session.add(resume)
        db_session.commit()
        
        experience = Experience(
            resume_id=resume.id,
            company="TechCorp",
            role="Software Engineer",
            start_date="2015",
            end_date="2020",
            description="Developed web applications"
        )
        db_session.add(experience)
        db_session.commit()
        
        assert experience.id is not None
        assert experience.resume_id == resume.id
        assert experience.company == "TechCorp"
        assert experience.role == "Software Engineer"
        assert experience.start_date == "2015"
        assert experience.end_date == "2020"
        assert experience.description == "Developed web applications"
    
    def test_experience_resume_relationship(self, db_session):
        user = User(
            email="expreluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Experience Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        resume = Resume(
            user_id=user.id,
            full_name="Test User",
            email="test@example.com",
            title="Test Resume"
        )
        db_session.add(resume)
        db_session.commit()
        
        experience = Experience(
            resume_id=resume.id,
            company="TechCorp",
            role="Software Engineer"
        )
        db_session.add(experience)
        db_session.commit()
        
        assert experience.resume == resume
        assert experience in resume.experience


class TestProjectModel:
    """Tests for Project model."""
    
    def test_project_creation(self, db_session):
        user = User(
            email="projuser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Project User"
        )
        db_session.add(user)
        db_session.commit()
        
        resume = Resume(
            user_id=user.id,
            full_name="Test User",
            email="test@example.com",
            title="Test Resume"
        )
        db_session.add(resume)
        db_session.commit()
        
        project = Project(
            resume_id=resume.id,
            project_name="E-Commerce Platform",
            description="Built a full-stack e-commerce solution",
            technologies="React, Node.js, MongoDB"
        )
        db_session.add(project)
        db_session.commit()
        
        assert project.id is not None
        assert project.resume_id == resume.id
        assert project.project_name == "E-Commerce Platform"
        assert project.description == "Built a full-stack e-commerce solution"
        assert project.technologies == "React, Node.js, MongoDB"
    
    def test_project_resume_relationship(self, db_session):
        user = User(
            email="projreluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Project Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        resume = Resume(
            user_id=user.id,
            full_name="Test User",
            email="test@example.com",
            title="Test Resume"
        )
        db_session.add(resume)
        db_session.commit()
        
        project = Project(
            resume_id=resume.id,
            project_name="Test Project",
            description="Test project description"
        )
        db_session.add(project)
        db_session.commit()
        
        assert project.resume == resume
        assert project in resume.projects


class TestJobModel:
    """Tests for Job model."""
    
    def test_job_creation(self, db_session):
        job = Job(
            title="Software Engineer",
            company="TechCorp",
            location="San Francisco, CA",
            description="Looking for experienced software engineer",
            requirements="5+ years experience in Python",
            salary_min=80000,
            salary_max=120000,
            job_type="Full-time",
            remote=True,
            posted_date=datetime.now()
        )
        db_session.add(job)
        db_session.commit()
        
        assert job.id is not None
        assert job.title == "Software Engineer"
        assert job.company == "TechCorp"
        assert job.location == "San Francisco, CA"
        assert job.description == "Looking for experienced software engineer"
        assert job.requirements == "5+ years experience in Python"
        assert job.salary_min == 80000
        assert job.salary_max == 120000
        assert job.job_type == "Full-time"
        assert job.remote is True
        assert job.posted_date is not None
    
    def test_job_skills_relationship(self, db_session):
        job = Job(
            title="Software Engineer",
            company="TechCorp",
            location="San Francisco, CA",
            description="Looking for experienced software engineer"
        )
        db_session.add(job)
        db_session.commit()
        
        skill1 = Skill(name="Python", category="Technical")
        skill2 = Skill(name="Django", category="Technical")
        db_session.add_all([skill1, skill2])
        db_session.commit()
        
        # Create job skills
        job_skill1 = JobSkill(job_id=job.id, skill_id=skill1.id)
        job_skill2 = JobSkill(job_id=job.id, skill_id=skill2.id)
        db_session.add_all([job_skill1, job_skill2])
        db_session.commit()
        
        assert skill1 in job.skills
        assert skill2 in job.skills
        assert job in skill1.jobs
        assert job in skill2.jobs


class TestJobApplicationModel:
    """Tests for JobApplication model."""
    
    def test_job_application_creation(self, db_session):
        user = User(
            email="appuser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Application User"
        )
        db_session.add(user)
        db_session.commit()
        
        job = Job(
            title="Software Engineer",
            company="TechCorp",
            location="San Francisco, CA",
            description="Looking for experienced software engineer"
        )
        db_session.add(job)
        db_session.commit()
        
        application = JobApplication(
            user_id=user.id,
            job_id=job.id,
            job_title="Software Engineer",
            company="TechCorp",
            status="applied",
            notes="Applied through company website"
        )
        db_session.add(application)
        db_session.commit()
        
        assert application.id is not None
        assert application.user_id == user.id
        assert application.job_id == job.id
        assert application.job_title == "Software Engineer"
        assert application.company == "TechCorp"
        assert application.status == "applied"
        assert application.notes == "Applied through company website"
        assert application.created_at is not None
    
    def test_job_application_user_relationship(self, db_session):
        user = User(
            email="appreluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Application Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        job = Job(
            title="Software Engineer",
            company="TechCorp",
            location="San Francisco, CA"
        )
        db_session.add(job)
        db_session.commit()
        
        application = JobApplication(
            user_id=user.id,
            job_id=job.id,
            job_title="Software Engineer",
            company="TechCorp",
            status="applied"
        )
        db_session.add(application)
        db_session.commit()
        
        assert application.user == user
        assert application in user.applications
    
    def test_job_application_job_relationship(self, db_session):
        user = User(
            email="appjobreluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Application Job Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        job = Job(
            title="Software Engineer",
            company="TechCorp",
            location="San Francisco, CA"
        )
        db_session.add(job)
        db_session.commit()
        
        application = JobApplication(
            user_id=user.id,
            job_id=job.id,
            job_title="Software Engineer",
            company="TechCorp",
            status="applied"
        )
        db_session.add(application)
        db_session.commit()
        
        assert application.job == job
        assert application in job.applications


class TestInterviewSessionModel:
    """Tests for InterviewSession model."""
    
    def test_interview_session_creation(self, db_session):
        user = User(
            email="intuser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Interview User"
        )
        db_session.add(user)
        db_session.commit()
        
        session = InterviewSession(
            user_id=user.id,
            job_title="Software Engineer",
            company="TechCorp",
            interview_type="technical",
            difficulty="medium",
            status="scheduled"
        )
        db_session.add(session)
        db_session.commit()
        
        assert session.id is not None
        assert session.user_id == user.id
        assert session.job_title == "Software Engineer"
        assert session.company == "TechCorp"
        assert session.interview_type == "technical"
        assert session.difficulty == "medium"
        assert session.status == "scheduled"
        assert session.created_at is not None
    
    def test_interview_session_user_relationship(self, db_session):
        user = User(
            email="intreluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Interview Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        session = InterviewSession(
            user_id=user.id,
            job_title="Software Engineer",
            company="TechCorp",
            interview_type="technical"
        )
        db_session.add(session)
        db_session.commit()
        
        assert session.user == user
        assert session in user.interview_sessions


class TestNotificationModel:
    """Tests for Notification model."""
    
    def test_notification_creation(self, db_session):
        user = User(
            email="notifuser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Notification User"
        )
        db_session.add(user)
        db_session.commit()
        
        notification = Notification(
            user_id=user.id,
            title="Application Update",
            message="Your application has been viewed",
            notification_type="application",
            is_read=False
        )
        db_session.add(notification)
        db_session.commit()
        
        assert notification.id is not None
        assert notification.user_id == user.id
        assert notification.title == "Application Update"
        assert notification.message == "Your application has been viewed"
        assert notification.notification_type == "application"
        assert notification.is_read is False
        assert notification.created_at is not None
    
    def test_notification_user_relationship(self, db_session):
        user = User(
            email="notifreluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Notification Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        notification = Notification(
            user_id=user.id,
            title="Test Notification",
            message="Test message"
        )
        db_session.add(notification)
        db_session.commit()
        
        assert notification.user == user
        assert notification in user.notifications


class TestSubscriptionPlanModel:
    """Tests for SubscriptionPlan model."""
    
    def test_subscription_plan_creation(self, db_session):
        plan = SubscriptionPlan(
            name="Premium",
            price=29.99,
            duration_months=1,
            features=["ATS Analysis", "Job Matching", "Interview Prep"],
            is_active=True
        )
        db_session.add(plan)
        db_session.commit()
        
        assert plan.id is not None
        assert plan.name == "Premium"
        assert plan.price == 29.99
        assert plan.duration_months == 1
        assert plan.features == ["ATS Analysis", "Job Matching", "Interview Prep"]
        assert plan.is_active is True
    
    def test_subscription_plan_unique_name(self, db_session):
        plan1 = SubscriptionPlan(
            name="Premium",
            price=29.99,
            duration_months=1
        )
        db_session.add(plan1)
        db_session.commit()
        
        plan2 = SubscriptionPlan(
            name="Premium",
            price=39.99,
            duration_months=1
        )
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.add(plan2)
            db_session.commit()


class TestUserSubscriptionModel:
    """Tests for UserSubscription model."""
    
    def test_user_subscription_creation(self, db_session):
        user = User(
            email="subuser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Subscription User"
        )
        db_session.add(user)
        db_session.commit()
        
        plan = SubscriptionPlan(
            name="Premium",
            price=29.99,
            duration_months=1
        )
        db_session.add(plan)
        db_session.commit()
        
        subscription = UserSubscription(
            user_id=user.id,
            plan_id=plan.id,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            is_active=True
        )
        db_session.add(subscription)
        db_session.commit()
        
        assert subscription.id is not None
        assert subscription.user_id == user.id
        assert subscription.plan_id == plan.id
        assert subscription.is_active is True
        assert subscription.start_date is not None
        assert subscription.end_date is not None
    
    def test_user_subscription_user_relationship(self, db_session):
        user = User(
            email="subreluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Subscription Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        plan = SubscriptionPlan(
            name="Premium",
            price=29.99,
            duration_months=1
        )
        db_session.add(plan)
        db_session.commit()
        
        subscription = UserSubscription(
            user_id=user.id,
            plan_id=plan.id,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(subscription)
        db_session.commit()
        
        assert subscription.user == user
        assert subscription in user.subscriptions
    
    def test_user_subscription_plan_relationship(self, db_session):
        user = User(
            email="subplanreluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Subscription Plan Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        plan = SubscriptionPlan(
            name="Premium",
            price=29.99,
            duration_months=1
        )
        db_session.add(plan)
        db_session.commit()
        
        subscription = UserSubscription(
            user_id=user.id,
            plan_id=plan.id,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(subscription)
        db_session.commit()
        
        assert subscription.plan == plan
        assert subscription in plan.user_subscriptions


class TestUserSettingsModel:
    """Tests for UserSettings model."""
    
    def test_user_settings_creation(self, db_session):
        user = User(
            email="settingsuser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Settings User"
        )
        db_session.add(user)
        db_session.commit()
        
        settings = UserSettings(
            user_id=user.id,
            email_notifications=True,
            push_notifications=False,
            theme="dark",
            language="en"
        )
        db_session.add(settings)
        db_session.commit()
        
        assert settings.id is not None
        assert settings.user_id == user.id
        assert settings.email_notifications is True
        assert settings.push_notifications is False
        assert settings.theme == "dark"
        assert settings.language == "en"
    
    def test_user_settings_user_relationship(self, db_session):
        user = User(
            email="settingsreluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Settings Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        settings = UserSettings(
            user_id=user.id,
            email_notifications=True,
            push_notifications=False
        )
        db_session.add(settings)
        db_session.commit()
        
        assert settings.user == user
        assert settings == user.settings


class TestCalendarEventModel:
    """Tests for CalendarEvent model."""
    
    def test_calendar_event_creation(self, db_session):
        user = User(
            email="caluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Calendar User"
        )
        db_session.add(user)
        db_session.commit()
        
        event = CalendarEvent(
            user_id=user.id,
            title="Interview with TechCorp",
            description="Technical interview for Software Engineer position",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_type="interview"
        )
        db_session.add(event)
        db_session.commit()
        
        assert event.id is not None
        assert event.user_id == user.id
        assert event.title == "Interview with TechCorp"
        assert event.description == "Technical interview for Software Engineer position"
        assert event.start_time is not None
        assert event.end_time is not None
        assert event.event_type == "interview"
    
    def test_calendar_event_user_relationship(self, db_session):
        user = User(
            email="calreluser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Calendar Relationship User"
        )
        db_session.add(user)
        db_session.commit()
        
        event = CalendarEvent(
            user_id=user.id,
            title="Test Event",
            description="Test event description",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1)
        )
        db_session.add(event)
        db_session.commit()
        
        assert event.user == user
        assert event in user.calendar_events