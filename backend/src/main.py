import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from src.logging_config import setup_logging
from src.extraction import router as extraction_router
from starlette.requests import Request
from structlog.contextvars import (bind_contextvars, clear_contextvars)

# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
setup_logging()

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

app.include_router(extraction_router.router, tags=["Extraction"], prefix="/extraction")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI"}

# health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}