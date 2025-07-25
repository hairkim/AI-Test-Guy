from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from .database import Base

class Query(BaseModel):
    question: str

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
    choices = Column(ARRAY(Text))  # ["A. ...", "B. ...", ...]
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