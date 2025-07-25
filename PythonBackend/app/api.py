from fastapi import APIRouter, UploadFile, File, Form
from app.models import Query
from app.chain import qa_chain
from app.extract import pdf_to_images, image_to_base64
import pdfplumber
from openai import OpenAI
import json
import os
import re
from app.pipeline import process_pdf


router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/ask")
def ask_question(query: Query):
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
    process_pdf(contents, exam_name)  # <-- runs classification, extraction, and DB insert

    return {"message": "✅ PDF processed and questions saved to database."}
    
