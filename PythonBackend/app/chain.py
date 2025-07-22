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


#TODO: Make this so that it loads embeddings only when submission and make function that creates vectorstore
#using the subject that the query uses (maybe use chat for that or make like a button to change sections)
embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
vectorstore = Chroma(
    collection_name="sat_math",
    persist_directory="../vectorstores/sat_math",
    embedding_function=embeddings
)

retriever = vectorstore.as_retriever()
qa_chain = RetrievalQA.from_chain_type(llm=ChatOpenAI(), retriever=retriever)
