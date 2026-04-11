"""
Create a test user for development/testing.
Run this script to create a test user in the database.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine
from app.core.security import get_password_hash
from app.models import User
from app.database.session import Base

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def create_test_user():
    db: Session = SessionLocal()
    try:
        # Check if test user already exists
        existing = db.query(User).filter(User.email == "test@example.com").first()
        if existing:
            print("Test user already exists!")
            return
        
        # Create test user
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("testpassword123"),
            full_name="Test User",
            is_active=True,
            is_admin=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Test user created successfully!")
        print(f"  Email: test@example.com")
        print(f"  Password: testpassword123")
        print(f"  User ID: {user.id}")
    except Exception as e:
        db.rollback()
        print(f"Error creating test user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()