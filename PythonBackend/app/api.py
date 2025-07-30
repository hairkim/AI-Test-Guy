from fastapi import APIRouter, UploadFile, File, Form
from app.models import Query
from app.chain import get_retriever_for_collection
from openai import OpenAI
import json, os, re, pdfplumber
from app.pipeline import process_pdf, classify_question_to_collection
from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate


router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


latex_prompt = PromptTemplate.from_template(
    """You are a math formatting assistant. Your task is to rewrite the following SAT math question using proper LaTeX syntax, but only for the math parts.

- Do **not** rewrite the entire sentence in LaTeX.
- Only wrap individual math expressions (equations, variables, fractions, exponents, etc.) in dollar signs: `$...$`.
- Keep all natural language, instructions, and non-math text exactly as-is.
- Do **not** repeat or rephrase the math expressions outside of LaTeX.
- Only include the rewritten sentence — no explanations, no extra commentary.

Question:
{question}

Rewritten version:"""
)

latex_answer_prompt = PromptTemplate.from_template(
    """Format the following math explanation using LaTeX for all math expressions.

- Keep the sentence structure and logic.
- Only wrap math expressions with `$...$`.
- Do NOT reword the explanation.

Explanation:
{explanation}

Formatted version:"""
)

latex_chain = LLMChain(llm=ChatOpenAI(), prompt=latex_prompt)
latex_answer_chain = LLMChain(llm=ChatOpenAI(), prompt=latex_answer_prompt)

qa_prompt = PromptTemplate.from_template(
    """You are a helpful math tutor. Use the following context to answer the question in a clear and detailed way.

- If the question includes LaTeX (e.g., `$x^2$`), preserve it.
- Explain your steps clearly.
- Only use the information from the context — do not make up new math.

Context:
{context}

Question:
{question}

Answer:"""
)

@router.post("/ask")
def ask_question(query: Query):
    collection = classify_question_to_collection(query.question)
    retriever = get_retriever_for_collection(collection)

    # Convert to LaTeX first
    latex_query = latex_chain.run(question=query.question)

    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(),
        retriever=retriever,
        chain_type="stuff",  # or "map_reduce" if docs are long
        chain_type_kwargs={"prompt": qa_prompt}
    )
    answer = qa_chain.run(latex_query)

    latex_answer = latex_answer_chain.run(explanation=answer)

    return {"answer": latex_answer}

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
    
