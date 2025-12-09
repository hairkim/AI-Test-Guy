from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from app.database import Base
from uuid import UUID


class FlaggedQuestion(Base):
    __tablename__ = "flagged_questions"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("sat_questions.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))