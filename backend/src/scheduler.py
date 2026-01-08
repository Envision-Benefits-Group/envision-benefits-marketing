# src/scheduler.py
from datetime import datetime
import traceback

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.database import AsyncSessionLocal
import structlog

logger = structlog.get_logger("SCHEDULER")

# get data