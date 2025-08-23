from pydantic import BaseModel, root_validator
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID
import uuid
from typing import Optional, Any, Dict
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

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
    
