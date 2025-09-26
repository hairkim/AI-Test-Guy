from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SATQuestion
from app.auth import get_current_user
from app.practice_tutor import PracticeTutorRequest, PracticeTutorResponse, StepByStepRequest, StepByStepResponse
from app.practice_tutor import PracticeQuestionTutor
import os
from app.api import tb, WOLFRAM_APPID

practice_tutor_router = APIRouter(prefix="/api/practice-tutor", tags=["Practice Tutor"])

#configure once
tutor = PracticeQuestionTutor(tb["llm_wrapper"], WOLFRAM_APPID)


@practice_tutor_router.post("/ask", response_model=PracticeTutorResponse)
async def ask_practice_tutor(
    request: PracticeTutorRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Main endpoint for students to ask questions about specific practice problems
    """
    # Get the question from database
    question = db.query(SATQuestion).filter(SATQuestion.id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Get guidance from tutor
    response = tutor.get_contextual_guidance(question, request.user_question, request.chat_history)
    
    return PracticeTutorResponse(
        response=response,
        question_context={
            "id": question.id,
            "section": question.section,
            "domain": question.domain,
            "difficulty": question.difficulty
        },
        hints_used=len([msg for msg in request.chat_history if "hint" in msg.get("tutor", "").lower()]),
        difficulty_level=question.difficulty
    )

@practice_tutor_router.post("/step", response_model=StepByStepResponse)
async def get_step_by_step(
    request: StepByStepRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint for structured step-by-step help
    """
    # Get the question from database
    question = db.query(SATQuestion).filter(SATQuestion.id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Get step-by-step guidance
    response = tutor.provide_step_by_step(question, request.step_requested, request.user_attempt)
    
    return StepByStepResponse(**response)

@practice_tutor_router.get("/question-context/{question_id}")
async def get_question_context(
    question_id: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get question details for the frontend (without the correct answer)
    """
    question = db.query(SATQuestion).filter(SATQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {
        "id": question.id,
        "section": question.section,
        "domain": question.domain,
        "difficulty": question.difficulty,
        "question_text": question.question_text,
        "paragraph": question.paragraph,
        "choices": {
            "A": question.choice_a,
            "B": question.choice_b,
            "C": question.choice_c,
            "D": question.choice_d
        }
        # Note: NOT including correct_answer or explanation
    }