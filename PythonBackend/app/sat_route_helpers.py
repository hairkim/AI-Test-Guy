from sqlalchemy import and_, func
from typing import List, Dict, Optional, Any
from app.models import SATQuestion, MockExam, MockExamQuestion, MockExamSection
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict
from fastapi import HTTPException
from datetime import datetime, timezone


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
    started_at: Optional[str] = None


class MockExamResponse(BaseModel):
    exam_id: str
    exam_type: str
    sections: Optional[List[str]] = None
    section_type: Optional[str] = None  # Which section we're currently on
    module: int
    module_questions: int
    total_questions: int
    questions: List[Dict]
    eng_module_time_limit: int = 32
    math_module_time_limit: int = 35
    break_time_limit: int = 10


class SubmitTestRequest(BaseModel):
    exam_id: str
    answers: Dict[str, str]
    module: int
    time_ended: Optional[str] = None

class SubmitTestResponse(BaseModel):
    score: int

def round_to_nearest_10(x):
    return int(round(x / 10.0) * 10)


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

# Utility functions
def get_difficulty_distribution(section_type: str, module: int = 1, custom_mix: Optional[Dict[str, int]] = None) -> Dict[str, int]:
    """Get realistic difficulty distribution for different exam types"""
    
    if custom_mix:
        return custom_mix
    
    if section_type == "Math":
        return {"Easy": 7, "Medium": 10, "Hard": 5}  # 22 -> 7, 10, 5
    elif section_type == "English":
        return {"Easy": 6, "Medium": 16, "Hard": 5}  # Total: 27 (real SAT english) module 1 should have 27 questions
    else:
        return {"Easy": 5, "Medium": 10, "Hard": 5}    # Default practice


# class QuestionResponse(BaseModel):
#     id: str
#     section: str
#     domain: str
#     difficulty: str
#     question_text: str
#     paragraph: Optional[str]
#     choices: Dict[str, str]

def questions_to_response(questions: List[SATQuestion], include_answers: bool = False):
    """Convert database questions to API response format"""
    print(f"questions_to_response called with include_answers={include_answers}")
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
            },
        }
        
        if include_answers:
            question_data["correct_answer"] = q.correct_answer
            question_data["explanation"] = q.explanation
            
        result.append(question_data)  # Return dict instead of Pydantic model
    
    return result

def determine_module2_difficulty_points(module1_results: List[Dict]) -> str:
    """Point-based system with different scoring for each difficulty"""
    
    points_earned = 0
    
    for result in module1_results:
        if result['is_correct']:
            if result['difficulty'] == "Easy":
                points_earned += 1
            elif result['difficulty'] == "Medium":
                points_earned += 2
            elif result['difficulty'] == "Hard":
                points_earned += 3
    
    # Threshold based on points (adjust based on your module 1 composition)
    if points_earned >= 25:  # Adjust this threshold
        return "higher"
    else:
        return "lower"

def get_module_questions(db: Session, exam: MockExam, module_number: int) -> List[MockExamQuestion]:
    """Get MockExamQuestion objects for a specific module using stored question IDs"""
    
    if module_number == 1:
        question_ids = exam.module1_questions or []
    elif module_number == 2:
        question_ids = exam.module2_questions or []
    else:
        return []
    
    if not question_ids:
        return []
    
    # Fetch the MockExamQuestion objects for these specific questions
    exam_questions = db.query(MockExamQuestion)\
        .filter(
            MockExamQuestion.mock_exam_id == exam.id,
            MockExamQuestion.sat_question_id.in_(question_ids)
        )\
        .order_by(MockExamQuestion.question_order)\
        .all()
    
    return exam_questions


def generate_module2_questions(db: Session, section: MockExamSection, difficulty_level: str) -> List[SATQuestion]:
    """Generate module 2 questions based on module 1 performance for a specific section"""
    
    section_type = section.section_type
    
    if difficulty_level == "higher":
        if section_type == "Math":
            difficulty_mix = {"Easy": 3, "Medium": 8, "Hard": 11}  # 22 total
        else:  # English
            difficulty_mix = {"Easy": 5, "Medium": 10, "Hard": 12}  # 27 total
    else:  # lower difficulty
        if section_type == "Math":
            difficulty_mix = {"Easy": 11, "Medium": 8, "Hard": 3}  # 22 total
        else:  # English
            difficulty_mix = {"Easy": 16, "Medium": 9, "Hard": 2}  # 27 total
    
    return generate_section_questions(db, section_type, difficulty_mix)


# def score_exam(exam: MockExam) -> (int, int):
#     """Score a mock exam based on module 1 and module 2 performance"""
#     module1_score = exam.module1_correct
#     module2_score = exam.module2_correct
    
#     combinedScore = module1_score + module2_score

