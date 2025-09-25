from posix import truncate
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Any
from datetime import datetime, timezone
from app.database import get_db
from app.models import SATQuestion, MockExam, MockExamQuestion, MockExamSection
from app.sat_route_helpers import (
    generate_section_questions,
    get_difficulty_distribution,
    questions_to_response,
    get_module_questions,
    determine_module2_difficulty_points,
    generate_module2_questions,
    create_mock_exam_sections,
    get_section_module_questions,
    calculate_section_score,
    QuestionResponse,
    QuestionWithAnswer,
    MockExamRequest,
    MockExamResponse,
    SubmitTestRequest,
    SubmitTestResponse
)
from app.auth import get_current_user

# Create router
sat_router = APIRouter(prefix="/api/sat", tags=["SAT Questions"])

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
        questions=questions_to_response(starting_section_questions, include_answers=False),
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
    
    # Get the exam and section
    exam = db.query(MockExam).filter(MockExam.id == request.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    section = next((s for s in exam.sections if s.section_type == section_type), None)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section {section_type} not found")
    
    # Get questions for this module
    questions = get_section_module_questions(db, section, module_number)
    
    # Score the module
    correct_count = 0
    module_results = []
    
    for exam_question in questions:
        user_answer = request.answers.get(exam_question.sat_question_id)
        sat_question = db.query(SATQuestion).filter_by(id=exam_question.sat_question_id).first()
        
        is_correct = user_answer == sat_question.correct_answer
        exam_question.user_answer = user_answer
        exam_question.is_correct = is_correct
        
        if module_number == 1:
            module_results.append({
                'is_correct': is_correct,
                'difficulty': sat_question.difficulty
            })
        
        if is_correct:
            correct_count += 1
    
    # Update section based on module
    if module_number == 1:
        section.module1_completed = True
        section.module1_correct = correct_count
        
        # Determine module 2 difficulty
        difficulty_level = determine_module2_difficulty_points(module_results)
        section.module2_difficulty_assigned = difficulty_level
        
        # Generate module 2 questions
        module2_questions = generate_module2_questions(db, section, difficulty_level)
        section.module2_questions = [q.id for q in module2_questions]
        section.module2_total = len(module2_questions)
        
        # Create module 2 question associations
        for i, question in enumerate(module2_questions):
            mock_exam_question = MockExamQuestion(
                section_id=section.id,
                sat_question_id=question.id,
                module_number=2,
                question_order=i + 1
            )
            db.add(mock_exam_question)
        
        db.commit()
        
        return {
            "section_type": section_type,
            "module": module_number,
            "correct": correct_count,
            "total": len(questions),
            "percentage": (correct_count / len(questions)) * 100,
            "module2_difficulty": difficulty_level,
            "module2_questions": questions_to_response(module2_questions, include_answers=True),
            "message": f"Module 1 complete. Module 2 will be {'more challenging' if difficulty_level == 'higher' else 'easier'}."
        }
    
    elif module_number == 2:
        section.module2_completed = True
        section.module2_correct = correct_count
        section.total_correct = section.module1_correct + section.module2_correct
        
        # Calculate section score
        section.section_score = calculate_section_score(section)
        
        # Mark completion time
        if request.time_ended:
            section.completed_at = datetime.fromisoformat(request.time_ended.replace('Z', '+00:00'))

        db.flush()
        
        # Check if entire exam is complete
        if exam.is_completed:
            exam.completed_at = datetime.utcnow()
            if exam.exam_type == "full_exam":
                # Calculate combined SAT score
                math_score = exam.math_section.section_score if exam.math_section else 0
                english_score = exam.english_section.section_score if exam.english_section else 0
                exam.total_score = math_score + english_score
            else:
                exam.total_score = section.section_score
        
        db.commit()
        
        return {
            "section_type": section_type,
            "module": module_number,
            "section_score": section.section_score,
            "total_correct": section.total_correct,
            "total_questions": section.total_questions,
            "percentage": section.percentage_correct,
            "exam_completed": exam.is_completed,
            "total_exam_score": exam.total_score if exam.is_completed else None
        }

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
        "questions": questions_to_response(questions, include_answers=False)
    }
    


# @sat_router.get("/mock-exam/adaptive/{exam_type}")
# def generate_adaptive_mock_exam(
#     exam_type: str,
#     user_performance_level: str = Query("medium", description="easy, medium, or hard based on user's typical performance"),
#     db: Session = Depends(get_db)
# ):
#     """Generate an adaptive mock exam that adjusts difficulty based on user performance level"""
    
#     # Adaptive difficulty distribution based on user's level
#     if user_performance_level == "easy":
#         # More easy questions for struggling students
#         if exam_type == "math_only":
#             difficulty_mix = {"Easy": 15, "Medium": 20, "Hard": 9}
#         else:
#             difficulty_mix = {"Easy": 18, "Medium": 25, "Hard": 11}
#     elif user_performance_level == "hard":
#         # More challenging distribution for advanced students  
#         if exam_type == "math_only":
#             difficulty_mix = {"Easy": 6, "Medium": 20, "Hard": 18}
#         else:
#             difficulty_mix = {"Easy": 8, "Medium": 25, "Hard": 21}
#     else:
#         # Standard distribution for average students
#         difficulty_mix = get_difficulty_distribution(exam_type)
    
#     all_questions = []
    
#     # Generate questions based on exam type
#     if exam_type in ["math_only", "full_sat"]:
#         math_questions = generate_section_questions(db, "Math", difficulty_mix)
#         all_questions.extend(math_questions)
    
#     if exam_type in ["english_only", "full_sat"]:
#         english_questions = generate_section_questions(db, "English", difficulty_mix)
#         all_questions.extend(english_questions)
    
#     # Create mock exam record with adaptive config
#     mock_exam = MockExam(
#         exam_type=f"{exam_type}_adaptive",
#         total_questions=len(all_questions),
#         config={
#             "difficulty_mix": difficulty_mix,
#             "user_performance_level": user_performance_level,
#             "adaptive": True
#         }
#     )
#     db.add(mock_exam)
#     db.flush()
    
#     # Create question associations
#     for i, question in enumerate(all_questions):
#         mock_exam_question = MockExamQuestion(
#             mock_exam_id=mock_exam.id,
#             sat_question_id=question.id,
#             question_order=i + 1
#         )
#         db.add(mock_exam_question)
    
#     db.commit()
    
#     time_limits = {"math_only": 70, "english_only": 64, "full_sat": 134}
    
#     return MockExamResponse(
#         exam_id=str(mock_exam.id),
#         exam_type=exam_type,
#         total_questions=len(all_questions),
#         questions=questions_to_response(all_questions, include_answers=False),
#         time_limit_minutes=time_limits.get(exam_type, 60)
#     )
    