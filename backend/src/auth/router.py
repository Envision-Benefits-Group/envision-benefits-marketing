# src.auth.router.py

import os
import traceback

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from src.auth import service
from src.auth.schemas import (ForgotPasswordRequest, Message,
                             ResetPasswordRequest, Token, RefreshTokenRequest,
                             UserCreate, UserDetailResponse, UserUpdate)
from src.auth.utils import create_access_token, split_name
from src.dependencies import CurrentUser, SessionDep
from src.email.email_service import EmailService

logger = structlog.get_logger("AUTH_ROUTER")
router = APIRouter()
email_service = EmailService(module="src.auth")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.post("/signup")
async def create_user(session: SessionDep, user_in: UserCreate):
    db_user = await service.get_user_by_email(session=session, email=user_in.email)
    if db_user:
        await logger.ainfo("Email already registered")
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await service.create_user(session=session, user_in=user_in)
    await logger.ainfo(f"User {user.email} created successfully")

    # Handle plan logic
    if user_in.plan and user_in.plan != "free":
        access_token = create_access_token(data={"sub": str(user.id)})
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active,
            "access_token": access_token,
        }

    return user


@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    session: SessionDep, form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    user = await service.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        await logger.ainfo(f"Failed login attempt for email {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        await logger.ainfo(f"Inactive user login attempt for email {user.email}")
        raise HTTPException(status_code=400, detail="Inactive user")
    tokens = await service.create_tokens_for_user(user)
    await logger.ainfo(f"User {user.email} logged in successfully")
    return Token(**tokens)


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
        session: SessionDep,
        refresh_request: RefreshTokenRequest
) -> Token:
       """
       Generate new access and refresh tokens using a valid refresh token.
       """
       try:
           tokens = await service.refresh_access_token(
               session=session,
               refresh_token=refresh_request.refresh_token
           )
           await logger.ainfo("Token refresh successful")
           return Token(**tokens)
       except HTTPException:
           raise
       except Exception:
           tb_str = traceback.format_exc()
           await logger.aerror("Exception in refresh_access_token endpoint", error=tb_str)
           raise HTTPException(
               status_code=500,
               detail="Internal server error during token refresh"
           )


@router.get("/user/current_user", response_model=UserDetailResponse)
async def get_current_user_details(current_user: CurrentUser):
    await logger.ainfo(f"Fetching details for user {current_user.email}")
    return current_user


@router.put("/user/current_user", response_model=UserDetailResponse)
async def update_current_user(
    session: SessionDep,
    current_user: CurrentUser,
    user_in: UserUpdate,
):
    try:
        # Store old email before update
        old_email = current_user.email

        # Update user in database
        user = await service.update_user(
            session=session, db_user=current_user, user_in=user_in
        )

        await logger.ainfo(f"User {user.email} updated successfully")
        return user
    except ValueError as ve:
        await logger.aerror(f"ValueError in update_current_user: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        tb_str = traceback.format_exc()
        await logger.aerror("Exception in update_current_user", error=tb_str)
        raise


@router.delete("/user/current_user", response_model=Message)
async def delete_current_user(session: SessionDep, current_user: CurrentUser):
    try:
        await service.delete_user(session=session, db_user=current_user)
        await logger.ainfo(f"User {current_user.email} deleted")
        return Message(message="User deleted successfully")
    except Exception:
        tb_str = traceback.format_exc()
        await logger.aerror("Exception in delete_current_user", error=tb_str)
        raise


@router.post("/forgot-password")
async def forgot_password(
    session: SessionDep,
    form_data: ForgotPasswordRequest,
):
    """
    Generates a password-reset token and emails it to the user.
    Returns a generic success message regardless of user existence.
    """
    # We don't raise any errors if the user doesn't exist (avoid email enumeration).
    await service.initiate_password_reset(session, form_data.email)
    return {"message": "If an account with that email exists, an email has been sent."}


@router.post("/reset-password")
async def reset_password(
    session: SessionDep,
    form_data: ResetPasswordRequest,
):
    """
    Verifies the token, then updates the user's password if valid.
    """
    await service.perform_password_reset(
        session, form_data.token, form_data.new_password
    )
    return {"message": "Your password has been reset successfully."}
