from typing import List
import structlog # Added for logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks # Added status and BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
import traceback

# Use SessionDep and CurrentSuperUser from global dependencies
from src.dependencies import SessionDep, CurrentSuperUser # CurrentSuperUser is Annotated
from src.admin import service as admin_service
from src.admin.schemas import UserAdminView # Removed AdminLoginRequest as it's not used
from src.auth.models import User # Corrected User model import
from src.auth.schemas import Token

# Initialize logger for the admin router
logger = structlog.get_logger("ADMIN_ROUTER")

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
async def admin_login_for_access_token(
    session: SessionDep, # Changed from db: Session to session: SessionDep
    form_data: OAuth2PasswordRequestForm = Depends()
):
    admin_username = form_data.username # Capture for logging
    await logger.ainfo(f"Admin login attempt for username: {admin_username}")
    try:
        token_data = await admin_service.admin_login_service(
            db=session, username=admin_username, password=form_data.password
        )
        await logger.ainfo(f"Admin user {admin_username} logged in successfully.")
        return token_data
    except HTTPException as e:
        await logger.awarn(f"Admin login failed for {admin_username}: {e.detail}", status_code=e.status_code)
        raise e
    except Exception as e: # Catch other unexpected errors
        tb_str = traceback.format_exc()
        await logger.aerror(f"Unexpected error during admin login for {admin_username}", error_message=str(e), traceback=tb_str)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during login. Check logs.")

@router.get("/users", response_model=List[UserAdminView]) # Removed explicit dependencies, CurrentSuperUser handles it
async def list_all_users_admin(
    session: SessionDep, # Changed from db: Session to session: SessionDep
    current_admin: CurrentSuperUser # Corrected: Use CurrentSuperUser directly as the type hint
):
    """
    Retrieve all users. Only accessible by superusers.
    """
    admin_email_for_log = current_admin.email # Capture email early for logging
    await logger.ainfo(f"Admin user {admin_email_for_log} requesting to list all users.")
    try:
        users = await admin_service.list_all_users_service(db=session)
        await logger.ainfo(f"Successfully retrieved {len(users)} users for admin {admin_email_for_log}.")
        return users
    except HTTPException as e: # Re-raise known HTTPExceptions from service
        await logger.awarn(f"Error listing users for admin {admin_email_for_log}: {e.detail}", status_code=e.status_code)
        raise
    except Exception as e: # Catch other unexpected errors from service or here
        tb_str = traceback.format_exc()
        await logger.aerror(f"Unexpected error listing users for admin {admin_email_for_log}", error_message=str(e), traceback=tb_str)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while listing users. Check logs.")