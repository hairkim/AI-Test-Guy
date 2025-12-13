from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
from app.sat_routes import sat_router
from app.practice_tutor_routes import practice_tutor_router
from dotenv import load_dotenv
import os
from app.auth import get_current_user
from app.dailytaskroutes import daily_task_router
from app.auth import user_router
from app.survival_routes import survival_router

load_dotenv()

app = FastAPI()

frontend_port = os.getenv("PORT", "5173")  # default to 5173 if not set
frontend_origin = f"http://localhost:{frontend_port}"

app.include_router(router)
app.include_router(sat_router)
app.include_router(practice_tutor_router)
app.include_router(daily_task_router)
app.include_router(user_router)
app.include_router(survival_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_origin,
        "https://ai-test-9m1lpcfqi-harris-projects-56ddc17a.vercel.app/"
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/protected")
def protected_route(user = Depends(get_current_user)):
    return {"user_id": user.user.id}
