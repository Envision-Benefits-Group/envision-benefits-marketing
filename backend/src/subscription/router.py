# # src/subscription/router.py
#
# import os
# import traceback
# from datetime import datetime, timedelta
#
# import stripe
# import structlog
# from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
# from sqlalchemy import select
# from sqlalchemy.exc import MultipleResultsFound
# from src.auth.models import User
# from src.dependencies import CurrentUser, SessionDep
# from src.ghl.ghl import GoHighLevelAPI
# from src.subscription.models import Subscription
# from src.subscription.schemas import SubscriptionRequest, SubscriptionTier
# from src.subscription.endorsely import EndorselyAPI
#
# logger = structlog.get_logger("SUBSCRIPTION_ROUTER")
#
# router = APIRouter(prefix="/stripe")
# ghl_api = GoHighLevelAPI()  # Initialize GHL API client
# endorsely_api = EndorselyAPI()
#
# stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
# SUCCESS_URL = os.getenv("SUCCESS_URL", "http://localhost:3000/success")
# CANCEL_URL = os.getenv("CANCEL_URL", "http://localhost:3000/cancel")
#
# # Pricing and duration settings (hardcoded)
# PRICING_TIERS = {
#     SubscriptionTier.VIP: {
#         "amount": 9900,  # in cents ($99)
#         "duration": timedelta(days=30),
#         "name": "VIP Subscription",
#     },
#     SubscriptionTier.FOUNDER: {
#         "amount": 88800,  # in cents ($888)
#         "duration": timedelta(days=365),
#         "name": "Founder Subscription",
#     },
# }
#
# @router.post("/create-checkout-session")
# async def create_checkout_session(
#     current_user: CurrentUser,
#     session: SessionDep,
#     req: SubscriptionRequest,
# ):
#     try:
#         tier = req.subscription_type
#         now = datetime.utcnow()
#
#         # For paid tiers, validate tier and set pricing details.
#         if tier not in PRICING_TIERS:
#             raise HTTPException(status_code=400, detail="Invalid subscription type.")
#
#         pricing = PRICING_TIERS[tier]
#
#         # Check for an existing pending subscription (if any)
#         result = await session.execute(
#             select(Subscription).where(
#                 Subscription.user_id == current_user.id,
#                 Subscription.status == "pending",
#             )
#         )
#         pending_subscription = result.scalar_one_or_none()
#
#         # Prepare metadata
#         metadata = {
#             "user_id": str(current_user.id),
#             "subscription_type": str(tier.value),
#             "user_email": str(current_user.email),
#             "email": str(current_user.email),
#         }
#
#         # Add referrer from user profile if exists
#         if current_user.referrer:
#             metadata["referrer"] = str(current_user.referrer)
#
#         # Add Endorsely referral with a different key to avoid automatic tracking
#         if req.endorsely_referral:
#             metadata["e_ref"] = str(req.endorsely_referral)  # Changed key name
#
#         # Create checkout session with metadata
#         checkout_session = stripe.checkout.Session.create(
#             payment_method_types=["card"],
#             line_items=[
#                 {
#                     "price_data": {
#                         "currency": "usd",
#                         "product_data": {"name": pricing["name"]},
#                         "unit_amount": pricing["amount"],
#                     },
#                     "quantity": 1,
#                 }
#             ],
#             mode="payment",
#             success_url=f"{SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
#             cancel_url=CANCEL_URL,
#             customer_email=current_user.email,
#             metadata=metadata,
#             payment_intent_data={
#                 "metadata": metadata,
#             },
#         )
#
#         # Calculate expiration date based on tier duration.
#         expiration_date = now + pricing["duration"]
#
#         if pending_subscription:
#             # Update existing pending subscription.
#             pending_subscription.stripe_checkout_session_id = checkout_session.id
#             pending_subscription.start_date = now
#             pending_subscription.end_date = expiration_date
#             pending_subscription.endorsely_referral_id = req.endorsely_referral  # Add this
#             await session.commit()
#             await logger.ainfo(
#                 f"Updated pending subscription {checkout_session.id} for user {current_user.email}"
#             )
#         else:
#             # Create a new pending subscription record.
#             new_subscription = Subscription(
#                 user_id=current_user.id,
#                 stripe_checkout_session_id=checkout_session.id,
#                 status="pending",
#                 start_date=now,
#                 end_date=expiration_date,
#                 endorsely_referral_id=req.endorsely_referral  # Add this
#             )
#             session.add(new_subscription)
#             await session.commit()
#             await logger.ainfo(
#                 f"Created checkout session {checkout_session.id} for user {current_user.email}"
#             )
#
#         # Return both the session id and the pending subscription details.
#         return {
#             "sessionId": checkout_session.id,
#             "subscription": {
#                 "subscriptionType": tier.value,
#                 "isPremium": True,  # For paid tiers.
#                 "expiresOn": expiration_date.isoformat(),
#             },
#         }
#     except Exception:
#         tb_str = traceback.format_exc()
#         await logger.aerror(
#             f"Error creating checkout session for user {current_user.email}",
#             error=tb_str,
#         )
#         raise HTTPException(
#             status_code=500, detail="Failed to create checkout session."
#         )
#
#
# @router.post("/webhook")
# async def stripe_webhook(
#     request: Request, session: SessionDep, background_tasks: BackgroundTasks
# ):
#     """
#     Stripe webhook endpoint to handle various Stripe events.
#     """
#     payload = await request.body()
#     sig_header = request.headers.get("stripe-signature")
#     await logger.ainfo("Received Stripe webhook event")
#
#     try:
#         event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
#         await logger.ainfo(f"Stripe event constructed: {event['type']}")
#     except (ValueError, stripe.error.SignatureVerificationError):
#         await logger.ainfo("Invalid webhook signature or payload")
#         raise HTTPException(status_code=400, detail="Invalid webhook")
#
#     # Handle different event types
#     if event["type"] == "checkout.session.completed":
#         # Payment was successful
#         checkout_session = event["data"]["object"]
#         session_id = checkout_session.get("id")
#         metadata = checkout_session.get("metadata", {})
#         payment_status = checkout_session.get("payment_status")
#
#         # Double check payment status
#         if payment_status != "paid":
#             await logger.ainfo(
#                 f"Checkout session {session_id} completed but payment status is {payment_status}"
#             )
#             return {"status": "success"}
#
#         await logger.ainfo(
#             f"Processing checkout.session.completed for session {session_id} with metadata: {metadata}"
#         )
#         # Fetch subscription from DB by Stripe checkout session ID.
#         result = await session.execute(
#             select(Subscription).where(
#                 Subscription.stripe_checkout_session_id == session_id
#             )
#         )
#         subscription = result.scalar_one_or_none()
#         if subscription:
#             await logger.ainfo(f"Subscription found for session {session_id}")
#             # Explicitly load the user to avoid lazy-loading issues.
#             user_result = await session.execute(
#                 select(User).where(User.id == subscription.user_id)
#             )
#             user = user_result.scalar_one_or_none()
#             if user:
#                 # Update the user record based on the checkout metadata.
#                 subscription_type = metadata.get("subscription_type", "vip")
#                 user.subscription_type = subscription_type
#                 user.is_premium = True
#                 subscription.status = "active"
#                 await session.commit()
#                 await logger.ainfo(
#                     f"Updated user {user.email}: subscription type {subscription_type} and subscription {subscription.id} to active"
#                 )
#                 # Determine additional GHL tags based on subscription type.
#                 additional_tag = ""
#                 if subscription_type == SubscriptionTier.VIP.value:
#                     additional_tag = "VIP8UP"
#                 elif subscription_type == SubscriptionTier.FOUNDER.value:
#                     additional_tag = "FOUNDER8UP"
#                 # Always include the base tag for paid subscriptions.
#                 tags = ["paid8up"]
#                 if additional_tag:
#                     tags.append(additional_tag)
#                 background_tasks.add_task(add_paid_tag_to_user, user.email, tags)
#
#                 # Track referral in Endorsely if user was referred
#                 if subscription.endorsely_referral_id and not subscription.referral_tracked:
#                     try:
#                         # Get the pricing amount based on subscription type
#                         tier = SubscriptionTier(subscription_type)
#                         amount = PRICING_TIERS[tier]["amount"]
#
#                         # Track the referral
#                         await endorsely_api.track_referral(
#                             referral_id=subscription.endorsely_referral_id,
#                             email=user.email,
#                             amount=amount,
#                             customer_id=str(user.id),
#                             name=user.name
#                         )
#
#                         # Mark as tracked only after successful tracking
#                         subscription.referral_tracked = True
#                         # Commit the change immediately
#                         await session.commit()
#
#                         await logger.ainfo(
#                             "Successfully tracked Endorsely referral",
#                             referral_id=subscription.endorsely_referral_id,
#                             user_id=user.id
#                         )
#                     except Exception:
#                         await logger.aerror(
#                             "Failed to track referral in Endorsely",
#                             error=traceback.format_exc(),
#                             user_id=user.id,
#                             referral_id=subscription.endorsely_referral_id
#                         )
#             else:
#                 await logger.ainfo(f"User not found for subscription {subscription.id}")
#         else:
#             await logger.ainfo(f"No subscription found for session {session_id}")
#     elif event["type"] in ["checkout.session.expired", "payment_intent.payment_failed", "charge.failed"]:
#         # Payment failed or session expired
#         checkout_session = event["data"]["object"]
#         session_id = checkout_session.get("id")
#
#         # Update subscription status to failed
#         result = await session.execute(
#             select(Subscription).where(
#                 Subscription.stripe_checkout_session_id == session_id
#             )
#         )
#         subscription = result.scalar_one_or_none()
#
#         if subscription:
#             # subscription.status = "failed"
#             # await session.commit()
#             await logger.ainfo(
#                 f"Checkout session failed or expired for session {session_id}"
#             )
#     else:
#         await logger.ainfo(f"Unhandled event type: {event['type']}")
#
#     return {"status": "success"}
#
#
# async def add_paid_tag_to_user(email: str, tags: list[str]):
#     """
#     Helper function to add GHL tags to a user's contact.
#     Adds the default 'paid8up' tag and additional tags (e.g., VIP8UP or FOUNDER8UP)
#     based on the subscription type.
#     """
#     try:
#         await ghl_api.add_tags_to_contact(email, tags)
#         await logger.ainfo(f"Added tags {tags} to user {email} in GHL")
#     except Exception:
#         tb_str = traceback.format_exc()
#         await logger.aerror(
#             f"Exception when adding tags {tags} to contact {email}", error=tb_str
#         )
#
#
# @router.get("/subscription/status")
# async def get_subscription_status(current_user: CurrentUser, session: SessionDep):
#     try:
#         result = await session.execute(
#             select(Subscription).where(
#                 Subscription.user_id == current_user.id,
#                 Subscription.status == "active",
#                 )
#         )
#         subscription = result.scalar_one_or_none()
#         await logger.ainfo(
#             f"Retrieved subscription status for user {current_user.email}"
#         )
#
#         if subscription:
#             return {
#                 "subscriptionType": current_user.subscription_type,
#                 "isPremium": current_user.is_premium,
#                 "expiresOn": subscription.end_date.isoformat(),
#             }
#         else:
#             return {"subscriptionType": "free", "isPremium": False}
#     except MultipleResultsFound:
#         # Handle the case where multiple active subscriptions are found.
#         result = await session.execute(
#             select(Subscription)
#             .where(
#                 Subscription.user_id == current_user.id,
#                 Subscription.status == "active",
#                 )
#             .order_by(Subscription.end_date.desc())
#         )
#         subscription = result.scalars().first()
#         await logger.ainfo(
#             f"Multiple active subscriptions found for user {current_user.email}. Using the most recent one."
#         )
#         if subscription:
#             return {
#                 "subscriptionType": current_user.subscription_type,
#                 "isPremium": current_user.is_premium,
#                 "expiresOn": subscription.end_date.isoformat(),
#             }
#         else:
#             return {"subscriptionType": "free", "isPremium": False}
#
#
# @router.get("/session")
# async def get_checkout_session(current_user: CurrentUser, session_id: str):
#     try:
#         await logger.ainfo(
#             f"Retrieving checkout session {session_id} for user {current_user.email}"
#         )
#         session_obj = stripe.checkout.Session.retrieve(session_id)
#         return session_obj
#     except Exception:
#         tb_str = traceback.format_exc()
#         await logger.aerror(
#             f"Error retrieving checkout session {session_id} for user {current_user.email}",
#             error=tb_str,
#         )
#         raise HTTPException(
#             status_code=500, detail="Failed to retrieve checkout session."
#         )
