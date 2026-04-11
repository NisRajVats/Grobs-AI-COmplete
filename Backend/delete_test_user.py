# Enhanced script to delete test users by multiple emails from the database
from app.database.session import SessionLocal
from app.models.user import User

# List of common test/demo emails to delete
TEST_EMAILS = [
    \"test@example.com\",
    \"rajputnishant393@gmail.com\",
    \"demo@grobsai.com\",  # Add more if needed
]

def delete_users_by_emails(emails):
    db = SessionLocal()
    deleted = 0
    try:
        for email in emails:
            user = db.query(User).filter(User.email == email).first()
            if user:
                print(f\"Deleting user: {email} (ID: {user.id}, active: {user.is_active})\")
                db.delete(user)
                deleted += 1
            else:
                print(f\"User not found: {email}\")
        db.commit()
        print(f\"{deleted} users deleted successfully.\")
    except Exception as e:
        print(f\"Error: {e}\")
        db.rollback()
    finally:
        db.close()

if __name__ == \"__main__\":
    print(\"Deleting test users...\")
    delete_users_by_emails(TEST_EMAILS)
    print(\"Done. Restart backend and test register/login.\")

