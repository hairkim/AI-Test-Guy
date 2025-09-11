from sqlalchemy import and_, func
from typing import List, Dict, Optional
from app.models import SATQuestion, MockExam, MockExamQuestion
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict

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
def get_difficulty_distribution(exam_type: str, custom_mix: Optional[Dict[str, int]] = None) -> Dict[str, int]:
    """Get realistic difficulty distribution for different exam types"""
    
    if custom_mix:
        return custom_mix
    
    if exam_type == "math_only":
        return {"Easy": 7, "Medium": 10, "Hard": 5}  # 22 -> 7, 10, 5
    elif exam_type == "english_only":
        return {"Easy": 6, "Medium": 16, "Hard": 5}  # Total: 27 (real SAT english) module 1 should have 27 questions
    elif exam_type == "full_sat":
        return {"Easy": 27, "Medium": 60, "Hard": 23}  # Total: 110 (full SAT) i dont think this will ever get used
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


def generate_module2_questions(db: Session, exam: MockExam, difficulty_level: str) -> List[SATQuestion]:
    """Generate module 2 questions based on module 1 performance"""
    
    if difficulty_level == "higher":
        # More challenging distribution
        if exam.exam_type == "math_only":
            difficulty_mix = {"Easy": 3, "Medium": 8, "Hard": 11} #total 22 questions
        elif exam.exam_type == "english_only": 
            difficulty_mix = {"Easy": 5, "Medium": 10, "Hard": 12} #total 27 questions
        else:  # full_sat - split between math and english
            math_mix = {"Easy": 3, "Medium": 8, "Hard": 11}
            english_mix = {"Easy": 5, "Medium": 10, "Hard": 12}
    else:  # lower difficulty
        if exam.exam_type == "math_only":
            difficulty_mix = {"Easy": 11, "Medium": 8, "Hard": 3} #total 22 questions
        elif exam.exam_type == "english_only":
            difficulty_mix = {"Easy": 16, "Medium": 9, "Hard": 2} #total 27 questions
        else:  # full_sat
            math_mix = {"Easy": 11, "Medium": 8, "Hard": 3}
            english_mix = {"Easy": 16, "Medium": 9, "Hard": 2}
    
    questions = []
    
    if exam.exam_type in ["math_only", "full_sat"]:
        if exam.exam_type == "full_sat":
            math_questions = generate_section_questions(db, "Math", math_mix)
        else:
            math_questions = generate_section_questions(db, "Math", difficulty_mix)
        questions.extend(math_questions)
    
    if exam.exam_type in ["english_only", "full_sat"]:
        if exam.exam_type == "full_sat":
            english_questions = generate_section_questions(db, "English", english_mix)
        else:
            english_questions = generate_section_questions(db, "English", difficulty_mix)
        questions.extend(english_questions)
    
    return questions


def score_exam(exam: MockExam) -> (int, int):
    """Score a mock exam based on module 1 and module 2 performance"""
    module1_score = exam.module1_correct
    module2_score = exam.module2_correct
    
    combinedScore = module1_score + module2_score

    if(exam.module1_difficulty_assigned == "lower"):
        score = round_to_nearest_10( 200 + (combinedScore/44) * (690 - 200) )
    else:
        score = round_to_nearest_10( 300 + (combinedScore/44) * (800 - 300) )
    
    return score, combinedScore