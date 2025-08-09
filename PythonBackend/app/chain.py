from langchain_postgres import PGVector
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.schema import Document
import json, os
from dotenv import load_dotenv


load_dotenv()
vector_url = os.getenv("DATABASE_URL")
retriever_cache = {}
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def get_vectorstore(collection_name: str) -> PGVector:
    """
    Returns a PGVector store bound to a 'collection_name'.
    If the collection doesn't exist yet, it will be created on first insert.
    """
    vectorstore = PGVector(
        embeddings=embedding_model,
        collection_name=collection_name,
        connection=vector_url,
        use_jsonb=True,
    )
    vectorstore.create_tables_if_not_exists()
    return vectorstore

def get_retriever_for_collection(collection: str):
    mapping = {
        "sat_math": "sat_math",
        # add others...
    }
    coll_name = mapping.get(collection, "sat_math")
    if coll_name not in retriever_cache:
        vectorstore = get_vectorstore(coll_name)
        # Tune k, score_threshold, etc. as needed
        retriever = vectorstore.as_retriever(
            search_type="similarity",          # or "mmr"
            search_kwargs={"k": 4}             # top-k docs
        )
        retriever_cache[coll_name] = retriever
    return retriever_cache[coll_name]



#this is the openAI version
# def get_retriever_for_collection(collection):
#     if collection not in retriever_cache:
#         vectorstore = PGVector(
#             connection_string=vector_url,
#             collection_name=collection,
#             embedding_function=OpenAIEmbeddings(openai_api_key=openai_key)
#         )
#         retriever_cache[collection] = vectorstore.as_retriever()
#     return retriever_cache[collection]

#this is using sentence transformer embedding
# Initialize HuggingFace embedding


# embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
# vectorstore = PGVector(
#     connection_string=pgvector_url,
#     embedding_function=embeddings,
#     collection_name=collection_name
# )


# retriever = vectorstore.as_retriever()
# qa_chain = RetrievalQA.from_chain_type(llm=ChatOpenAI(), retriever=retriever)
