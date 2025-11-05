from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.survival_models import SurvivalSession
from app.models import SATQuestion, User
from sqlalchemy import func
from typing import Optional
from app.sat_route_helpers import QuestionResponse
from app.survival_routes_helpers import (
    get_random_question_excluding,
    QuestionWithAnswer,
    SaveSurvivalSessionRequest,
    SurvivalQuestionRequest
)
from app.auth import get_current_user, get_current_user_db
from datetime import datetime

survival_router = APIRouter(prefix="/api/survival", tags=["Survival Questions API"])

@survival_router.post("/question", response_model=QuestionWithAnswer)
def get_survival_question(
    request: SurvivalQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Get a random question for survival mode.
    Frontend manages lives and question tracking.
    Returns question with answer for instant frontend validation.
    """
    
    # Validate inputs
    if request.difficulty not in ["Easy", "Medium", "Hard"]:
        raise HTTPException(status_code=400, detail="Invalid difficulty")
    
    if request.section and request.section not in ["Math", "English"]:
        raise HTTPException(status_code=400, detail="Invalid section")
    
    # Get question excluding already shown ones
    question = get_random_question_excluding(
        db=db,
        difficulty=request.difficulty,
        excluded_ids=request.excluded_question_ids,
        section=request.section,
        domain=request.domain
    )
    
    if not question:
        raise HTTPException(
            status_code=404,
            detail="No more questions available with these criteria"
        )
    
    # Return question WITH answer for frontend validation
    return QuestionWithAnswer(
        id=question.id,
        section=question.section,
        domain=question.domain,
        difficulty=question.difficulty,
        question_text=question.question_text,
        paragraph=question.paragraph,
        choices={
            "A": question.choice_a,
            "B": question.choice_b,
            "C": question.choice_c,
            "D": question.choice_d
        },
        correct_answer=question.correct_answer,
        explanation=question.explanation
    )


@survival_router.post("/session/save")
def save_survival_session(
    request: SaveSurvivalSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Save a completed survival session (called when user loses all 3 lives).
    Frontend sends all the data accumulated during the session.
    """
    
    # Verify user exists (optional but recommended)
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create session record
    session = SurvivalSession(
        user_id=request.user_id,
        difficulty=request.difficulty,
        section=request.section,
        domain=request.domain,
        questions_answered=request.questions_answered,
        questions_correct=request.questions_correct,
        question_ids=request.question_ids,
        answers=request.answers,
        ended_at=datetime.now()
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "session_id": str(session.id),
        "message": "Session saved successfully",
        "stats": {
            "questions_answered": session.questions_answered,
            "questions_correct": session.questions_correct,
            "accuracy": session.accuracy
        }
    }


@survival_router.get("/stats/{user_id}")
def get_user_survival_stats(
    user_id: str,
    difficulty: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get user's survival mode statistics"""
    
    query = db.query(SurvivalSession).filter(SurvivalSession.user_id == user_id)
    
    if difficulty:
        query = query.filter(SurvivalSession.difficulty == difficulty)
    
    if section:
        query = query.filter(SurvivalSession.section == section)
    
    sessions = query.order_by(SurvivalSession.ended_at.desc()).all()
    
    if not sessions:
        return {
            "total_sessions": 0,
            "best_score": 0,
            "average_accuracy": 0,
            "total_questions_answered": 0
        }
    
    return {
        "total_sessions": len(sessions),
        "best_score": max(s.questions_correct for s in sessions),
        "average_accuracy": sum(s.accuracy for s in sessions) / len(sessions),
        "total_questions_answered": sum(s.questions_answered for s in sessions),
        "recent_sessions": [
            {
                "id": str(s.id),
                "difficulty": s.difficulty,
                "section": s.section,
                "questions_answered": s.questions_answered,
                "questions_correct": s.questions_correct,
                "accuracy": s.accuracy,
                "ended_at": s.ended_at.isoformat()
            }
            for s in sessions[:10]  # Last 10 sessions
        ]
    }

@survival_router.get("/leaderboard")
def get_survival_leaderboard(
    difficulty: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get leaderboard - Database does the sorting, not the application"""
    
    query = db.query(SurvivalSession).join(User)
    
    if difficulty:
        query = query.filter(SurvivalSession.difficulty == difficulty)
    
    if section:
        query = query.filter(SurvivalSession.section == section)
    
    # ✅ Database sorts and limits - only retrieves top N records
    sessions = query.order_by(
        SurvivalSession.questions_correct.desc(),
        SurvivalSession.questions_answered.asc()
    ).limit(limit).all()  # Only gets 10-100 records, not millions!
    
    return {"leaderboard": sessions}