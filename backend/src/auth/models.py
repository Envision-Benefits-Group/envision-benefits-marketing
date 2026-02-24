# src.auth.models.py

from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base

# from src.subscription.models import Subscription

if TYPE_CHECKING:
    from src.feedback.models import Feedback


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    is_premium = mapped_column(Boolean, default=False, nullable=True)
    # subscription = relationship("Subscription", back_populates="user", uselist=False)
    # subscription_type: Mapped[str] = mapped_column(String(20), default="free", nullable=True)