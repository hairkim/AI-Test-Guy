from pydantic import BaseModel, root_validator
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index, Boolean, UniqueConstraint, CheckConstraint, DateTime
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

class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)

    sections = relationship("Section", back_populates="exam")


class Section(Base):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id"))

    exam = relationship("Exam", back_populates="sections")
    questions = relationship("Question", back_populates="section")


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


class Solution(Base):
    __tablename__ = "solutions"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    step_num = Column(Integer)
    step_text = Column(Text)

    question = relationship("Question", back_populates="solutions")


class QuestionEmbedding(Base):
    __tablename__ = "question_embeddings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    text = Column(Text)
    # embedding = Column(Vector(1536))  # OpenAI embedding size
    embedding = Column(Vector(768))

    question = relationship("Question", backref="embedding")

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


class ReadingAnswer(Base):
    __tablename__ = "reading_answers"

    # question_id is the PK (one answer per question)
    question_id = Column(Integer, ForeignKey("reading_questions.id", ondelete="CASCADE"), primary_key=True)
    label = Column(String(1), nullable=False)  # 'A'|'B'|'C'|'D'

    question = relationship("ReadingQuestion", back_populates="answer")

    __table_args__ = (
        CheckConstraint("label IN ('A','B','C','D')", name="ck_answer_label_abcd"),
    )


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


class MockExam(Base):
    """Mock exam instances for users"""
    __tablename__ = "mock_exams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String)  # For when you add user accounts
    exam_type = Column(String, nullable=False)  # "full_sat", "math_only", "english_only"

    # Module 1 results
    module1_completed = Column(Boolean, default=False)
    module1_correct = Column(Integer, default=0)
    module1_total = Column(Integer, default=22)  # 22 questions per module
    module1_questions = Column(JSONB, default={})
    
    # Module 2 results  
    module2_completed = Column(Boolean, default=False)
    module2_correct = Column(Integer, default=0)
    module2_total = Column(Integer, default=22)
    module2_questions = Column(JSONB, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Calculated fields
    total_questions = Column(Integer)
    correct_answers = Column(Integer)
    score = Column(Integer)  # Scaled score (200-800)
    time_spent_minutes = Column(Integer)
    
    # Exam configuration
    config = Column(JSONB, default={})  # Store difficulty mix, section weights, etc.
    
    # Relationships
    questions = relationship("MockExamQuestion", back_populates="mock_exam", cascade="all, delete-orphan")

    @property 
    def percentage_correct(self):
        if not self.total_questions:
            return 0
        return (self.correct_answers / self.total_questions) * 100


class MockExamQuestion(Base):
    """Junction table linking mock exams to specific questions"""
    __tablename__ = "mock_exam_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mock_exam_id = Column(UUID(as_uuid=True), ForeignKey("mock_exams.id", ondelete="CASCADE"))
    sat_question_id = Column(String, ForeignKey("sat_questions.id", ondelete="CASCADE"))
    
    question_order = Column(Integer)  # Order within the exam
    user_answer = Column(String(1))  # A, B, C, D, or null if not answered
    is_correct = Column(Boolean)
    time_spent_seconds = Column(Integer)
    
    # Relationships
    mock_exam = relationship("MockExam", back_populates="questions")
    sat_question = relationship("SATQuestion", back_populates="mock_exam_questions")


# Optional: Keep track of user performance over time
class UserPerformance(Base):
    """Track user performance across different domains/difficulties"""
    __tablename__ = "user_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    
    # Performance metrics by category
    section = Column(String)  # "Math" or "English" 
    domain = Column(String)   # "Advanced Math", "Information and Ideas", etc.
    difficulty = Column(String)  # "Easy", "Medium", "Hard"
    
    questions_attempted = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    average_time_seconds = Column(Integer)
    
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    @property
    def accuracy_rate(self):
        if not self.questions_attempted:
            return 0
        return (self.questions_correct / self.questions_attempted) * 100
    
