from app.database import SessionLocal
from app.models import Question, Solution, Exam, Section, QuestionEmbedding
from app.chain import get_vectorstore
from openai import OpenAI
import os, uuid, time
from datasets import load_dataset

import torch
from transformers import AutoTokenizer, AutoModel

MODEL_ID = "tbs17/MathBERT-custom"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class HFMeanPoolEmbedder:
    def __init__(self, model_id: str = MODEL_ID, device: str = DEVICE):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
        self.model = AutoModel.from_pretrained(model_id)
        self.model.to(device)
        self.device = device

    @torch.no_grad()
    def encode(self, texts, batch_size: int = 16, max_length: int = 512):
        # accepts str or list[str]
        single = isinstance(texts, str)
        if single:
            texts = [texts]

        embs = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            inputs = self.tokenizer(
                batch, padding=True, truncation=True, max_length=max_length, return_tensors="pt"
            ).to(self.device)

            outputs = self.model(**inputs)                 # last_hidden_state: [B, T, H]
            last_hidden = outputs.last_hidden_state
            mask = inputs["attention_mask"].unsqueeze(-1).float()  # [B, T, 1]

            # mean pooling over tokens actually present
            summed = (last_hidden * mask).sum(dim=1)       # [B, H]
            counts = mask.sum(dim=1).clamp(min=1e-9)       # [B, 1]
            mean_pooled = summed / counts

            # L2-normalize for cosine similarity vector stores (recommended)
            mean_pooled = torch.nn.functional.normalize(mean_pooled, p=2, dim=1)

            embs.append(mean_pooled.cpu())

        embs = torch.cat(embs, dim=0)                      # [N, H]
        return embs[0].tolist() if single else [e.tolist() for e in embs]

#for embeddings
dataset = load_dataset("ndavidson/sat-math-chain-of-thought")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
db = SessionLocal()

embedder = HFMeanPoolEmbedder(MODEL_ID)

def createEmbedding(question: Question) -> QuestionEmbedding:
    embedding_vector = embedder.encode(question.question_text)  # -> List[float]
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
