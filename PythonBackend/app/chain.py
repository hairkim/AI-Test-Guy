from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
import json, os
from dotenv import load_dotenv


load_dotenv()
openai_key = os.getenv("OPENAI_KEY")
vector_url = os.getenv("DATABASE_URL")
retriever_cache = {}


def get_retriever_for_collection(collection):
    if collection not in retriever_cache:
        vectorstore = PGVector(
            connection_string=vector_url,
            collection_name=collection,
            embedding_function=OpenAIEmbeddings(openai_api_key=openai_key)
        )
        retriever_cache[collection] = vectorstore.as_retriever()
    return retriever_cache[collection]


# embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
# vectorstore = PGVector(
#     connection_string=pgvector_url,
#     embedding_function=embeddings,
#     collection_name=collection_name
# )


# retriever = vectorstore.as_retriever()
# qa_chain = RetrievalQA.from_chain_type(llm=ChatOpenAI(), retriever=retriever)
