# src.contact.router.py

import traceback
from typing import List, Optional

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from src.contact import service
from src.contact.schemas import (
    ContactSubmissionCreate,
    ContactSubmissionResponse,
    ContactSubmissionSuccess,
)
from src.dependencies import SessionDep, CurrentSuperUser

logger = structlog.get_logger("CONTACT_ROUTER")
router = APIRouter()


@router.post("/", response_model=ContactSubmissionSuccess)
async def submit_contact_form(
    session: SessionDep, 
    contact_in: ContactSubmissionCreate
):
    """
    Submit a contact form (public endpoint).
    
    This endpoint accepts contact form submissions from the public website.
    Input validation and sanitization is handled by Pydantic schemas.
    """
    try:
        # Create the contact submission
        contact_submission = await service.create_contact_submission(
            session=session, 
            contact_in=contact_in
        )
        
        await logger.ainfo(
            f"Contact form submitted successfully with ID {contact_submission.id}",
            email=contact_in.email,
            subject=contact_in.subject
        )
        
        return ContactSubmissionSuccess(
            message="Thank you for your message! We'll get back to you within 24 hours.",
            submission_id=contact_submission.id
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValidationError as validation_error:
        await logger.awarning(
            "Contact form validation error",
            error=str(validation_error)
        )
        raise HTTPException(
            status_code=422, 
            detail="Invalid form data. Please check your inputs and try again."
        )
    except Exception as e:
        tb_str = traceback.format_exc()
        await logger.aerror("Error submitting contact form", error=tb_str)
        
        error_msg = str(e)
        if "migrations" in error_msg and "alembic upgrade head" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable. Database needs to be updated."
            )
        
        raise HTTPException(
            status_code=500, 
            detail="We're sorry, but there was an error processing your request. Please try again later."
        )


@router.get("/{submission_id}", response_model=ContactSubmissionResponse)
async def get_contact_submission(
    submission_id: int,
    session: SessionDep,
    _: CurrentSuperUser
):
    """
    Get a specific contact submission by ID (admin only).
    """
    try:
        submission = await service.get_contact_submission_by_id(
            session=session, 
            submission_id=submission_id
        )
        
        if not submission:
            raise HTTPException(
                status_code=404, 
                detail=f"Contact submission with ID {submission_id} not found"
            )
        
        await logger.ainfo(f"Retrieved contact submission with ID {submission_id} (admin request)")
        return ContactSubmissionResponse.model_validate(submission)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception:
        tb_str = traceback.format_exc()
        await logger.aerror(f"Error retrieving contact submission with ID {submission_id}", error=tb_str)
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve contact submission"
        )


@router.get("/admin/all", response_model=List[ContactSubmissionResponse])
async def get_all_contact_submissions_admin(
    session: SessionDep,
    _: CurrentSuperUser,
    limit: Optional[int] = Query(100, description="Number of contact submissions to retrieve")
):
    """
    Get all contact submissions (admin only).
    """
    try:
        submissions = await service.get_all_contact_submissions(
            session=session, 
            limit=limit
        )
        
        await logger.ainfo(f"Retrieved {len(submissions)} contact submissions (admin request)")
        return [ContactSubmissionResponse.model_validate(submission) for submission in submissions]
        
    except Exception:
        tb_str = traceback.format_exc()
        await logger.aerror("Error retrieving all contact submissions", error=tb_str)
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve contact submissions"
        ) 