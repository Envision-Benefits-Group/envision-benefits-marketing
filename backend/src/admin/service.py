import os # For getenv
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid
import structlog # Added for logging
import traceback # Added for manual traceback formatting

from sqlalchemy.ext.asyncio import AsyncSession # Changed from Session
from sqlalchemy.future import select # For async queries
from sqlalchemy.orm import selectinload # For eager loading relationships
from fastapi import HTTPException, status, BackgroundTasks # Added BackgroundTasks

# Corrected imports based on project structure
from src.auth.utils import verify_password, create_access_token, ALGORITHM, SECRET_KEY # Reused from auth
from src.auth.service import get_user_by_email # Reused from auth
from src.admin.schemas import UserAdminView
from src.auth.models import User # Corrected model import
from src.email.email_service import EmailService # Import EmailService

# Initialize logger for the admin service
logger = structlog.get_logger("ADMIN_SERVICE")

# Define admin token expiry similar to how it's done in auth.utils
ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 240))

async def admin_login_service(db: AsyncSession, username: str, password: str):
    await logger.ainfo(f"Attempting admin login for username: {username}")
    user = await get_user_by_email(session=db, email=username) # Use async session, await call
    if not user or not verify_password(password, user.hashed_password):
        await logger.awarn(f"Admin login failed: Incorrect username or password for {username}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_superuser:
        await logger.awarn(f"Admin login failed: User {username} lacks superuser privileges.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have superuser privileges"
        )

    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=expires_delta # Use user.email for sub, consistent with auth.utils
    )
    await logger.ainfo(f"Admin user {username} authenticated successfully.")
    return {"access_token": access_token, "token_type": "bearer"}

async def list_all_users_service(db: AsyncSession) -> List[UserAdminView]:
    await logger.ainfo("Fetching all users for admin panel.")
    try:
        # Eager load the subscription relationship using selectinload
        result = await db.execute(
            select(User).options(selectinload(User.subscription))
        )
        users = result.scalars().all()

        user_views = []
        for user_model in users:

            user_views.append(
                UserAdminView(
                    id=user_model.id,
                    name=user_model.name,
                    email=user_model.email,
                    is_active=user_model.is_active,
                    is_superuser=user_model.is_superuser,
                    is_premium=user_model.is_premium,
                    created_at=user_model.created_at,
                )
            )
        await logger.ainfo(f"Successfully fetched {len(user_views)} users.")
        return user_views
    except Exception as e:
        tb_str = traceback.format_exc() # Manually format traceback
        await logger.aerror(
            "Error fetching all users for admin panel.",
            error_message=str(e), # Add error message
            traceback=tb_str # Add manually formatted traceback
        )
        # Optionally, include tb_str in the detail if you want it in the HTTP response (for dev/debug)
        # For production, you might prefer a generic message in the HTTP response.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error while fetching users. Check logs for details.")