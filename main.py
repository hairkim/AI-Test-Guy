import json
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import JSONLoader
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# Load your OpenAI key
import os
from dotenv import load_dotenv
import openai

load_dotenv()  # Load from .env into environment
openai_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_key

try:
    models = openai.models.list()
    print("✅ API key is valid!")
except Exception as e:
    print("❌ API key error:", e)

# Step 1: Load and prepare dataset
def load_dataset(filepath):
    with open(filepath, "r") as f:
        data = [json.loads(line) for line in f.readlines()]
    return [
        {
            "page_content": f"Question: {d['question']}\nChoices: {d['choices']}\nAnswer: {d['answer']}\nExplanation: {d['explanation']}",
            "metadata": {"type": "SAT", "subject": "Math"}
        }
        for d in data
    ]

# Step 2: Create vector store
def create_vector_store(data):
    from langchain.schema import Document
    docs = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in data]
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    split_docs = splitter.split_documents(docs)
    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(split_docs, embeddings)
    return db

# Step 3: Create QA Chain
def create_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever()
    llm = ChatOpenAI(temperature=0)
    qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    return qa

# Step 4: Run an example
def main():
    data = load_dataset("sat_math_questions.jsonl")
    vectorstore = create_vector_store(data)
    qa = create_qa_chain(vectorstore)

    while True:
        query = input("Ask a SAT math question (or type 'exit'): ")
        if query.lower() == "exit":
            break
        answer = qa.run(query)
        print("\nAnswer:\n", answer)

if __name__ == "__main__":
    main()
