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
from datetime import datetime, timezone

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
    user = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """
    Save a completed survival session (called when user loses all 3 lives).
    Frontend sends all the data accumulated during the session.
    """
    
    question_ids = [answer.get("question_id") for answer in request.answers if answer.get("question_id")]
    questions = db.query(SATQuestion).filter(SATQuestion.id.in_(question_ids)).all()
    question_by_id = {question.id: question for question in questions}

    validated_answers = []
    questions_correct = 0

    for answer in request.answers:
        question_id = answer.get("question_id")
        question = question_by_id.get(question_id)
        if not question:
            continue

        user_answer = answer.get("user_answer")
        is_correct = user_answer == question.correct_answer
        if is_correct:
            questions_correct += 1

        validated_answers.append({
            "question_id": question_id,
            "user_answer": user_answer,
            "correct_answer": question.correct_answer,
            "is_correct": is_correct,
        })

    questions_answered = len(validated_answers)
    
    # Create session record
    session = SurvivalSession(
        user_id=user.id,
        difficulty=request.difficulty,
        section=request.section,
        domain=request.domain,
        questions_answered=questions_answered,
        questions_correct=questions_correct,
        question_ids=[answer["question_id"] for answer in validated_answers],
        answers=validated_answers,
        started_at=request.start_time,
        ended_at=datetime.now(timezone.utc)
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
    difficulty: str,
    section: str,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard showing each user's BEST session only.
    One entry per user, ranked by their highest questions_correct.
    """
    
    # Subquery: Get each user's best score for this difficulty/section
    best_scores = db.query(
        SurvivalSession.user_id,
        func.max(SurvivalSession.questions_correct).label('max_correct')
    ).filter(
        SurvivalSession.difficulty == difficulty,
        SurvivalSession.section == section
    ).group_by(
        SurvivalSession.user_id
    ).subquery()
    
    # Main query: Get the full session details for those best scores
    leaderboard = db.query(
        SurvivalSession,
        User
    ).join(
        User, SurvivalSession.user_id == User.id
    ).join(
        best_scores,
        (SurvivalSession.user_id == best_scores.c.user_id) &
        (SurvivalSession.questions_correct == best_scores.c.max_correct)
    ).filter(
        SurvivalSession.difficulty == difficulty,
        SurvivalSession.section == section
    ).order_by(
        SurvivalSession.questions_correct.desc(),
        SurvivalSession.questions_answered.asc(),
        SurvivalSession.ended_at.asc()  # If still tied, earliest wins
    ).limit(limit).all()
    
    return {
        "leaderboard": [
            {
                "rank": i + 1,
                "user_id": session.user_id,
                "user_name": user.name,
                "questions_correct": session.questions_correct,
                "questions_answered": session.questions_answered,
                "difficulty": session.difficulty,
                "section": session.section,
                "date": session.ended_at.strftime("%Y-%m-%d") if session.ended_at else None
            }
            for i, (session, user) in enumerate(leaderboard)
        ]
    }
