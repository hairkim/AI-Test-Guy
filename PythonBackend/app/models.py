from pydantic import BaseModel, root_validator
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index, Boolean, UniqueConstraint, CheckConstraint, DateTime, func, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID
import uuid
from typing import Optional, Any, Dict
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from datetime import datetime

class EnhancedQuery(BaseModel):
    question: Optional[str] = None
    image: Optional[str] = None

    @root_validator(pre=True)
    def validate_question_or_image(cls, values):
        question = values.get('question')
        image = values.get('image')

        # Check if neither question nor image is provided
        if not question and not image:
            raise ValueError("Either question text or image must be provided")
        
        # If question is provided but empty string, treat as None
        if question is not None and not question.strip():
            values['question'] = None

        return values

class EnglishQuery(BaseModel):
    question: str = ""
    passage: Optional[str] = None
    image: Optional[str] = None
    
    # @validator('image')
    # def validate_image(cls, v):
    #     """
    #     Pydantic validator that automatically runs whenever 'image' field is set.
    #     Validates that the base64 string represents a valid image.
    #     """
    #     if v is not None:
    #         try:
    #             # Step 1: Decode the base64 string
    #             image_data = base64.b64decode(v)
    #             print(image_data)
                
    #             # Step 2: Try to open it as an image using PIL
    #             # This will raise an exception if the data isn't a valid image
    #             Image.open(io.BytesIO(image_data))
                
    #             # If we get here, the image is valid
    #             return v
                
    #         except Exception as e:
    #             # If decoding or opening fails, raise a validation error
    #             raise ValueError(f"Invalid image data: {e}")
        
    #     # If image is None, that's fine
    #     return v
    
    # @validator('question')
    # def validate_question_or_image(cls, v, values):
    #     """
    #     Validator that ensures either question text OR image is provided.
    #     Uses the 'values' parameter to access other fields during validation.
    #     """
    #     # Check if neither question nor image is provided
    #     if not v and not values.get('image'):
    #         raise ValueError("Either question text or image must be provided")
        
    #     # If question is provided but empty string, treat as None
    #     if v is not None and not v.strip():
    #         return None
            
    #     return v

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    picture_url = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False,
                         server_default=text("timezone('UTC', now())"))
    level = Column(Integer, default=1)

class Task_Types(Base):
    __tablename__ = "task_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    points = Column(Integer, default=0)
    category = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False,
                         server_default=text("timezone('UTC', now())"))

class UserTaskCompletion(Base):
    __tablename__ = "user_task_completions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_type_id = Column(Integer, ForeignKey("task_types.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False, 
                         server_default=text("timezone('UTC', now())"))
    __table_args__ = (
        UniqueConstraint("user_id", "task_type_id", "completed_at", name="uq_user_task_completion"),
    )

#not using this anymore
class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)

    sections = relationship("Section", back_populates="exam")


#not using this anymore
class Section(Base):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id"))

    exam = relationship("Exam", back_populates="sections")
    questions = relationship("Question", back_populates="section")


#not using
class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey("sections.id"))
    question_text = Column(Text, nullable=False)
    answer = Column(String)
    explanation = Column(Text)
    image = Column(Text)  # base64 string or URL

    section = relationship("Section", back_populates="questions")
    solutions = relationship("Solution", back_populates="question")

#not using
class Solution(Base):
    __tablename__ = "solutions"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    step_num = Column(Integer)
    step_text = Column(Text)

    question = relationship("Question", back_populates="solutions")

#not using
class QuestionEmbedding(Base):
    __tablename__ = "question_embeddings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    text = Column(Text)
    # embedding = Column(Vector(1536))  # OpenAI embedding size
    embedding = Column(Vector(768))

    question = relationship("Question", backref="embedding")

