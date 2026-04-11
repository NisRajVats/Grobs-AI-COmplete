"""Check test user in database"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models import User
from app.core.security import verify_password

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == "test@example.com").first()
    if user:
        print(f"User found: {user.email}")
        print(f"Hashed password: {user.hashed_password[:30]}...")
        # Test password verification
        result = verify_password("testpassword123", user.hashed_password)
        print(f"Password verification: {result}")
    else:
        print("User not found")
finally:
    db.close()