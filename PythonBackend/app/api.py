from fastapi import APIRouter, UploadFile, File
from app.models import Query
from app.chain import qa_chain
from app.extract import parse_pdf_to_json
import pdfplumber

router = APIRouter()

@router.post("/ask")
def ask_question(query: Query):
    answer = qa_chain.run(query.question)
    return {"answer": answer}

@router.post("/submit_pdf")
async def submit_pdf(pdf: UploadFile = File(...)):
    print("yoooooo it hit this")
    if pdf.content_type != "application/pdf":
        return {"error": "Please upload a valid PDF file."}
    
    contents = await pdf.read()

    parse_pdf_to_json(contents, 'sat_math_questions.jsonl')
    return {"response": "Successfully parsed and loaded data"}
    
