# src.contact.service.py

import os
import traceback
from datetime import datetime
from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.contact.models import ContactSubmission
from src.contact.schemas import ContactSubmissionCreate
from src.email.email_service import EmailService

logger = structlog.get_logger("CONTACT_SERVICE")


async def create_contact_submission(
    session: AsyncSession, 
    contact_in: ContactSubmissionCreate
) -> ContactSubmission:
    """
    Create a new contact submission and send notification email to admin.
    
    Args:
        session: Database session
        contact_in: Contact submission data
        
    Returns:
        ContactSubmission: The created contact submission
        
    Raises:
        Exception: If there's an error creating the submission
    """
    contact_submission = None
    try:
        # Create the contact submission record
        contact_submission = ContactSubmission(
            first_name=contact_in.first_name,
            last_name=contact_in.last_name,
            email=contact_in.email,
            phone=contact_in.phone,
            subject=contact_in.subject,
            message=contact_in.message
        )
        
        session.add(contact_submission)
        await session.commit()
        await session.refresh(contact_submission)
        
        await logger.ainfo(
            f"Contact submission created with ID {contact_submission.id}",
            email=contact_in.email,
            subject=contact_in.subject
        )
        
        # Send notification email to admin (fire and forget)
        try:
            await _send_contact_notification_email(contact_submission)
        except Exception as email_error:
            # Log email error but don't fail the submission
            await logger.aerror(
                "Failed to send contact notification email",
                error=str(email_error),
                submission_id=contact_submission.id if contact_submission else None
            )
        
        return contact_submission
        
    except Exception as e:
        tb_str = traceback.format_exc()
        await logger.aerror("Error creating contact submission", error=tb_str)
        await session.rollback()
        
        # Check if it's a table doesn't exist error
        error_msg = str(e).lower()
        if 'relation "contact_submissions" does not exist' in error_msg or 'table "contact_submissions" doesn\'t exist' in error_msg or 'no such table: contact_submissions' in error_msg:
            raise Exception("Contact submissions table does not exist. Please run database migrations: 'alembic upgrade head'")
        
        raise Exception(f"Failed to create contact submission: {str(e)}")


async def get_contact_submission_by_id(
    session: AsyncSession, 
    submission_id: int
) -> Optional[ContactSubmission]:
    """
    Get a contact submission by ID.
    
    Args:
        session: Database session
        submission_id: ID of the submission
        
    Returns:
        ContactSubmission or None if not found
    """
    try:
        from sqlalchemy.future import select
        result = await session.execute(select(ContactSubmission).where(ContactSubmission.id == submission_id))
        submission = result.scalar_one_or_none()
        if submission:
            await logger.ainfo(f"Retrieved contact submission with ID {submission_id}")
        return submission
    except Exception:
        tb_str = traceback.format_exc()
        await logger.aerror(f"Error retrieving contact submission with ID {submission_id}", error=tb_str)
        raise


async def get_all_contact_submissions(
    session: AsyncSession, 
    limit: int = 100
) -> list[ContactSubmission]:
    """
    Get all contact submissions (admin function).
    
    Args:
        session: Database session
        limit: Maximum number of submissions to retrieve
        
    Returns:
        List of ContactSubmission objects
    """
    try:
        from sqlalchemy.future import select
        result = await session.execute(
            select(ContactSubmission)
            .order_by(ContactSubmission.created_at.desc())
            .limit(limit)
        )
        submissions = result.scalars().all()
        await logger.ainfo(f"Retrieved {len(submissions)} contact submissions")
        return submissions
    except Exception:
        tb_str = traceback.format_exc()
        await logger.aerror("Error retrieving contact submissions", error=tb_str)
        raise


async def _send_contact_notification_email(contact_submission: ContactSubmission):
    """
    Send notification email to admin about new contact submission.
    
    Args:
        contact_submission: The contact submission to notify about
    """
    try:
        # Get admin email from environment
        admin_email = os.getenv("ADMIN_EMAIL")
        if not admin_email:
            await logger.aerror("ADMIN_EMAIL environment variable not set")
            return False
        
        # Initialize email service
        email_service = EmailService()
        
        # Format submission date
        if contact_submission.created_at:
            submission_date = contact_submission.created_at.strftime("%B %d, %Y at %I:%M %p")
        else:
            submission_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        # Create email content
        subject = f"🔔 New Contact Form Submission - {contact_submission.subject}"
        
        # HTML email content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                    New Contact Form Submission
                </h2>
                
                <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1e40af;">Contact Information</h3>
                    <p><strong>Name:</strong> {contact_submission.first_name} {contact_submission.last_name}</p>
                    <p><strong>Email:</strong> <a href="mailto:{contact_submission.email}">{contact_submission.email}</a></p>
                    {f'<p><strong>Phone:</strong> {contact_submission.phone}</p>' if contact_submission.phone else ''}
                    <p><strong>Subject:</strong> {contact_submission.subject}</p>
                    <p><strong>Submitted:</strong> {submission_date}</p>
                </div>
                
                <div style="background-color: #fefefe; padding: 20px; border-left: 4px solid #2563eb; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1e40af;">Message</h3>
                    <p style="white-space: pre-wrap;">{contact_submission.message}</p>
                </div>
                
                <div style="margin-top: 30px; padding: 15px; background-color: #ecfccb; border-radius: 8px;">
                    <p style="margin: 0; font-size: 14px; color: #365314;">
                        <strong>Next Steps:</strong> Please respond to this inquiry within 24 hours to maintain good customer service.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text email content
        text_content = f"""
New Contact Form Submission

Contact Information:
Name: {contact_submission.first_name} {contact_submission.last_name}
Email: {contact_submission.email}
{f'Phone: {contact_submission.phone}' if contact_submission.phone else ''}
Subject: {contact_submission.subject}
Submitted: {submission_date}

Message:
{contact_submission.message}

Next Steps: Please respond to this inquiry within 24 hours to maintain good customer service.
        """
        
        # Send the email
        success = email_service.send_email(
            to_address=admin_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        if success:
            await logger.ainfo(
                f"Contact notification email sent to admin: {admin_email}",
                submission_id=contact_submission.id
            )
        else:
            await logger.aerror(
                f"Failed to send contact notification email to admin: {admin_email}",
                submission_id=contact_submission.id
            )
        
        return success
        
    except Exception:
        tb_str = traceback.format_exc()
        await logger.aerror(
            f"Error sending contact notification email",
            error=tb_str,
            submission_id=contact_submission.id
        )
        return False 