from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

frontend_port = os.getenv("PORT", "5173")  # default to 5173 if not set
frontend_origin = f"http://localhost:{frontend_port}"


app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
