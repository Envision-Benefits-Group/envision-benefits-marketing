import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from src.admin import router as admin_router
from src.auth import router as auth_routers
from src.database import engine
from src.logging_config import setup_logging
# # from src.scheduler import scheduler
# from src.subscription.models import Subscription
# from src.subscription.router import router as subscription_router
from starlette.requests import Request
from structlog.contextvars import (bind_contextvars, clear_contextvars)

# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
setup_logging()

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup code
#     scheduler.start()
#     print("Scheduler started")
#     yield
#     # Shutdown code
#     scheduler.shutdown()
#     print("Scheduler shutdown")


app = FastAPI()

# Add GZip Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS Middleware if needed
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_context_to_logs(request: Request, call_next):
    # Clear any existing context variables to avoid data leakage between requests
    clear_contextvars()

    # Extract user ID from headers
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        user_id = "None"

    # Bind user_id to the context
    bind_contextvars(user_id=user_id)

    # Proceed with the request and response cycle
    response = await call_next(request)
    return response


# Include your routers
app.include_router(auth_routers.router, tags=["Authentication"], prefix="/auth")
app.include_router(admin_router.router, tags=["Admin"], prefix="/admin")


# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI User CRUD with PostgreSQL"}

# health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}