#not using
class Passage(Base):
    __tablename__ = "passages"

    id = Column(Integer, primary_key=True)
    dataset = Column(Text, nullable=False)           # e.g., 'MCTest'
    split = Column(Text, nullable=False)             # 'train' | 'dev' | 'test'
    story_id = Column(Text, nullable=False, unique=True)  # e.g., 'mc160.train.0'
    text = Column(Text, nullable=False)              # full story text
    meta = Column(JSONB, nullable=False, server_default="{}")

    # children
    questions = relationship(
        "ReadingQuestion",
        back_populates="passage",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sentences = relationship(
        "PassageSentence",
        back_populates="passage",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PassageSentence.sent_idx",
    )

    __table_args__ = (
        Index("ix_passages_dataset_split", "dataset", "split"),
    )

#not using
class ReadingQuestion(Base):
    __tablename__ = "reading_questions"

    id = Column(Integer, primary_key=True)
    passage_id = Column(Integer, ForeignKey("passages.id", ondelete="CASCADE"), nullable=False)
    q_index = Column(Integer, nullable=False)  # 1..4 per story
    question_text = Column(Text, nullable=False)
    requires_multiple = Column(Boolean, nullable=False)  # from 'multiple:' vs 'one:'

    passage = relationship("Passage", back_populates="questions")

    choices = relationship(
        "ReadingChoice",
        back_populates="question",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ReadingChoice.label",
    )

    # one-to-one
    answer = relationship(
        "ReadingAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    __table_args__ = (
        UniqueConstraint("passage_id", "q_index", name="uq_readingq_passage_qindex"),
        Index("ix_reading_questions_passage_qindex", "passage_id", "q_index"),
    )

#not using
class ReadingChoice(Base):
    __tablename__ = "reading_choices"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("reading_questions.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(1), nullable=False)   # 'A'|'B'|'C'|'D'
    text = Column(Text, nullable=False)

    question = relationship("ReadingQuestion", back_populates="choices")

    __table_args__ = (
        UniqueConstraint("question_id", "label", name="uq_choice_question_label"),
        CheckConstraint("label IN ('A','B','C','D')", name="ck_choice_label_abcd"),
    )

#not using
class ReadingAnswer(Base):
    __tablename__ = "reading_answers"

    # question_id is the PK (one answer per question)
    question_id = Column(Integer, ForeignKey("reading_questions.id", ondelete="CASCADE"), primary_key=True)
    label = Column(String(1), nullable=False)  # 'A'|'B'|'C'|'D'

    question = relationship("ReadingQuestion", back_populates="answer")

    __table_args__ = (
        CheckConstraint("label IN ('A','B','C','D')", name="ck_answer_label_abcd"),
    )

#not using
class PassageSentence(Base):
    __tablename__ = "passage_sentences"

    id = Column(Integer, primary_key=True)
    passage_id = Column(Integer, ForeignKey("passages.id", ondelete="CASCADE"), nullable=False)
    sent_idx = Column(Integer, nullable=False)      # 1-based line number
    sent_text = Column(Text, nullable=False)

    passage = relationship("Passage", back_populates="sentences")

    __table_args__ = (
        UniqueConstraint("passage_id", "sent_idx", name="uq_sentence_passage_idx"),
        Index("ix_passage_sentences_passage_idx", "passage_id", "sent_idx"),
    )


class SATQuestion(Base):
    """
    Optimized model for OpenSAT dataset questions
    Simpler structure than your existing Question model
    """
    __tablename__ = "sat_questions"
    
    id = Column(String, primary_key=True)  # Use the original ID from dataset
    section = Column(String, nullable=False)  # "Math" or "English"
    domain = Column(String, nullable=False)  # "Advanced Math", "Information and Ideas", etc.
    difficulty = Column(String, nullable=False)  # "Easy", "Medium", "Hard"
    
    question_text = Column(Text, nullable=False)
    paragraph = Column(Text)  # For reading comprehension questions
    
    choice_a = Column(Text, nullable=False)
    choice_b = Column(Text, nullable=False) 
    choice_c = Column(Text, nullable=False)
    choice_d = Column(Text, nullable=False)
    
    correct_answer = Column(String(1), nullable=False)  # A, B, C, or D
    explanation = Column(Text, nullable=False)
    visual_type = Column(String)  # If there are visual elements
    
    # Relationships
    mock_exam_questions = relationship("MockExamQuestion", back_populates="sat_question")
    sat_embeddings = relationship("SATQuestionEmbedding", back_populates="sat_question")

    # Database indexes for performance
    __table_args__ = (
        Index("ix_sat_questions_section", "section"),
        Index("ix_sat_questions_difficulty", "difficulty"), 
        Index("ix_sat_questions_domain", "domain"),
        Index("ix_sat_questions_section_difficulty", "section", "difficulty"),  # Composite index
        Index("ix_sat_questions_section_domain", "section", "domain"),  # Composite index
        Index("ix_sat_questions_paragraph_not_null", "section", "difficulty", 
              postgresql_where="paragraph IS NOT NULL"),  # Partial index for passage-based questions
    )

    def to_dict(self):
        """Convert to dict for API responses"""
        return {
            "id": self.id,
            "section": self.section,
            "domain": self.domain,
            "difficulty": self.difficulty,
            "question_text": self.question_text,
            "paragraph": self.paragraph,
            "choices": {
                "A": self.choice_a,
                "B": self.choice_b, 
                "C": self.choice_c,
                "D": self.choice_d
            },
            "correct_answer": self.correct_answer,
            "explanation": self.explanation
        }


class SATQuestionEmbedding(Base):
    """Embeddings for SAT questions for similarity search"""
    __tablename__ = "sat_question_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(String, ForeignKey("sat_questions.id", ondelete="CASCADE"))
    text = Column(Text)
    embedding = Column(Vector(768))  # MathBERT embedding size
    
    sat_question = relationship("SATQuestion", back_populates="sat_embeddings")


class UserPerformance(Base):
    """Track user performance across different domains/difficulties"""
    __tablename__ = "user_performance"


    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)


    # Performance metrics by category
    section = Column(String) # "Math" or "English"
    domain = Column(String) # "Advanced Math", "Information and Ideas", etc.
    difficulty = Column(String) # "Easy", "Medium", "Hard"


    questions_attempted = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    average_time_seconds = Column(Integer)


    last_updated = Column(DateTime(timezone=True), nullable=False,
    server_default=text("timezone('UTC', now())"),
    server_onupdate=text("timezone('UTC', now())"))


    @property
    def accuracy_rate(self):
        if not self.questions_attempted:
            return 0
        return (self.questions_correct / self.questions_attempted) * 100

class MockExam(Base):
    """Main mock exam record - can contain multiple sections"""
    __tablename__ = "mock_exams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String)
    exam_type = Column(String, nullable=False)  # "full_exam", "math_only", "english_only"
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("timezone('UTC', now())"))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Overall exam stats (calculated from sections)
    total_score = Column(Integer)  # Combined score for full SAT
    time_spent_minutes = Column(Integer)
    
    # Exam configuration
    config = Column(JSONB, default={})
    
    # Relationships
    sections = relationship("MockExamSection", back_populates="mock_exam", cascade="all, delete-orphan")
    
    @property
    def is_completed(self):
        """Check if all sections are completed"""
        return all(section.is_completed for section in self.sections)
    
    @property
    def math_section(self):
        """Get math section if it exists"""
        return next((s for s in self.sections if s.section_type == "Math"), None)
    
    @property
    def english_section(self):
        """Get English section if it exists"""
        return next((s for s in self.sections if s.section_type == "English"), None)


