import os
import csv
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.auth.models import User
from src.auth.utils import get_password_hash

def initialize_or_update_superuser():
    # Load environment variables
    load_dotenv()
    SUPERUSER_EMAIL = os.getenv("SUPERUSER_EMAIL")
    SUPERUSER_PASSWORD = os.getenv("SUPERUSER_PASSWORD")
    if not SUPERUSER_EMAIL or not SUPERUSER_PASSWORD:
        raise ValueError("SUPERUSER_EMAIL and SUPERUSER_PASSWORD must be set in the environment variables.")

    # Get the synchronous database URL
    DATABASE_URL = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL or ALEMBIC_DATABASE_URL must be set in the environment variables.")

    # Remove async driver prefix if present
    sync_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")

    # Create a synchronous engine
    engine = create_engine(sync_DATABASE_URL, future=True)

    # Create a synchronous session
    session = Session(bind=engine)
    try:
        # Check if a user with the superuser email already exists
        existing_user = session.query(User).filter(User.email == SUPERUSER_EMAIL).first()
        if existing_user:
            # Update the user
            existing_user.hashed_password = get_password_hash(SUPERUSER_PASSWORD)
            existing_user.is_active = True
            existing_user.is_superuser = True
            session.commit()
            print("Superuser updated.")
        else:
            # Create a new superuser
            superuser = User(
                email=SUPERUSER_EMAIL,
                hashed_password=get_password_hash(SUPERUSER_PASSWORD),
                is_active=True,
                is_superuser=True,
                name="Admin"
            )
            session.add(superuser)
            session.commit()
            session.refresh(superuser)
            print("Superuser created.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    initialize_or_update_superuser()
