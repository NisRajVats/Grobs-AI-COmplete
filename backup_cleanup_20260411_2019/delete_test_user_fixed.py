from app.database.session import SessionLocal
from app.models.user import User

TEST_EMAILS = [
    'test@example.com',
    'rajputnishant393@gmail.com',
    'demo@grobsai.com',
]

def delete_users():
    db = SessionLocal()
    deleted = 0
    try:
        for email in TEST_EMAILS:
            user = db.query(User).filter(User.email == email).first()
            if user:
                print(f'Deleting {email}')
                db.delete(user)
                deleted += 1
        db.commit()
        print(f'{deleted} users deleted.')
    except Exception as e:
        print(f'Error: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    delete_users()

