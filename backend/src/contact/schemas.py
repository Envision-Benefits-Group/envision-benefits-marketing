# src.contact.schemas.py

import html
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator, EmailStr


class ContactSubmissionBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    message: str

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        # Strip whitespace and sanitize HTML
        v = html.escape(v.strip())
        if len(v) > 100:
            raise ValueError('Name cannot exceed 100 characters')
        # Allow only letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        # Basic malicious pattern detection
        if any(pattern in v.lower() for pattern in ['<script', 'javascript:', 'vbscript:', 'onload=', 'onerror=']):
            raise ValueError('Invalid characters detected')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        # Sanitize and normalize email
        v = html.escape(v.strip().lower())
        # Check for suspicious patterns
        if any(pattern in v for pattern in ['<script', 'javascript:', '..']):
            raise ValueError('Invalid email format')
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            # Strip whitespace and sanitize
            v = html.escape(v.strip())
            if v:  # Only validate if not empty
                # Check for malicious patterns only
                if any(pattern in v.lower() for pattern in ['<script', 'javascript:', 'data:', 'eval(', 'onclick=']):
                    raise ValueError('Invalid phone number format')
                # Simple length check
                if len(v) > 20:
                    raise ValueError('Phone number cannot exceed 20 characters')
                # Allow digits, spaces, +, -, (), but require at least some digits
                if not re.search(r'\d', v):
                    raise ValueError('Phone number must contain at least one digit')
        return v

    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v):
        if not v or not v.strip():
            raise ValueError('Subject cannot be empty')
        v = html.escape(v.strip())
        if len(v) > 100:
            raise ValueError('Subject cannot exceed 100 characters')
        # Validate against allowed subjects from frontend
        allowed_subjects = [
            'General Inquiry',
            'Technical Support', 
            'Billing Question',
            'Partnership Opportunity',
            'Feedback'
        ]
        if v not in allowed_subjects:
            raise ValueError(f'Subject must be one of: {", ".join(allowed_subjects)}')
        return v

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        # Sanitize HTML and strip whitespace
        v = html.escape(v.strip())
        if len(v) < 10:
            raise ValueError('Message must be at least 10 characters long')
        if len(v) > 5000:
            raise ValueError('Message cannot exceed 5000 characters')
        # Check for suspicious patterns that might indicate malicious content
        suspicious_patterns = [
            '<script', 'javascript:', 'vbscript:', 'data:', 'file:',
            'onload=', 'onerror=', 'onclick=', 'onmouseover=',
            'eval(', 'setTimeout(', 'setInterval(',
            'document.cookie', 'window.location', 'document.write'
        ]
        v_lower = v.lower()
        for pattern in suspicious_patterns:
            if pattern in v_lower:
                raise ValueError('Message contains invalid content')
        return v


class ContactSubmissionCreate(ContactSubmissionBase):
    pass


class ContactSubmissionResponse(ContactSubmissionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ContactSubmissionSuccess(BaseModel):
    message: str
    submission_id: int 