from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
from app.sat_routes import sat_router
from app.practice_tutor_routes import practice_tutor_router
from dotenv import load_dotenv
import os
from app.auth import get_current_user

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
app.include_router(sat_router)
app.include_router(practice_tutor_router)

@app.get("/protected")
def protected_route(user = Depends(get_current_user)):
    return {"user_id": user.user.id}
