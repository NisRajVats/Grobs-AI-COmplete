#!/usr/bin/env python3
"""
GrobsAI Backend Setup Script
Run this once to initialize the database with sample data.
"""
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import engine, Base, SessionLocal
import app.models  # Import all models

def setup():
    print("🔧 Setting up GrobsAI Backend...")
    
    # Create all tables
    print("📊 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!")
    
    db = SessionLocal()
    try:
        # Check if we need to seed data
        from app.models import Job
        job_count = db.query(Job).count()
        
        if job_count == 0:
            print("🌱 Seeding sample jobs...")
            seed_jobs(db)
            print(f"✅ Sample jobs added!")
        else:
            print(f"ℹ️  Database already has {job_count} jobs, skipping seed.")
        
        print("\n✅ Setup complete! You can now run the backend:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        
    finally:
        db.close()


def seed_jobs(db):
    """Add sample jobs to database."""
    from app.models import Job
    from datetime import datetime, timedelta
    
    sample_jobs = [
        {
            "job_title": "Senior Software Engineer",
            "company_name": "TechCorp",
            "location": "San Francisco, CA",
            "job_type": "Full-time",
            "salary_range": "$150,000 - $200,000",
            "job_description": "We are looking for a Senior Software Engineer to join our growing team. You will work on building scalable backend services using Python, FastAPI, and PostgreSQL. Experience with cloud platforms (AWS/GCP) is required. Strong understanding of microservices architecture and RESTful API design. 5+ years of professional software development experience.",
            "skills_required": '["Python", "FastAPI", "PostgreSQL", "AWS", "Docker", "Kubernetes"]',
            "posted_date": (datetime.now() - timedelta(days=2)).isoformat(),
            "source": "Sample"
        },
        {
            "job_title": "Frontend Developer - React",
            "company_name": "StartupXYZ",
            "location": "Remote",
            "job_type": "Full-time",
            "salary_range": "$100,000 - $140,000",
            "job_description": "Join our team as a Frontend Developer. Build modern, responsive web applications using React, TypeScript, and Tailwind CSS. Work closely with designers and backend engineers. Experience with state management (Redux/Zustand) and REST API integration required. 3+ years of React development experience.",
            "skills_required": '["React", "TypeScript", "Tailwind CSS", "Redux", "REST APIs"]',
            "posted_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "source": "Sample"
        },
        {
            "job_title": "Full Stack Engineer",
            "company_name": "InnovateCo",
            "location": "New York, NY",
            "job_type": "Full-time",
            "salary_range": "$130,000 - $170,000",
            "job_description": "We're hiring a Full Stack Engineer to help build our product platform. You'll work on both frontend (React/Next.js) and backend (Node.js/Python) code. Database design experience with PostgreSQL and MongoDB. 4+ years of full stack development. CI/CD pipeline experience a plus.",
            "skills_required": '["React", "Node.js", "Python", "PostgreSQL", "MongoDB", "Docker"]',
            "posted_date": (datetime.now() - timedelta(hours=5)).isoformat(),
            "source": "Sample"
        },
        {
            "job_title": "Data Scientist",
            "company_name": "DataDriven Inc",
            "location": "Austin, TX",
            "job_type": "Full-time",
            "salary_range": "$120,000 - $160,000",
            "job_description": "Looking for a Data Scientist to extract insights from large datasets. Build machine learning models for predictive analytics. Experience with Python (pandas, scikit-learn, TensorFlow), SQL, and data visualization tools required. 3+ years in data science or related field.",
            "skills_required": '["Python", "Machine Learning", "SQL", "TensorFlow", "Pandas", "Data Visualization"]',
            "posted_date": (datetime.now() - timedelta(days=3)).isoformat(),
            "source": "Sample"
        },
        {
            "job_title": "DevOps Engineer",
            "company_name": "CloudFirst",
            "location": "Seattle, WA",
            "job_type": "Full-time",
            "salary_range": "$140,000 - $180,000",
            "job_description": "Join our DevOps team to build and maintain cloud infrastructure. Manage AWS/GCP environments, implement CI/CD pipelines, and ensure system reliability. Strong expertise in Kubernetes, Docker, Terraform, and Infrastructure as Code required. 4+ years DevOps/SRE experience.",
            "skills_required": '["AWS", "GCP", "Kubernetes", "Docker", "Terraform", "CI/CD", "Linux"]',
            "posted_date": datetime.now().isoformat(),
            "source": "Sample"
        },
        {
            "job_title": "Machine Learning Engineer",
            "company_name": "AI Ventures",
            "location": "Remote",
            "job_type": "Full-time",
            "salary_range": "$160,000 - $220,000",
            "job_description": "Build production-grade ML systems for our AI products. Design and deploy ML pipelines, work with LLMs, and optimize model performance. Experience with PyTorch, MLflow, and vector databases required. Background in NLP and transformer models preferred.",
            "skills_required": '["Python", "PyTorch", "MLflow", "LLMs", "NLP", "Vector Databases"]',
            "posted_date": (datetime.now() - timedelta(hours=12)).isoformat(),
            "source": "Sample"
        },
        {
            "job_title": "Product Manager",
            "company_name": "GrowthCo",
            "location": "Chicago, IL",
            "job_type": "Full-time",
            "salary_range": "$110,000 - $150,000",
            "job_description": "Lead product strategy and roadmap for our core platform. Work with engineering, design, and business teams to build features users love. Data-driven mindset with experience in A/B testing and product analytics. 3+ years of PM experience in tech.",
            "skills_required": '["Product Strategy", "Roadmapping", "Agile", "Data Analysis", "SQL", "User Research"]',
            "posted_date": (datetime.now() - timedelta(days=4)).isoformat(),
            "source": "Sample"
        },
        {
            "job_title": "Backend Engineer - Python",
            "company_name": "ScaleTech",
            "location": "Boston, MA",
            "job_type": "Full-time",
            "salary_range": "$130,000 - $170,000",
            "job_description": "Build high-performance backend services. Design RESTful APIs, work with message queues (Redis/Celery), and optimize database performance. Strong Python (FastAPI/Django), PostgreSQL, and Redis experience required. Experience with microservices a plus.",
            "skills_required": '["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Celery", "REST APIs"]',
            "posted_date": (datetime.now() - timedelta(days=2)).isoformat(),
            "source": "Sample"
        },
        {
            "job_title": "iOS Developer",
            "company_name": "MobileFirst",
            "location": "Los Angeles, CA",
            "job_type": "Full-time",
            "salary_range": "$120,000 - $160,000",
            "job_description": "Develop native iOS applications using Swift and SwiftUI. Work on a user-facing consumer app with millions of users. Experience with REST API integration, Core Data, and App Store deployment required. 3+ years iOS development experience.",
            "skills_required": '["Swift", "SwiftUI", "iOS", "Core Data", "REST APIs", "Xcode"]',
            "posted_date": (datetime.now() - timedelta(days=5)).isoformat(),
            "source": "Sample"
        },
        {
            "job_title": "Cloud Architect",
            "company_name": "Enterprise Solutions",
            "location": "Dallas, TX",
            "job_type": "Full-time",
            "salary_range": "$180,000 - $240,000",
            "job_description": "Design and implement enterprise cloud architectures. Lead cloud migration projects, define architectural standards, and mentor junior engineers. AWS/Azure/GCP certification required. 8+ years of IT/cloud experience with proven large-scale architecture.",
            "skills_required": '["AWS", "Azure", "GCP", "Architecture", "Terraform", "Security", "Networking"]',
            "posted_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "source": "Sample"
        }
    ]
    
    for job_data in sample_jobs:
        job = Job(**job_data)
        db.add(job)
    
    db.commit()
    print(f"   Added {len(sample_jobs)} sample jobs")


if __name__ == "__main__":
    setup()
