from pydantic import BaseModel, root_validator
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index, Boolean, UniqueConstraint, CheckConstraint, DateTime, func, text, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from .database import Base

class SurvivalSession(Base):
    __tablename__ = "survival_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session configuration
    difficulty = Column(String, nullable=False)
    section = Column(String, nullable=False)
    domain = Column(String, nullable=True)
    
    # Final results only (saved when game ends)
    questions_answered = Column(Integer, nullable=False)
    questions_correct = Column(Integer, nullable=False)
    
    # Question tracking
    question_ids = Column(JSONB)  # All questions shown
    answers = Column(JSONB)  # Full answer history with is_correct
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=text("timezone('UTC', now())"))
    ended_at = Column(DateTime(timezone=True), server_default=text("timezone('UTC', now())"))
    
    __table_args__ = (
        Index("ix_survival_sessions_user_id", "user_id"),
        Index("ix_survival_sessions_difficulty", "difficulty"),
    )
    
    @property
    def accuracy(self):
        if self.questions_answered == 0:
            return 0
        return (self.questions_correct / self.questions_answered) * 100