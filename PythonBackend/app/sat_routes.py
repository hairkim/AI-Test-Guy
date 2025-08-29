from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import random

from app.database import get_db
from app.models import SATQuestion, MockExam, MockExamQuestion

# Create router
sat_router = APIRouter(prefix="/api/sat", tags=["SAT Questions"])

# Pydantic models for request/response
class QuestionResponse(BaseModel):
    id: str
    section: str
    domain: str
    difficulty: str
    question_text: str
    paragraph: Optional[str]
    choices: Dict[str, str]
    # Don't include correct_answer in response for active tests
    
class QuestionWithAnswer(QuestionResponse):
    correct_answer: str
    explanation: str

class MockExamRequest(BaseModel):
    exam_type: str = Field(..., description="math_only, english_only, or full_sat")
    difficulty_mix: Optional[Dict[str, int]] = None
    user_id: Optional[str] = None

class MockExamResponse(BaseModel):
    exam_id: str
    exam_type: str
    total_questions: int
    questions: List[QuestionResponse]
    time_limit_minutes: int

# Utility functions
def get_difficulty_distribution(exam_type: str, custom_mix: Optional[Dict[str, int]] = None) -> Dict[str, int]:
    """Get realistic difficulty distribution for different exam types"""
    
    if custom_mix:
        return custom_mix
    
    if exam_type == "math_only":
        return {"Easy": 15, "Medium": 30, "Hard": 13}  # Total: 58 (real SAT math)
    elif exam_type == "english_only":
        return {"Easy": 12, "Medium": 30, "Hard": 10}  # Total: 52 (real SAT english)
    elif exam_type == "full_sat":
        return {"Easy": 27, "Medium": 60, "Hard": 23}  # Total: 110 (full SAT)
    else:
        return {"Easy": 5, "Medium": 10, "Hard": 5}    # Default practice

def questions_to_response(questions: List[SATQuestion], include_answers: bool = False) -> List[Dict]:
    """Convert database questions to API response format"""
    result = []
    for q in questions:
        question_data = {
            "id": q.id,
            "section": q.section,
            "domain": q.domain,
            "difficulty": q.difficulty,
            "question_text": q.question_text,
            "paragraph": q.paragraph,
            "choices": {
                "A": q.choice_a,
                "B": q.choice_b,
                "C": q.choice_c,
                "D": q.choice_d
            }
        }
        
        if include_answers:
            question_data["correct_answer"] = q.correct_answer
            question_data["explanation"] = q.explanation
            
        result.append(question_data)
    
    return result

# API Routes

@sat_router.get("/questions/random", response_model=List[QuestionResponse])
def get_random_questions(
    section: str = Query(..., description="Math or English"),
    count: int = Query(10, ge=1, le=100, description="Number of questions to return"),
    difficulty: Optional[str] = Query(None, description="Easy, Medium, or Hard"),
    domain: Optional[str] = Query(None, description="Specific domain to filter by"),
    db: Session = Depends(get_db)
):
    """Get random questions for practice"""
    
    query = db.query(SATQuestion).filter(SATQuestion.section == section)
    
    if difficulty:
        query = query.filter(SATQuestion.difficulty == difficulty)
    
    if domain:
        query = query.filter(SATQuestion.domain == domain)
    
    # Get random questions
    questions = query.order_by(func.random()).limit(count).all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found matching criteria")
    
    return questions_to_response(questions, include_answers=False)

@sat_router.post("/mock-exam/generate", response_model=MockExamResponse)
def generate_mock_exam(
    request: MockExamRequest,
    db: Session = Depends(get_db)
):
    """Generate a complete mock exam with balanced question distribution"""
    
    difficulty_mix = get_difficulty_distribution(request.exam_type, request.difficulty_mix)
    all_questions = []
    
    # Generate questions based on exam type
    if request.exam_type in ["math_only", "full_sat"]:
        math_questions = generate_section_questions(db, "Math", difficulty_mix)
        all_questions.extend(math_questions)
    
    if request.exam_type in ["english_only", "full_sat"]:
        english_questions = generate_section_questions(db, "English", difficulty_mix)
        all_questions.extend(english_questions)
    
    # Create mock exam record
    mock_exam = MockExam(
        exam_type=request.exam_type,
        user_id=request.user_id,
        total_questions=len(all_questions),
        config={"difficulty_mix": difficulty_mix}
    )
    db.add(mock_exam)
    db.flush()  # Get exam ID
    
    # Create question associations
    for i, question in enumerate(all_questions):
        mock_exam_question = MockExamQuestion(
            mock_exam_id=mock_exam.id,
            sat_question_id=question.id,
            question_order=i + 1
        )
        db.add(mock_exam_question)
    
    db.commit()
    
    # Set time limits (official Digital SAT timing from College Board)
    time_limits = {
        "math_only": 70,      # 44 questions in 70 minutes (35 min per module)
        "english_only": 64,   # 54 questions in 64 minutes (32 min per module)
        "full_sat": 134       # 98 questions in 134 minutes (70+64, no break time)
    }
    
    return MockExamResponse(
        exam_id=str(mock_exam.id),
        exam_type=request.exam_type,
        total_questions=len(all_questions),
        questions=questions_to_response(all_questions, include_answers=False),
        time_limit_minutes=time_limits.get(request.exam_type, 60)
    )

