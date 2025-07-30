from openai import OpenAI
from app.extract import pdf_to_images, image_to_base64
from app.database import SessionLocal
from app.models import Exam, Section, Question, Solution
import os, json, re, base64, uuid
from sqlalchemy.orm import Session
from supabase import create_client
from app.models import QuestionEmbedding


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def embed_text(text: str) -> list[float]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


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

def classify_question_to_collection(question: str) -> str:
    messages = [
        {
            "role": "user",
            "content": (
                f"You are a classification assistant. Given a question, return only the name of the most appropriate exam section collection. "
                f"The possible collection names are: 'sat_math', 'sat_reading', 'sat_writing'.\n\n"
                f"Question: {question}\n\n"
                f"Answer with only the collection name, nothing else."
            )
        }
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=20,
    )
    return response.choices[0].message.content.strip()

def embed_and_answer(session: Session, question_text: str) -> dict:
    query_vec = embed_text(question_text)

    # Find most similar questions (top 4)
    similar = (
        session.query(QuestionEmbedding)
        .order_by(QuestionEmbedding.embedding.l2_distance(query_vec))
        .limit(4)
        .all()
    )

    context = "\n---\n".join(item.text for item in similar)

    messages = [
        {"role": "system", "content": "You are an SAT tutor. Use the examples to solve the new question."},
        {"role": "user", "content": f"Examples:\n{context}\n\nNow solve: {question_text}\nReturn a JSON object with 'answer', 'explanation', and 'steps', where steps is a list of objects each with 'step_num' and 'step_text'. Do not return steps as plain strings.'"}
    ]
    response = client.chat.completions.create(
        model="gpt-4o", messages=messages, max_tokens=3000
    )

    match = re.search(r"\{.*\}", response.choices[0].message.content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return {}
    return {"answer": "", "explanation": "", "steps": []}


def upload_image_to_supabase(base64_str: str) -> str:
    image_bytes = base64.b64decode(base64_str)
    filename = f"question_{uuid.uuid4().hex}.png"
    filepath = f"question-images/{filename}"

    res = supabase.storage.from_("question-images").upload(
        filepath,
        image_bytes,
        {"content-type": "image/png"}
    )
    if hasattr(res, 'data') and res.data:
        return f"{SUPABASE_URL}/storage/v1/object/public/{filepath}"
    print("Upload failed:", res)
    return ""

def extract_questions(base64_img: str) -> list:
    prompt = (
        """You are an AI tutor. Extract all SAT questions from the given image. Return a JSON array of objects, where each object follows this exact structure:

        [
            {
                "question": "What is 2 + 2?",
                "choices": ["A. 3", "B. 4", "C. 5", "D. 6"]
            }
        ]

       Do not include commentary. Do not change the format."""
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

    section = session.query(Section).filter_by(name=section_name, exam_id=exam.id).first()
    if not section:
        section = Section(name=section_name, exam_id=exam.id)
        session.add(section)

    session.commit()  # Commit once after ensuring exam/section exist

    for q in questions:
        print("Processing:", q.get("question", ""))
        img_url = upload_image_to_supabase(base64_img) if "image" in q else None
        ai_response = embed_and_answer(session, q.get("question", ""))

        if not isinstance(ai_response, dict):  # Failsafe
            print("Unexpected AI response:", ai_response)
            continue

        question = Question(
            section_id=section.id,
            question_text=q.get("question", ""),
            choices=q.get("choices", []),
            answer=ai_response.get("answer", ""),
            explanation=ai_response.get("explanation", ""),
            image=img_url
        )
        session.add(question)
        session.flush()  # Assigns question.id before adding foreign keys

        vector = embed_text(q.get("question", ""))
        embedding_row = QuestionEmbedding(
            question_id=question.id,
            text=q.get("question", ""),
            embedding=vector
        )
        session.add(embedding_row)

        for i, step in enumerate(ai_response.get("steps", []), start=1):
            if isinstance(step, dict):
                step_obj = Solution(
                    question_id=question.id,
                    step_num=step.get("step_num", i),
                    step_text=step.get("step_text", "")
                )
            else:
                # step is just a string
                step_obj = Solution(
                    question_id=question.id,
                    step_num=i,
                    step_text=str(step)
                )
            session.add(step_obj)

    session.commit()  # Final commit after all data added


def process_pdf(pdf_bytes: bytes, exam_name: str):
    images = pdf_to_images(pdf_bytes)
    encoded = [image_to_base64(img) for img in images]
    db = SessionLocal()
    for img in encoded:
        section = classify_section(img).strip().lower()
        if section not in ["math", "reading", "writing"]:
            print(f"⚠️ Skipping unknown section: {section}")
            continue
        questions = extract_questions(img)
        if questions:
            save_to_db(db, exam_name, section, questions, img)
    db.close()


def process_image_to_question(base64_img: str) -> str:
    prompt = """
        You are a math assistant. Given the image of an SAT math question, extract only the question text (not the answer choices), and rewrite it using LaTeX formatting **only** for mathematical expressions.

        - Keep the natural language intact.
        - Wrap all math symbols, expressions, variables, and numbers in dollar signs: `$...$`.
        - Do NOT include answer choices or explanations.
        - Return only the rewritten question text in one paragraph — no extra commentary.
    """

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
        model="gpt-4o",
        messages=messages,
        max_tokens=500
    )

    return response.choices[0].message.content.strip()