class MockExamSection(Base):
    """Individual section (Math or English) within a mock exam"""
    __tablename__ = "mock_exam_sections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mock_exam_id = Column(UUID(as_uuid=True), ForeignKey("mock_exams.id", ondelete="CASCADE"))
    section_type = Column(String, nullable=False)  # "Math" or "English"
    
    # Module 1 results
    module1_completed = Column(Boolean, default=False)
    module1_correct = Column(Integer, default=0)
    module1_total = Column(Integer, default=22)  # Will be 22 for math, 27 for English
    module1_questions = Column(JSONB, default=list)  # List of question IDs
    
    # Module 2 results
    module2_completed = Column(Boolean, default=False)
    module2_correct = Column(Integer, default=0)
    module2_total = Column(Integer, default=22)  # Will be 22 for math, 27 for English
    module2_questions = Column(JSONB, default=list)
    module2_difficulty_assigned = Column(String)  # "higher" or "lower"

    total = Column(Integer, default=0)
    
    # Section-specific timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    time_spent_minutes = Column(Integer)
    
    # Calculated fields
    total_correct = Column(Integer, default=0)
    section_score = Column(Integer)  # 200-800 for this section
    
    # Relationships
    mock_exam = relationship("MockExam", back_populates="sections")
    questions = relationship("MockExamQuestion", back_populates="section", cascade="all, delete-orphan")
    
    @property
    def is_completed(self):
        return self.module1_completed and self.module2_completed
    
    @property
    def total_questions(self):
        return self.module1_total + self.module2_total
    
    @property
    def percentage_correct(self):
        if self.total_questions == 0:
            return 0
        return (self.total_correct / self.total_questions) * 100



