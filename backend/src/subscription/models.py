# # src/subscription/models.py
# from datetime import datetime, timedelta
#
# from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
# from sqlalchemy.orm import relationship
# from src.database import Base
#
#
# class Subscription(Base):
#     __tablename__ = "subscriptions"
#
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     stripe_checkout_session_id = Column(String, nullable=False)
#     stripe_subscription_id = Column(
#         String, nullable=True
#     )  # For recurring subscriptions
#     status = Column(
#         String, nullable=False, default="pending"
#     )  # e.g., 'active', 'expired', 'pending'
#     start_date = Column(DateTime, default=datetime.utcnow)
#     end_date = Column(DateTime)
#     endorsely_referral_id = Column(String, nullable=True)  # Add this field
#     referral_tracked = Column(Boolean, default=False)  # Add this field
#
#     # Relationships
#     user = relationship("User", back_populates="subscription")
