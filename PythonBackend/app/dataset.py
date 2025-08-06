from app.database import SessionLocal
from app.models import Question, Solution, Exam, Section, QuestionEmbedding
from openai import OpenAI
import os, uuid, time
from datasets import load_dataset
from sentence_transformers import SentenceTransformer

#for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
dataset = load_dataset("ndavidson/sat-math-chain-of-thought")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
db = SessionLocal()

def createEmbedding(question):
    embedding_vector = model.encode(question.question_text).tolist()
    embedding_row = QuestionEmbedding(
        question_id=question.id,
        text=question.question_text,
        embedding=embedding_vector
    )
    return embedding_row

def insert_from_dataset():
    start_time = time.time()  # Start timer

    exam = db.query(Exam).filter_by(name="sat").first()
    if not exam:
        exam = Exam(name="sat", description="")
        db.add(exam)

    section = db.query(Section).filter_by(name="math", exam_id=exam.id).first()
    if not section:
        section = Section(name="math", exam_id=exam.id)
        db.add(section)

    db.commit()  # Commit once after ensuring exam/section exist
    train_set = dataset['train']
    #cut dataset in 1/6
    subset = train_set.select(range(len(train_set) // 6))

    for row in subset:
        question_text = row['question']
        q = Question(
            section_id=section.id,
            question_text=question_text,
            answer=row['answer'],
        )
        db.add(q)
        db.flush()  # so q.id is available

        # ⬇️ Embed and save
        embeded_row = createEmbedding(q)
        db.add(embeded_row)

        for i, step in enumerate(row['reasoning_chain']['steps']):
            step_obj = Solution(
                question_id=q.id,
                step_num=i + 1,
                step_text=step['explanation']  # Grab explanation text only
            )
            db.add(step_obj)

        print("added stuff yay")

    db.commit()

    end_time = time.time()  # End timer
    elapsed = end_time - start_time
    print(f"⏱️ Total time taken: {elapsed:.2f} seconds")

insert_from_dataset()
