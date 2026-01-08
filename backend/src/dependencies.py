import os
from typing import Annotated, AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.auth.models import User
from src.auth.schemas import TokenPayload
from src.auth.utils import ALGORITHM
from src.database import AsyncSessionLocal

SECRET_KEY = os.getenv("secret")

oauth2_scheme_admin = OAuth2PasswordBearer(tokenUrl="/admin-panel/login/access-token")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/access-token")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)

        if token_data.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type, expected 'access'",
            )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Handle both user ID (regular auth) and email (admin auth) in the token subject
    user = None
    try:
        # First try to parse as user ID (regular auth)
        user_id = int(token_data.sub)
        result = await session.execute(
            select(User).where(User.id == user_id).options(selectinload(User.permissions))
        )
        user = result.scalar_one_or_none()
    except (ValueError, TypeError):
        # If parsing as int fails, treat as email (admin auth)
        email = token_data.sub
        result = await session.execute(
            select(User).where(User.email == email).options(selectinload(User.permissions))
        )
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency for any active user (both free and premium).
    This is used for endpoints that should be accessible to all users.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]


async def get_current_admin_user(
    session: SessionDep, token: str = Depends(oauth2_scheme_admin)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials for admin",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise credentials_exception
    except (InvalidTokenError, ValidationError) as e:
        raise credentials_exception from e

    from src.auth.service import get_user_by_email

    user = await get_user_by_email(session=session, email=token_data.sub)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Admin user not found"
        )
    return user


AdminUser = Annotated[User, Depends(get_current_admin_user)]


def get_current_active_superuser(current_user: AdminUser) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive admin user"
        )
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


CurrentSuperUser = Annotated[User, Depends(get_current_active_superuser)]


async def get_current_premium_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium membership is required to access this resource.",
        )
    return current_user


CurrentPremiumUser = Annotated[User, Depends(get_current_premium_user)]
