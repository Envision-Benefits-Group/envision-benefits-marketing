import os
import secrets
import string
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("secret")
ALGORITHM = os.getenv("algorithm")
ACCESS_TOKEN_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 120))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
RESET_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("RESET_TOKEN_EXPIRE_MINUTES", 60)
)  # or any short duration you prefer


access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE)
refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)


def create_access_token(
        data: dict, expires_delta: timedelta = access_token_expires
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": secrets.token_hex(16)
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(
        data: dict, expires_delta: timedelta = refresh_token_expires
) -> str:
    """
    Creates a refresh token with a longer expiry time.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_hex(16)
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_refresh_token(token: str) -> dict:
    """
    Verifies and decodes a refresh token.
    Raises ValueError if the token type is not 'refresh'.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def split_name(full_name: str | None):
    if not full_name:
        return "", ""
    parts = full_name.split(maxsplit=1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""
    return first_name, last_name


def create_reset_token(email: str) -> str:
    """
    Creates a short-lifespan JWT for password reset, storing the user's email in 'sub'.
    """
    data = {"sub": email}
    expires_delta = timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    return create_access_token(data=data, expires_delta=expires_delta)


def generate_random_password(length: int = 12) -> str:
    """
    Generate a secure random password with letters, digits, and special characters.
    """
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!@#$%^&*"

    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special_chars),
    ]

    # Fill the rest with random characters from all sets
    all_chars = lowercase + uppercase + digits + special_chars
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))

    # Shuffle the password list to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)

    return "".join(password)
