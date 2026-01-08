# Sample Module Tutorial: Fitness Goals

This tutorial demonstrates how to create a complete module in the backend following our established patterns. We'll build a "Fitness Goals" module that includes CRUD operations and AI-powered goal recommendations.

## Module Overview

The `fitness_goals` module will:
- Manage user fitness goals (CRUD operations)
- Provide AI-powered goal recommendations
- Follow the established module structure
- Demonstrate relationships with the User model

## Step 1: Create Module Structure

Create the following directory structure in `/backend/src/fitness_goals/`:

`
backend/src/fitness_goals/
 __init__.py
 models.py
 schemas.py
 service.py
─ router.py
 prompts.py
 ai_service.py
`

## Step 2: Define the Database Model

**File: `/backend/src/fitness_goals/models.py`**

`python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

class FitnessGoal(Base):
    __tablename__ = "fitness_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    target_value = Column(String(100))  # e.g., "10kg", "30 minutes", "5 times/week"
    category = Column(String(50))  # e.g., "weight_loss", "strength", "cardio"
    priority = Column(String(20), default="medium")  # low, medium, high
    is_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    target_date = Column(DateTime(timezone=True))
    
    # Relationship with User
    user = relationship("User", back_populates="fitness_goals")
`

## Step 3: Update User Model

**Add to `/backend/src/auth/models.py`** (in the User class):

`python
# Add this relationship to the User class
fitness_goals = relationship("FitnessGoal", back_populates="user")
`

## Key Patterns Demonstrated

1. **Model Relationships**: ForeignKey relationship with User model
2. **Comprehensive CRUD**: Full create, read, update, delete operations
3. **Pagination**: Proper pagination with skip/limit parameters
4. **Input Validation**: Pydantic schemas with validation rules
5. **Error Handling**: Proper HTTP exceptions and status codes
6. **AI Integration**: LangChain LLM integration with async operations
7. **Modular Design**: Separation of concerns across files
8. **Authentication**: Protected endpoints requiring user authentication

This sample module demonstrates all the key patterns you'll need when building new features in the backend. Use this as a template and modify it according to your specific requirements.
