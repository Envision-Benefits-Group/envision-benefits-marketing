# # src/subscription/schemas.py
# from enum import Enum
# from typing import Optional
# from pydantic import BaseModel
#
# class SubscriptionTier(str, Enum):
#     FREE = "free"
#     VIP = "vip"
#     FOUNDER = "founder"
#
# class SubscriptionRequest(BaseModel):
#     subscription_type: SubscriptionTier
#     endorsely_referral: Optional[str] = None
