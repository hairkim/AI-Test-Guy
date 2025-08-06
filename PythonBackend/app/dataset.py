from app.database import SessionLocal
from app.models import Question, Solution, Exam, Section, QuestionEmbedding
from app.chain import get_vectorstore
from openai import OpenAI
import os, uuid, time
from datasets import load_dataset
from sentence_transformers import SentenceTransformer

#for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
dataset = load_dataset("ndavidson/sat-math-chain-of-thought")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
db = SessionLocal()

def createEmbedding(question: Question) -> QuestionEmbedding:
    embedding_vector = model.encode(question.question_text).tolist()
    return QuestionEmbedding(
        question_id=question.id,
        text=question.question_text,
        embedding=embedding_vector
    )

def insert_from_dataset():
    start = time.time()

    # --- Ensure exam/section ---
    exam = db.query(Exam).filter_by(name="sat").first()
    if not exam:
        exam = Exam(name="sat", description="")
        db.add(exam)
        db.flush()

    section = db.query(Section).filter_by(name="math", exam_id=exam.id).first()
    if not section:
        section = Section(name="math", exam_id=exam.id)
        db.add(section)
        db.flush()

    db.commit()

    # --- Vector store for LangChain tables ---
    # name the collection by exam/section (must match what you use when retrieving)
    collection_name = "sat_math"
    vectorstore = get_vectorstore(collection_name)

    train_set = dataset["train"]
    subset = train_set.select(range(len(train_set) // 6))

    # batch buffers for vectorstore.add_texts
    batch_texts: List[str] = []
    batch_metas: List[Dict] = []
    batch_ids: List[str] = []
    BATCH_SIZE = 100

    def flush_batch():
        if not batch_texts:
            return
        vectorstore.add_texts(
            texts=batch_texts,
            metadatas=batch_metas,
            ids=batch_ids,           # prevents duplicates if re-running
        )
        batch_texts.clear()
        batch_metas.clear()
        batch_ids.clear()

    for row in subset:
        question_text = row["question"]

        # --- your own tables ---
        q = Question(
            section_id=section.id,
            question_text=question_text,
            answer=row.get("answer"),
        )
        db.add(q)
        db.flush()  # get q.id

        db.add(createEmbedding(q))  # optional: keep your own embedding table

        for i, step in enumerate(row["reasoning_chain"]["steps"]):
            db.add(Solution(
                question_id=q.id,
                step_num=i + 1,
                step_text=step.get("explanation", "")
            ))

        # --- LangChain tables (add to batch) ---
        batch_texts.append(question_text)
        batch_metas.append({
            "exam": "sat",
            "section": "math",
            "question_id": q.id,
            # add whatever you need for filtering later:
            # "answer": row.get("answer"),
        })
        batch_ids.append(str(q.id))   # your DB id as stable doc id

        # flush periodically
        if len(batch_texts) >= BATCH_SIZE:
            flush_batch()
            print("🔎 Indexed", BATCH_SIZE, "questions into langchain_pg_embedding")

    # final flush
    flush_batch()
    db.commit()

    print(f"✅ Inserted into your tables and langchain_pg_* in {time.time() - start:.2f}s")

insert_from_dataset()
