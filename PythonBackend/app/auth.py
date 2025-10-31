from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.security import HTTPBearer
from supabase import create_client
import jwt
import os
import uuid
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
security = HTTPBearer()

user_router = APIRouter(prefix="/api/users", tags=["Users"])

class UserSyncRequest(BaseModel):
    id: str  # UUID from Supabase
    name: str
    email: str
    picture_url: str = None
    created_at: datetime.datetime

def get_current_user(token: str = Depends(security)):
    try:
        # Verify the JWT token with Supabase
        user = supabase.auth.get_user(token.credentials)
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@user_router.post("/sync")
def sync_user(request: UserSyncRequest, db: Session = Depends(get_db)):
    """Create or update user in local database from Supabase auth"""
    
    user_uuid = uuid.UUID(request.id)
    
    # Try to get existing user
    user = db.query(User).filter(User.id == user_uuid).first()
    
    if user:
        # Update existing user info
        user.name = request.name
        user.email = request.email
        user.picture_url = request.picture_url
        
        print(f"✅ Updated existing user: {user.email}")
    else:
        # Create new user
        user = User(
            id=user_uuid,
            name=request.name,
            email=request.email,
            picture_url=request.picture_url,
            created_at=request.created_at,
            level=1,
            points=0
        )
        db.add(user)
        print(f"✅ Created new user: {user.email}")
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "picture_url": user.picture_url,
        "level": user.level,
        "points": user.points
    }

def get_current_user_db(token: str = Depends(security), db: Session = Depends(get_db)) -> User:
    """Get database User model (for routes that need points, level, etc.)"""
    try:
        # Verify the JWT token with Supabase
        supabase_user = supabase.auth.get_user(token.credentials)
        
        # Get the actual user from YOUR database using the email
        user_email = supabase_user.user.email
        
        # Query your local database for the User
        db_user = db.query(User).filter(User.email == user_email).first()
        
        if not db_user:
            raise HTTPException(
                status_code=404, 
                detail="User not found in database. Please sync user first."
            )
        
        return db_user
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

