from app.models import SATQuestion
from app.sat_route_helpers import QuestionWithAnswer
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime

class SurvivalQuestionRequest(BaseModel):
    difficulty: str
    section: Optional[str] = None
    domain: Optional[str] = None
    excluded_question_ids: List[str] = []  # Questions already shown


class SurvivalQuestionResponse(BaseModel):
    question: QuestionWithAnswer  # Include answer for frontend validation


class SaveSurvivalSessionRequest(BaseModel):
    user_id: str
    difficulty: str
    section: str
    domain: Optional[str] = None
    questions_answered: int
    questions_correct: int
    question_ids: List[str]
    answers: List[Dict]  # [{"question_id": "...", "user_answer": "A", "is_correct": true}, ...]
    start_time: datetime


def get_random_question_excluding(
    db: Session,
    difficulty: str,
    excluded_ids: List[str],
    section: Optional[str] = None,
    domain: Optional[str] = None
) -> Optional[SATQuestion]:
    """Get a random question that's not in the excluded list"""
    
    query = db.query(SATQuestion).filter(
        SATQuestion.difficulty == difficulty,
        ~SATQuestion.id.in_(excluded_ids) if excluded_ids else True
    )
    
    if section:
        query = query.filter(SATQuestion.section == section)
    
    if domain:
        query = query.filter(SATQuestion.domain == domain)
    
    question = query.order_by(func.random()).first()
    
    return question