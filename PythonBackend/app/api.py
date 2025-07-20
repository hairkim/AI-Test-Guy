from fastapi import APIRouter
from app.models import Query
from app.chain import qa_chain

router = APIRouter()

@router.post("/ask")
def ask_question(query: Query):
    answer = qa_chain.run(query.question)
    return {"answer": answer}
