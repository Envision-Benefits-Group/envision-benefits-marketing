# src.auth.service.py

import os
import traceback

import jwt
import structlog
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.auth.models import User
from src.auth.schemas import UserCreate, UserUpdate
from src.auth.utils import (
    ALGORITHM,
    SECRET_KEY,
    create_reset_token,
    generate_random_password,
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from src.email.email_service import EmailService

logger = structlog.get_logger("AUTH_SERVICE")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


async def create_user(*, session: AsyncSession, user_in: UserCreate) -> User:
    try:
        # Convert email to lowercase before storing
        email = user_in.email.lower()
        hashed_password = get_password_hash(user_in.password)
        user = User(
            email=email,
            name=user_in.name,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
            terms_accepted=user_in.agreed_to_terms,
            phone=user_in.phone,
            address=user_in.address,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        await logger.ainfo(f"User {user.email} created in the database")
        return user
    except IntegrityError:
        await session.rollback()
        await logger.aerror(f"IntegrityError when creating user {email}")
        raise HTTPException(
            status_code=400, detail="User with this email already exists."
        )
    except SQLAlchemyError:
        await session.rollback()
        tb_str = traceback.format_exc()
        await logger.aerror(f"SQLAlchemyError when creating user {email}", error=tb_str)
        raise HTTPException(
            status_code=500, detail="Failed to create user due to database error."
        )


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    try:
        # Convert email to lowercase for case-insensitive comparison
        email = email.lower()
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        await logger.ainfo(f"Retrieved user by email {email}")
        return user
    except Exception:
        tb_str = traceback.format_exc()
        await logger.aerror(f"Exception in get_user_by_email for {email}", error=tb_str)
        raise


async def get_user_by_id(*, session: AsyncSession, user_id: int) -> User | None:
    """
    Get user by ID for refresh token validation.
    """
    try:
        result = await session.execute(
            select(User)
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            await logger.ainfo(f"Retrieved user by ID {user_id}")
        return user
    except Exception:
        tb_str = traceback.format_exc()
        await logger.aerror(f"Exception in get_user_by_id for {user_id}", error=tb_str)
        raise


async def authenticate(
    *, session: AsyncSession, email: str, password: str
) -> User | None:
    # Email will be converted to lowercase in get_user_by_email
    user = await get_user_by_email(session=session, email=email)
    if not user:
        await logger.ainfo(f"Authentication failed: User {email.lower()} not found")
        return None
    if not verify_password(password, user.hashed_password):
        await logger.ainfo(
            f"Authentication failed: Incorrect password for {email.lower()}"
        )
        return None
    await logger.ainfo(f"User {email.lower()} authenticated successfully")
    return user


async def create_tokens_for_user(user: User) -> dict:
    """
    Create both access and refresh tokens for a user.
    The subject ('sub') of the token is the user's ID to ensure it's a stable identifier.
    """
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    await logger.ainfo(f"Created tokens for user {user.email}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def refresh_access_token(*, session: AsyncSession, refresh_token: str) -> dict:
    """
    Generate new access and refresh tokens using a valid refresh token.
    """
    try:
        # Verify the refresh token
        payload = verify_refresh_token(refresh_token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
            )

        # Get the user
        user = await get_user_by_id(session=session, user_id=int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
            )

        # Create new tokens
        new_tokens = await create_tokens_for_user(user)
        await logger.ainfo(f"Refresh token used successfully for user {user.email}")
        return new_tokens

    except jwt.ExpiredSignatureError:
        await logger.ainfo("Expired refresh token used")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired"
        )
    except (jwt.InvalidTokenError, ValueError) as e:
        await logger.awarn(f"Invalid refresh token used: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    except Exception:
        tb_str = traceback.format_exc()
        await logger.aerror("Exception in refresh_access_token", error=tb_str)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh",
        )


async def update_user(
    *, session: AsyncSession, db_user: User, user_in: UserUpdate
) -> User:
    # Capture user email before any operations to avoid detached instance issues
    user_email = db_user.email
    
    try:
        user_data = user_in.model_dump(exclude_unset=True)
        # Handle password change
        if "new_password" in user_data:
            new_password = user_data.pop("new_password")
            current_password = user_data.pop("current_password", None)
            if not current_password:
                await logger.ainfo(
                    f"Password change requested without current password for user {user_email}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="Current password is required to change password",
                )
            if not verify_password(current_password, db_user.hashed_password):
                await logger.ainfo(
                    f"Incorrect current password for user {user_email}"
                )
                raise HTTPException(
                    status_code=400, detail="Current password is incorrect"
                )
            hashed_password = get_password_hash(new_password)
            user_data["hashed_password"] = hashed_password

        if user_data:
            for key, value in user_data.items():
                setattr(db_user, key, value)
            await session.commit()
            await session.refresh(db_user)
            await logger.ainfo(f"User {user_email} updated successfully")
        return db_user
    except Exception:
        await session.rollback()
        tb_str = traceback.format_exc()
        await logger.aerror(
            f"Exception in update_user for {user_email}", error=tb_str
        )
        raise


async def delete_user(*, session: AsyncSession, db_user: User):
    # Capture user email before any operations to avoid detached instance issues
    user_email = db_user.email
    
    try:
        await session.delete(db_user)
        await session.commit()
        await logger.ainfo(f"User {user_email} deleted from the database")
    except Exception:
        await session.rollback()
        tb_str = traceback.format_exc()
        await logger.aerror(
            f"Exception in delete_user for {user_email}", error=tb_str
        )
        raise


async def initiate_password_reset(session: AsyncSession, email: str):
    """
    Initiates the password reset process by creating a token and emailing the user.
    Returns True if the email was found and the email sent, or False if user not found.
    """
    # Email will be converted to lowercase in get_user_by_email
    user = await get_user_by_email(session=session, email=email)
    if not user:
        # Return False to indicate no user found (for reference),
        # but we won't raise an error to avoid email enumeration.
        await logger.ainfo("Password reset requested for non-existent email.")
        return False

    # 1. Create a short-lifespan reset token
    reset_token = create_reset_token(email=user.email)

    # 2. Construct the reset link to match Next.js dynamic route structure
    # Changed from /reset-password?token= to /reset-password/{token}
    reset_link = f"{FRONTEND_URL}/auth/reset-password/{reset_token}"

    # 3. Send the email
    email_service = EmailService(module="src.auth")
    email_service.send_forgot_password_email(
        to_address=user.email,
        user_name=user.name if user.name else "",
        reset_link=reset_link,
    )

    await logger.ainfo(f"Password reset initiated for {user.email}")
    return True


async def perform_password_reset(session: AsyncSession, token: str, new_password: str):
    """
    Verifies the reset token and updates the user's password if valid.
    Returns the user or raises HTTPException if invalid/expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    user = await get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Hash the new password
    new_hashed_password = get_password_hash(new_password)
    user.hashed_password = new_hashed_password

    session.add(user)
    await session.commit()
    await session.refresh(user)

    await logger.ainfo(f"Password reset performed for {user.email}")
    return user
