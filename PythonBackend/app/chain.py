from langchain.chains import RetrievalQA
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import Document
import json
import os
from dotenv import load_dotenv

load_dotenv()
openai_key = os.getenv("OPENAI_KEY")

def load_dataset(path):
    with open(path, "r") as f:
        data = [json.loads(line) for line in f]
    return [
        Document(
            page_content=f"Question: {d['question']}\nChoices: {d['choices']}\nAnswer: {d['answer']}\nExplanation: {d['explanation']}",
            metadata={"subject": "SAT Math"},
        )
        for d in data
    ]

docs = load_dataset("sat_math_questions.jsonl")
embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
vectorstore = Chroma.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever()
qa_chain = RetrievalQA.from_chain_type(llm=ChatOpenAI(), retriever=retriever)
