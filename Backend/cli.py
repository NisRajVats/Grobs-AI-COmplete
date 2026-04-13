#!/usr/bin/env python3
"""
GrobsAI Command Line Interface
Consolidated utility for user management and system operations.
"""
import sys
import os
import argparse
from typing import List, Optional

# Add parent directory to path to allow imports from app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine, Base
from app.core.security import get_password_hash, verify_password
from app.models.user import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_user(email: str, password: str, full_name: str, is_admin: bool = False):
    """Create a new user in the database."""
    db = SessionLocal()
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"Error: User with email {email} already exists.")
            return False
        
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            is_active=True,
            is_admin=is_admin
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"User created successfully!")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.full_name}")
        print(f"  Admin: {user.is_admin}")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        return False
    finally:
        db.close()

def delete_user(email: str):
    """Delete a user by email."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Error: User with email {email} not found.")
            return False
        
        print(f"Deleting user: {email} (ID: {user.id})")
        db.delete(user)
        db.commit()
        print(f"User deleted successfully.")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error deleting user: {e}")
        return False
    finally:
        db.close()

def check_user(email: str, password: Optional[str] = None):
    """Check if a user exists and optionally verify password."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User with email {email} not found.")
            return False
        
        print(f"User found: {user.email}")
        print(f"  ID: {user.id}")
        print(f"  Name: {user.full_name}")
        print(f"  Active: {user.is_active}")
        print(f"  Admin: {user.is_admin}")
        
        if password:
            is_valid = verify_password(password, user.hashed_password)
            print(f"  Password verification: {'Success' if is_valid else 'Failed'}")
        
        return True
    finally:
        db.close()

def list_users(limit: int = 20):
    """List users in the database."""
    db = SessionLocal()
    try:
        users = db.query(User).limit(limit).all()
        if not users:
            print("No users found in database.")
            return
        
        print(f"{'ID':<5} | {'Email':<30} | {'Name':<20} | {'Admin':<6}")
        print("-" * 70)
        for user in users:
            print(f"{user.id:<5} | {user.email:<30} | {user.full_name:<20} | {user.is_admin:<6}")
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="GrobsAI CLI Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create User
    create_parser = subparsers.add_parser("create-user", help="Create a new user")
    create_parser.add_argument("--email", required=True, help="User email")
    create_parser.add_argument("--password", required=True, help="User password")
    create_parser.add_argument("--name", required=True, help="User full name")
    create_parser.add_argument("--admin", action="store_true", help="Make user an admin")

    # Delete User
    delete_parser = subparsers.add_parser("delete-user", help="Delete a user")
    delete_parser.add_argument("--email", required=True, help="User email")

    # Check User
    check_parser = subparsers.add_parser("check-user", help="Check user details")
    check_parser.add_argument("--email", required=True, help="User email")
    check_parser.add_argument("--password", help="Verify user password")

    # List Users
    list_parser = subparsers.add_parser("list-users", help="List users")
    list_parser.add_argument("--limit", type=int, default=20, help="Limit number of users")

    args = parser.parse_args()

    if args.command == "create-user":
        create_user(args.email, args.password, args.name, args.admin)
    elif args.command == "delete-user":
        delete_user(args.email)
    elif args.command == "check-user":
        check_user(args.email, args.password)
    elif args.command == "list-users":
        list_users(args.limit)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