#     if(exam.module2_difficulty_assigned == "lower"):
#         score = round_to_nearest_10( 200 + (combinedScore/44) * (690 - 200) )
#     else:
#         score = round_to_nearest_10( 300 + (combinedScore/44) * (800 - 300) )
    
#     return score, combinedScore


def get_section_question_counts(section_type: str) -> dict:
    """Get the correct question counts for each section type"""
    if section_type == "Math":
        return {
            "module1_total": 22,
            "module2_total": 22,
            "total": 44
        }
    elif section_type == "English":
        return {
            "module1_total": 27,
            "module2_total": 27,
            "total": 54
        }
    else:
        raise ValueError(f"Unknown section type: {section_type}")



def create_mock_exam_sections(db: Session, exam: MockExam, exam_type: str) -> List[MockExamSection]:
    """Create the appropriate sections based on exam type"""
    sections = []

    if exam_type in ["english_only", "full_exam"]:
        english_section = MockExamSection(
            mock_exam_id=exam.id,
            section_type="English",
            **get_section_question_counts("English")
        )
        sections.append(english_section)
    
    if exam_type in ["math_only", "full_exam"]:
        math_section = MockExamSection(
            mock_exam_id=exam.id,
            section_type="Math",
            **get_section_question_counts("Math")
        )
        sections.append(math_section)
    
    for section in sections:
        db.add(section)
    
    return sections

def get_section_module_questions(db: Session, section: MockExamSection, module_number: int) -> List[MockExamQuestion]:
    """Get MockExamQuestion objects for a specific module of a section"""
    
    return db.query(MockExamQuestion)\
        .filter(
            MockExamQuestion.section_id == section.id,
            MockExamQuestion.module_number == module_number
        )\
        .order_by(MockExamQuestion.question_order)\
        .all()

def calculate_section_score(section: MockExamSection) -> int:
    """Calculate the scaled score (200-800) for a section"""
    
    total_correct = section.total_correct
    section_type = section.section_type
    difficulty_level = section.module2_difficulty_assigned
    
    # Different scoring based on section type
    if section_type == "Math":
        total_possible = 44
    else:  # English
        total_possible = 54
    
    if difficulty_level == "lower":
        score = round_to_nearest_10(200 + (total_correct / total_possible) * (690 - 200))
    else:
        score = round_to_nearest_10(300 + (total_correct / total_possible) * (800 - 300))
    
    return score

#submitting helper functions

def get_exam_and_sections(db: Session, exam_id: str, section_type: str):
    exam = db.query(MockExam).filter(MockExam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    section = next((s for s in exam.sections if s.section_type == section_type), None)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section {section_type} not found")
    
    return exam, section

def score_module(
    db: Session,
    section: MockExamSection,
    module_number: int,
    answers: Dict[str, str],
    user_id: str
) -> tuple[int, list]:
    """Score a module and update user performance"""
    
    questions = get_section_module_questions(db, section, module_number)
    
    correct_count = 0
    module_results = []
    
    for exam_question in questions:
        user_answer = answers.get(exam_question.sat_question_id)
        sat_question = db.query(SATQuestion).filter_by(
            id=exam_question.sat_question_id
        ).first()
        
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
        
        # Update user performance 
        # TODO: fix update_user_performace function
        # update_user_performance(user_id, sat_question, is_correct, db)
    
    return correct_count, module_results

def handle_module1_submission(db: Session, section: MockExamSection, section_type: str, correct_count: int, module_results: List):
    """Handle module 1 submission and generate module 2"""

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
    
    total_questions = len(get_section_module_questions(db, section, 1))
    
    return {
        "section_type": section_type,
        "module": 1,
        "correct": correct_count,
        "total": total_questions,
        "percentage": (correct_count / total_questions) * 100,
        "module2_difficulty": difficulty_level,
        "module2_questions": questions_to_response(module2_questions, include_answers=True),
        "message": f"Module 1 complete. Module 2 will be {'more challenging' if difficulty_level == 'higher' else 'easier'}."
    }

def handle_module2_submission(
    db: Session,
    exam: MockExam,
    section: MockExamSection,
    section_type: str,
    correct_count: int,
    time_ended: Optional[str]
):
    """Handle module 2 submission and finalize exam"""
    
    section.module2_completed = True
    section.module2_correct = correct_count
    section.total_correct = section.module1_correct + section.module2_correct
    
    # Calculate section score
    section.section_score = calculate_section_score(section)
    
    # Mark completion time
    if time_ended:
        section.completed_at = datetime.now(timezone.utc)
    
    db.flush()
    
    # Check if entire exam is complete
    if exam.is_completed:
        exam.completed_at = datetime.now(timezone.utc)
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
        "module": 2,
        "section_score": section.section_score,
        "total_correct": section.total_correct,
        "total_questions": section.total_questions,
        "percentage": section.percentage_correct,
        "exam_completed": exam.is_completed,
        "total_exam_score": exam.total_score if exam.is_completed else None
    }