class MockExamQuestion(Base):
    """Junction table linking sections to specific questions"""
    __tablename__ = "mock_exam_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("mock_exam_sections.id", ondelete="CASCADE"))
    sat_question_id = Column(String, ForeignKey("sat_questions.id", ondelete="CASCADE"))
    
    module_number = Column(Integer, nullable=False)  # 1 or 2
    question_order = Column(Integer)  # Order within the module
    user_answer = Column(String(1))  # A, B, C, D, or null
    is_correct = Column(Boolean)
    time_spent_seconds = Column(Integer)
    
    # Relationships
    section = relationship("MockExamSection", back_populates="questions")
    sat_question = relationship("SATQuestion", back_populates="mock_exam_questions")


# Updated helper functions
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
    

class CollegeSATScore(Base):
    """
    Model for storing college SAT score ranges
    """
    __tablename__ = "college_sat_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    college_name = Column(String, nullable=False, unique=True)
    sat_range = Column(String, nullable=False)  # e.g., "1200-1400"
    
    # Parsed score ranges for easier querying
    sat_min = Column(Integer, nullable=True)  # 25th percentile
    sat_max = Column(Integer, nullable=True)  # 75th percentile
    
    
    # Database indexes for performance
    __table_args__ = (
        Index("ix_college_sat_scores_college_name", "college_name"),
        Index("ix_college_sat_scores_sat_min", "sat_min"),
        Index("ix_college_sat_scores_sat_max", "sat_max"),
        Index("ix_college_sat_scores_range", "sat_min", "sat_max"),  # Composite index for range queries
    )

    def to_dict(self):
        """Convert to dict for API responses"""
        return {
            "id": self.id,
            "college_name": self.college_name,
            "sat_range": self.sat_range,
            "sat_min": self.sat_min,
            "sat_max": self.sat_max,
        }

    @classmethod
    def get_colleges_for_score(cls, db_session, score: int):
        """
        Get colleges where the given score falls within their SAT range
        """
        return db_session.query(cls).filter(
            cls.sat_min <= score,
            cls.sat_max >= score
        ).all()

    @classmethod
    def get_colleges_by_score_range(cls, db_session, min_score: int, max_score: int):
        """
        Get colleges where SAT ranges overlap with the given score range
        """
        return db_session.query(cls).filter(
            cls.sat_min <= max_score,
            cls.sat_max >= min_score
        ).all()

    def __repr__(self):
        return f"<CollegeSATScore(college='{self.college_name}', range='{self.sat_range}')>"