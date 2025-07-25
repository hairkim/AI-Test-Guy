from openai import OpenAI
from app.extract import pdf_to_images, image_to_base64
from app.database import SessionLocal
from app.models import Exam, Section, Question, Solution
import os, json, re
from sqlalchemy.orm import Session

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def classify_section(base64_img: str) -> str:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What section of the SAT is this page from? Answer only one of: Math, Reading, Writing."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
            ]
        }
    ]
    response = client.chat.completions.create(
        model="gpt-4o", messages=messages, max_tokens=100
    )
    return response.choices[0].message.content.strip()

def extract_questions(base64_img: str) -> list:
    prompt = (
        """You are an AI tutor. Extract all SAT questions from the given image. Return a JSON array of objects, where each object follows this exact structure:

        [
            {
                "question": "Question text here",
                "choices": ["A. ...", "B. ...", "C. ...", "D. ..."],
                "answer": "Correct answer here (e.g., B)",
                "explanation": "Brief summary of how to solve it",
                "image": "data:image/png;base64,... (only if the question includes a diagram or complex equation)",
                "steps": [
                    { "step_num": 1, "step_text": "First step of the solution" },
                    { "step_num": 2, "step_text": "Second step of the solution" }
                    ...
                ]
            }
        ]

        Do not include extra commentary. Only include the "image" field if a diagram or visual is essential to the question. Each question must have clear steps that a student can follow."""
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
            ]
        }
    ]
    response = client.chat.completions.create(
        model="gpt-4o", messages=messages, max_tokens=2000
    )
    content = response.choices[0].message.content

    match = re.search(r"\[\s*\{.*\}\s*\]", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return []
    return []

def save_to_db(session: Session, exam_name: str, section_name: str, questions: list, base64_img: str):
    exam = session.query(Exam).filter_by(name=exam_name).first()
    if not exam:
        exam = Exam(name=exam_name, description="")
        session.add(exam)
        session.commit()

    section = session.query(Section).filter_by(name=section_name, exam_id=exam.id).first()
    if not section:
        section = Section(name=section_name, exam_id=exam.id)
        session.add(section)
        session.commit()

    for q in questions:
        question = Question(
            section_id=section.id,
            question_text=q.get("question", ""),
            choices=q.get("choices", []),
            answer=q.get("answer", ""),
            explanation=q.get("explanation", ""),
            image=base64_img if "image" in q else None
        )
        session.add(question)
    session.commit()

def process_pdf(pdf_bytes: bytes, exam_name: str):
    images = pdf_to_images(pdf_bytes)
    encoded = [image_to_base64(img) for img in images]
    
    db = SessionLocal()
    for img in encoded:
        section = classify_section(img)
        questions = extract_questions(img)
        if questions:
            save_to_db(db, exam_name, section, questions, img)
    db.close()