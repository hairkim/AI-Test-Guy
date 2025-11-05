from posix import truncate
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Any
from datetime import datetime, timezone, date
from app.database import get_db
from app.models import SATQuestion, MockExam, MockExamQuestion, MockExamSection, CollegeSATScore, DailyPracticeSet
from app.sat_route_helpers import (
    generate_section_questions,
    get_difficulty_distribution,
    questions_to_response,
    create_mock_exam_sections,
    get_exam_and_sections,
    score_module,
    handle_module1_submission,
    handle_module2_submission,
    QuestionResponse,
    QuestionWithAnswer,
    MockExamRequest,
    MockExamResponse,
    SubmitTestRequest,
    SubmitTestResponse
)
from app.auth import get_current_user, get_current_user_db
from app.dailytaskhelperfunctions import update_user_performance

# Create router
sat_router = APIRouter(prefix="/api/sat", tags=["SAT Questions"])

# API Routes

@sat_router.get("/questions/random", response_model=List[QuestionResponse])
def get_random_questions(
    section: str = Query(..., description="Math or English"),
    count: int = Query(10, ge=1, le=100, description="Number of questions to return"),
    difficulty: Optional[str] = Query(None, description="Easy, Medium, or Hard"),
    domain: Optional[str] = Query(None, description="Specific domain to filter by"),
    user = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Get random questions for practice - same set per day"""
    
    today = date.today()
    
    # Check if user already has a practice set for today with these filters
    existing_set = db.query(DailyPracticeSet).filter(
        DailyPracticeSet.user_id == user.id,
        DailyPracticeSet.date == today,
        DailyPracticeSet.section == section,
        DailyPracticeSet.difficulty == difficulty,
        DailyPracticeSet.domain == domain
    ).first()
    
    if existing_set:
        # Return the existing set of questions
        questions = db.query(SATQuestion).filter(
            SATQuestion.id.in_(existing_set.question_ids)   
        ).all()
        
        # Sort questions to match the original order
        question_dict = {q.id: q for q in questions}
        questions = [question_dict[qid] for qid in existing_set.question_ids if qid in question_dict]
        
    else:
        # Generate new random questions
        query = db.query(SATQuestion).filter(SATQuestion.section == section)
        
        if difficulty:
            query = query.filter(SATQuestion.difficulty == difficulty)
        
        if domain:
            query = query.filter(SATQuestion.domain == domain)
        
        # Get random questions
        questions = query.order_by(func.random()).limit(count).all()
        
        if not questions:
            raise HTTPException(status_code=404, detail="No questions found matching criteria")
        
        # Save this set for the day
        question_ids = [q.id for q in questions]
        new_set = DailyPracticeSet(
            user_id=user.id,
            date=today,
            section=section,
            difficulty=difficulty,
            domain=domain,
            question_ids=question_ids
        )
        db.add(new_set)
        db.commit()
    
    return questions_to_response(questions, include_answers=True)


@sat_router.post("/mock-exam/generate", response_model=MockExamResponse)
def generate_mock_exam(
    request: MockExamRequest,
    db: Session = Depends(get_db)
):
    """Generate a complete mock exam with balanced question distribution"""
    
    # Create the main exam record
    mock_exam = MockExam(
        exam_type=request.exam_type,
        user_id=request.user_id,
        started_at=datetime.fromisoformat(request.started_at.replace('Z', '+00:00')) if request.started_at else datetime.utcnow(),
        config={"difficulty_mix": request.difficulty_mix}
    )
    db.add(mock_exam)
    db.flush()  # Get exam ID
    
    # Create sections based on exam type
    sections = create_mock_exam_sections(db, mock_exam, request.exam_type)
    db.flush()  # Get section IDs
    
    # Generate module 1 questions for ALL sections (as before)
    all_questions = []
    starting_section_questions = []
    
    for section in sections:
        difficulty_mix = get_difficulty_distribution(
            section.section_type, 
            module=1, 
            custom_mix=request.difficulty_mix
        )
        
        # Generate module 1 questions
        module1_questions = generate_section_questions(db, section.section_type, difficulty_mix)
        section.module1_questions = [q.id for q in module1_questions]
        section.module1_total = len(module1_questions)
        
        # Create question associations
        for i, question in enumerate(module1_questions):
            mock_exam_question = MockExamQuestion(
                section_id=section.id,
                sat_question_id=question.id,
                module_number=1,
                question_order=i + 1
            )
            db.add(mock_exam_question)
        
        all_questions.extend(module1_questions)
        
        # For full_exam, English goes first; otherwise use first section
        if (request.exam_type == "full_exam" and section.section_type == "English") or \
           (request.exam_type != "full_exam" and section == sections[0]):
            starting_section_questions = module1_questions
            starting_section = section
    
    # Calculate total questions across all sections
    total_questions = sum(section.total for section in sections)
    
    db.commit()
    
    # Return only the starting section's questions
    return MockExamResponse(
        exam_id=str(mock_exam.id),
        exam_type=request.exam_type,
        sections=[section.section_type for section in sections],
        section_type=starting_section.section_type,
        module=1,
        module_questions=starting_section.module1_total,
        total_questions=total_questions,
        questions=questions_to_response(starting_section_questions, include_answers=True),
        eng_module_time_limit=32,
        math_module_time_limit=35,
        break_time_limit=10
    )

@sat_router.get("/mock-exam/history")
def get_mock_exam_history(user: Any = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a user's mock exam history with sections, sorted by most recent"""
    from sqlalchemy.orm import joinedload
    
    user_id = user.user.id
    
    exams = db.query(MockExam)\
        .options(joinedload(MockExam.sections))\
        .filter(MockExam.user_id == user_id)\
        .order_by(MockExam.created_at.desc())\
        .all()
    
    return exams

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
    
    
    return MockExamResponse(
        exam_id=exam_id,
        exam_type=mock_exam.exam_type,
        module=mock_exam.module,
        module_questions=len(questions),
        total_questions=exam.total_questions,
        questions=questions_to_response(questions, include_answers=False),
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

@sat_router.post("/submit_test/{section_type}/{module_number}")
def submit_test(
    section_type: str, 
    module_number: int, 
    request: SubmitTestRequest, 
    db: Session = Depends(get_db)
):
    """Submit a module for a specific section"""
    # Validate and get exam data
    exam, section = get_exam_and_sections(db, request.exam_id, section_type)
    
    # Score the module and update performance
    correct_count, module_results = score_module(
        db, section, module_number, request.answers, exam.user_id
    )
    
    # Handle module-specific logic
    if module_number == 1:
        return handle_module1_submission(
            db, section, section_type, correct_count, module_results
        )
    else:  # module_number == 2
        return handle_module2_submission(
            db, exam, section, section_type, correct_count, request.time_ended
        )

@sat_router.get("/mock-exam/section/{section_type}/module/{module_number}")
def get_section_module_questions_api(
    section_type: str, 
    module_number: int, 
    exam_id: str = Header(alias="X-Exam-ID"),
    db: Session = Depends(get_db)
):
    """Get questions for a specific module of a section"""
    
    exam = db.query(MockExam).filter(MockExam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    section = next((s for s in exam.sections if s.section_type == section_type), None)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section {section_type} not found")
    
    # Get question IDs for the module
    if module_number == 1:
        question_ids = section.module1_questions
        total_questions = section.module1_total
    elif module_number == 2:
        if not section.module1_completed:
            raise HTTPException(status_code=400, detail="Must complete module 1 first")
        question_ids = section.module2_questions
        total_questions = section.module2_total
    else:
        raise HTTPException(status_code=400, detail="Invalid module number")
    
    if not question_ids:
        raise HTTPException(status_code=404, detail="No questions found for this module")
    
    # Fetch the actual questions
    questions = db.query(SATQuestion).filter(SATQuestion.id.in_(question_ids)).all()
    
    return {
        "exam_id": exam_id,
        "section_type": section_type,
        "module": module_number,
        "total_questions": total_questions,
        "questions": questions_to_response(questions, include_answers=True)
    }
    
@sat_router.get("/colleges/recommendations/{score}")
def get_college_recommendations(
    score: int,
    safety_limit: int = Query(15, ge=5, le=50),
    target_limit: int = Query(15, ge=5, le=50),
    reach_limit: int = Query(15, ge=5, le=50),
    db: Session = Depends(get_db)
):
    """Get college recommendations: safety, target, and reach schools"""
    
    # Safety schools: score is above 75th percentile (user's score > school's max range)
    safety_schools = db.query(CollegeSATScore).filter(
        CollegeSATScore.sat_max < score - 30  # More realistic threshold
    ).order_by(CollegeSATScore.sat_max.desc()).limit(safety_limit).all()
    
    # Target schools: score is within the school's range
    target_schools = db.query(CollegeSATScore).filter(
        CollegeSATScore.sat_min <= score,
        CollegeSATScore.sat_max >= score
    ).order_by(CollegeSATScore.sat_min).limit(target_limit).all()
    
    # Reach schools: score is below 25th percentile but within reason
    reach_schools = db.query(CollegeSATScore).filter(
        CollegeSATScore.sat_min > score,
        CollegeSATScore.sat_min <= score + 150  # Increased range for more options
    ).order_by(CollegeSATScore.sat_min).limit(reach_limit).all()
    
    return {
        "user_score": score,
        "total_colleges": len(safety_schools) + len(target_schools) + len(reach_schools),
        "recommendations": {
            "safety": [college.to_dict() for college in safety_schools],
            "target": [college.to_dict() for college in target_schools],
            "reach": [college.to_dict() for college in reach_schools]
        },
        "summary": {
            "safety_count": len(safety_schools),
            "target_count": len(target_schools),
            "reach_count": len(reach_schools)
        }
    }