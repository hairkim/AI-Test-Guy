from fastapi import APIRouter, Depends
from app.database import get_db
from app.models import UserPerformance, DailyTask
from app.dailytaskhelperfunctions import generate_personalized_tasks, update_user_performance
from sqlalchemy import func
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.auth import get_current_user_db
from typing import Any

daily_task_router = APIRouter(prefix="/api/daily", tags=["Daily Tasks"])

@daily_task_router.post("/tasks/generate-daily")
def generate_daily_tasks(user = Depends(get_current_user_db), db: Session = Depends(get_db)):
    """Generate tasks for today"""
    
    today = datetime.now(timezone.utc).date()
    user_id = user.id

    def serialize_task(task: DailyTask):
        return {
            "id": str(task.id),
            "task_title": task.task_title,
            "section": task.section,
            "domain": task.domain,
            "difficulty": task.difficulty,
            "target_count": task.target_count,
            "progress_count": task.progress_count,
            "is_completed": task.is_completed,
        }
    
    # Check if tasks already exist for today
    existing = db.query(DailyTask).filter(
        DailyTask.user_id == user_id,
        func.date(DailyTask.task_date) == today
    ).all()
    
    if existing:
        return {
            "message": "Tasks already generated for today",
            "tasks": [serialize_task(task) for task in existing],
        }
    
    # Generate personalized or default tasks
    tasks = generate_personalized_tasks(user_id, db)
    
    # Create task records
    created_tasks = []
    for task_data in tasks:
        # Extract the fields that DailyTask actually has
        task = DailyTask(
            user_id=user_id,
            task_date=datetime.now(timezone.utc),
            section=task_data.get('section'),
            domain=task_data.get('domain'),
            difficulty=task_data.get('difficulty'),
            target_count=task_data.get('target_count', task_data.get('count', 5)),
            task_title=task_data.get('task_title'),
            # Don't pass "type" or "priority" since DailyTask doesn't have those fields
        )
        db.add(task)
        created_tasks.append(task)
    
    db.commit()
    for task in created_tasks:
        db.refresh(task)

    return {"tasks": [serialize_task(task) for task in created_tasks]}
