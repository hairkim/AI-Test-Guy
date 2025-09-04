from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.database import get_db
from app.models import SATQuestion, MockExam, MockExamQuestion
from app.sat_route_helpers import (
    generate_section_questions,
    get_difficulty_distribution,
    questions_to_response,
    get_module_questions,
    determine_module2_difficulty_points,
    generate_module2_questions,
    score_exam,
    QuestionResponse,
    QuestionWithAnswer,
    MockExamRequest,
    MockExamResponse,
    SubmitTestRequest,
    SubmitTestResponse
)

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
    
    difficulty_mix = get_difficulty_distribution(request.exam_type, request.difficulty_mix)
    all_questions = []
    
    # Generate questions based on exam type
    if request.exam_type in ["math_only", "full_sat"]:
        math_questions = generate_section_questions(db, "Math", difficulty_mix) #returns List[SATQuestion]
        all_questions.extend(math_questions)
    
    if request.exam_type in ["english_only", "full_sat"]:
        english_questions = generate_section_questions(db, "English", difficulty_mix)
        all_questions.extend(english_questions)
    
    # Create mock exam record
    mock_exam = MockExam(
        exam_type=request.exam_type,
        user_id=request.user_id,
        total_questions=len(all_questions),
        module1_questions=[question.id for question in all_questions],
        
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
        module=1,
        total_questions=len(all_questions),
        questions=questions_to_response(all_questions, include_answers=True), #type List[QuestionResponse]
        time_limit_minutes=time_limits.get(request.exam_type, 60)
    )

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
        module=mock_exam.module,
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


@sat_router.post("/submit_test/{module_number}")
def submit_test(module_number: int, request: SubmitTestRequest, db: Session = Depends(get_db)):
    """Submit a mock exam"""
    exam = db.query(MockExam).filter(MockExam.id == request.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    questions = get_module_questions(db, exam, module_number)

    #count how many questions were correct
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

    if module_number == 1:
        exam.module1_completed = True
        exam.module1_correct = correct_count
        exam.module1_total = len(questions)

        difficulty_level = determine_module2_difficulty_points(module_results)

        # Generate module 2 questions
        module2_questions = generate_module2_questions(db, exam, difficulty_level) #returns List[SATQuestion]
        print("submit test in module 2 the length of questions for module 2: " + str(len(module2_questions)))
        exam.module2_questions=[question.id for question in module2_questions]
        
        # Create MockExamQuestion records for module 2
        current_order = max([eq.question_order for eq in exam.questions]) + 1
        module2_exam_questions = []
        
        for question in module2_questions:
            mock_exam_question = MockExamQuestion(
                mock_exam_id=exam.id,
                sat_question_id=question.id,
                question_order=current_order
            )
            db.add(mock_exam_question)
            module2_exam_questions.append(mock_exam_question)
            current_order += 1
        
        db.commit()
        
        # After commit, the MockExamQuestion objects will have their relationships loaded
        # Convert the SATQuestion objects (accessed via relationship) to response format
        module2_sat_questions = [meq.sat_question for meq in module2_exam_questions]
        
        return {
            "module": module_number,
            "correct": correct_count,
            "total": len(module2_sat_questions),
            "percentage": (correct_count / len(module2_sat_questions)) * 100,
            "module2_difficulty": difficulty_level,
            "module2_questions": questions_to_response(module2_sat_questions, include_answers=True),
            "message": f"Module 1 complete. Module 2 will be {'more challenging' if difficulty_level == 'higher' else 'easier'}."
        }
    elif module_number == 2:
        print('module2')
        #will return score based on this metric:
        #let C be number of correct answers
        #score_easy = round_to_nearest_10( 200 + (C/44) * (690 - 200) )
        #score_hard = round_to_nearest_10( 300 + (C/44) * (800 - 300) )

        exam.module2_completed = True
        exam.module2_correct = correct_count
        exam.module2_total = len(questions)

        exam.score, total_correct = score_exam(exam)
        db.commit()
        return {
            "score": exam.score,
            "percentage": (total_correct / 44) * 100
        }

    else:
        raise HTTPException(status_code=400, detail="Invalid module number. Must be 1 or 2.")
    
    