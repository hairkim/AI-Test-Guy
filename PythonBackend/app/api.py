from fastapi import APIRouter, UploadFile, File, Form
from app.models import Query
from app.chain import get_retriever_for_collection
from openai import OpenAI
import json, os, re, pdfplumber
from app.pipeline import process_pdf, classify_question_to_collection
from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI


router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@router.post("/ask")
def ask_question(query: Query):
    collection = classify_question_to_collection(query.question)
    retriever = get_retriever_for_collection(collection)
    qa_chain = RetrievalQA.from_chain_type(llm=ChatOpenAI(), retriever=retriever)
    answer = qa_chain.run(query.question)
    return {"answer": answer}

@router.post("/submit_pdf")
async def submit_pdf(
    pdf: UploadFile = File(...),
    exam_name: str = Form(...)  # <-- exam name input (e.g., "SAT")
):
    if pdf.content_type != "application/pdf":
        return {"error": "Please upload a valid PDF file."}

    contents = await pdf.read()
    process_pdf(contents, exam_name.lower())  # <-- runs classification, extraction, and DB insert

    return {"message": "✅ PDF processed and questions saved to database."}
    