def generate_section_questions(db: Session, section: str, difficulty_mix: Dict[str, int]) -> List[SATQuestion]:
    """Generate questions for a specific section with difficulty distribution"""
    
    questions = []
    
    for difficulty, count in difficulty_mix.items():
        section_questions = db.query(SATQuestion)\
            .filter(and_(
                SATQuestion.section == section,
                SATQuestion.difficulty == difficulty
            ))\
            .order_by(func.random())\
            .limit(count)\
            .all()
        
        if len(section_questions) < count:
            # If we don't have enough questions of this difficulty, get what we can
            available = len(section_questions)
            print(f"Warning: Only {available} {difficulty} {section} questions available, requested {count}")
        
        questions.extend(section_questions)
    
    return questions

@sat_router.get("/mock-exam/{exam_id}", response_model=MockExamResponse)
def get_mock_exam(exam_id: str, db: Session = Depends(get_db)):
    """Retrieve an existing mock exam"""
    
    mock_exam = db.query(MockExam).filter(MockExam.id == exam_id).first()
    if not mock_exam:
        raise HTTPException(status_code=404, detail="Mock exam not found")
    
    # Get questions in order
    exam_questions = db.query(MockExamQuestion)\
        .filter(MockExamQuestion.mock_exam_id == exam_id)\
        .order_by(MockExamQuestion.question_order)\
        .all()
    
    questions = [eq.sat_question for eq in exam_questions]
    
    time_limits = {"math_only": 80, "english_only": 64, "full_sat": 144}
    
    return MockExamResponse(
        exam_id=exam_id,
        exam_type=mock_exam.exam_type,
        total_questions=len(questions),
        questions=questions_to_response(questions, include_answers=False),
        time_limit_minutes=time_limits.get(mock_exam.exam_type, 60)
    )

@sat_router.get("/questions/{question_id}/answer", response_model=QuestionWithAnswer)
def get_question_with_answer(question_id: str, db: Session = Depends(get_db)):
    """Get a specific question with its answer and explanation"""
    
    question = db.query(SATQuestion).filter(SATQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return questions_to_response([question], include_answers=True)[0]

@sat_router.get("/stats/overview")
def get_database_stats(db: Session = Depends(get_db)):
    """Get overview statistics of available questions"""
    
    total_questions = db.query(SATQuestion).count()
    
    # Count by section
    section_counts = db.query(SATQuestion.section, func.count())\
        .group_by(SATQuestion.section)\
        .all()
    
    # Count by difficulty
    difficulty_counts = db.query(SATQuestion.difficulty, func.count())\
        .group_by(SATQuestion.difficulty)\
        .all()
    
    # Count by domain
    domain_counts = db.query(SATQuestion.domain, func.count())\
        .group_by(SATQuestion.domain)\
        .all()
    
    return {
        "total_questions": total_questions,
        "by_section": {section: count for section, count in section_counts},
        "by_difficulty": {difficulty: count for difficulty, count in difficulty_counts},
        "by_domain": {domain: count for domain, count in domain_counts}
    }

@sat_router.get("/domains/{section}")
def get_available_domains(section: str, db: Session = Depends(get_db)):
    """Get available domains for a specific section"""
    
    domains = db.query(SATQuestion.domain)\
        .filter(SATQuestion.section == section)\
        .distinct()\
        .all()
    
    return {"section": section, "domains": [domain[0] for domain in domains]}

@sat_router.get("/mock-exam/adaptive/{exam_type}")
def generate_adaptive_mock_exam(
    exam_type: str,
    user_performance_level: str = Query("medium", description="easy, medium, or hard based on user's typical performance"),
    db: Session = Depends(get_db)
):
    """Generate an adaptive mock exam that adjusts difficulty based on user performance level"""
    
    # Adaptive difficulty distribution based on user's level
    if user_performance_level == "easy":
        # More easy questions for struggling students
        if exam_type == "math_only":
            difficulty_mix = {"Easy": 15, "Medium": 20, "Hard": 9}
        else:
            difficulty_mix = {"Easy": 18, "Medium": 25, "Hard": 11}
    elif user_performance_level == "hard":
        # More challenging distribution for advanced students  
        if exam_type == "math_only":
            difficulty_mix = {"Easy": 6, "Medium": 20, "Hard": 18}
        else:
            difficulty_mix = {"Easy": 8, "Medium": 25, "Hard": 21}
    else:
        # Standard distribution for average students
        difficulty_mix = get_difficulty_distribution(exam_type)
    
    all_questions = []
    
    # Generate questions based on exam type
    if exam_type in ["math_only", "full_sat"]:
        math_questions = generate_section_questions(db, "Math", difficulty_mix)
        all_questions.extend(math_questions)
    
    if exam_type in ["english_only", "full_sat"]:
        english_questions = generate_section_questions(db, "English", difficulty_mix)
        all_questions.extend(english_questions)
    
    # Create mock exam record with adaptive config
    mock_exam = MockExam(
        exam_type=f"{exam_type}_adaptive",
        total_questions=len(all_questions),
        config={
            "difficulty_mix": difficulty_mix,
            "user_performance_level": user_performance_level,
            "adaptive": True
        }
    )
    db.add(mock_exam)
    db.flush()
    
    # Create question associations
    for i, question in enumerate(all_questions):
        mock_exam_question = MockExamQuestion(
            mock_exam_id=mock_exam.id,
            sat_question_id=question.id,
            question_order=i + 1
        )
        db.add(mock_exam_question)
    
    db.commit()
    
    time_limits = {"math_only": 70, "english_only": 64, "full_sat": 134}
    
    return MockExamResponse(
        exam_id=str(mock_exam.id),
        exam_type=exam_type,
        total_questions=len(all_questions),
        questions=questions_to_response(all_questions, include_answers=False),
        time_limit_minutes=time_limits.get(exam_type, 60)
    )
