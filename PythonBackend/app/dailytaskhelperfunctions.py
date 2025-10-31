from app.models import UserPerformance, SATQuestion, DailyTask, User
import datetime
from datetime import timezone
from sqlalchemy import func
from sqlalchemy.orm import Session

def get_default_tasks():
    return [
        {"type": "practice_questions", "section": "Math", "count": 5, "priority": 1, "task_title": "Take All Math Practice Questions"},
        {"type": "practice_questions", "section": "English", "count": 5, "priority": 1, "task_title": "Take All English Practice Questions"},
        # {"type": "review_concepts", "topic": "Basic SAT strategies", "priority": 2, "task_title": "Review Concepts"} #maybe include this idk yet
    ]

def generate_personalized_tasks(user_id, db):
    # Minimum threshold: 20 questions attempted
    userPerf = db.query(UserPerformance).filter(UserPerformance.user_id == user_id).first()
    if userPerf:
        total_questions_attempted = userPerf.questions_attempted
    else:
        total_questions_attempted = 0
    if total_questions_attempted < 20:
        return get_default_tasks()
    
    # Analyze weak areas
    weak_areas = identify_weak_areas(user_id, db)
    
    tasks = []
    for area in weak_areas:
        tasks.append({
            "type": "targeted_practice",
            "section": area.section,
            "domain": area.domain,
            "difficulty": area.difficulty,
            "count": calculate_practice_count(area.accuracy),
            "priority": calculate_priority(area),
            "task_title": f"Take {calculate_practice_count(area.accuracy)} Math Practice Questions"
        })
    
    return tasks

def identify_weak_areas(user_id, db):
    """
    Query UserPerformance to find areas below threshold
    """
    performance_data = db.query(UserPerformance).filter(
        UserPerformance.user_id == user_id,
        UserPerformance.questions_attempted >= 5  # Minimum sample size
    ).all()
    
    weak_areas = []
    for perf in performance_data:
        accuracy = perf.accuracy_rate
        
        # Tiered thresholds
        if accuracy < 60:  # Critical weakness
            weak_areas.append({
                "section": perf.section,
                "domain": perf.domain,
                "difficulty": perf.difficulty,
                "severity": "critical",
                "accuracy": accuracy
            })
        elif accuracy < 75:  # Needs improvement
            weak_areas.append({
                "section": perf.section,
                "domain": perf.domain,
                "difficulty": perf.difficulty,
                "severity": "moderate",
                "accuracy": accuracy
            })
    
    return sorted(weak_areas, key=lambda x: x['accuracy'])[:3]

def calculate_priority(area):
    """
    Calculate priority score for a weak area
    Lower number = higher priority (1 is highest)
    
    Factors:
    - Accuracy (lower = higher priority)
    - Severity level
    - Section importance
    """
    base_priority = 5
    
    # Accuracy weighting (lower accuracy increases priority)
    if area['accuracy'] < 40:
        base_priority -= 3
    elif area['accuracy'] < 60:
        base_priority -= 2
    elif area['accuracy'] < 75:
        base_priority -= 1
    
    # Severity weighting
    if area.get('severity') == 'critical':
        base_priority -= 2
    elif area.get('severity') == 'moderate':
        base_priority -= 1
    
    # Keep priority in valid range
    return max(1, base_priority)

def calculate_practice_count(accuracy):
    """
    Determine number of practice questions based on accuracy rate
    Lower accuracy = more practice needed
    """
    if accuracy < 40:
        return 20  # Very weak - needs lots of practice
    elif accuracy < 60:
        return 15   # Weak - needs moderate practice
    elif accuracy < 75:
        return 10   # Below average - needs some practice
    else:
        return 5   # Decent performance - light practice

def update_user_performance(user_id, question, is_correct, time_spent, db):
    """Called after each question attempt"""
    
    # Update or create performance record
    perf = db.query(UserPerformance).filter(
        UserPerformance.user_id == user_id,
        UserPerformance.section == question.section,
        UserPerformance.domain == question.domain,
        UserPerformance.difficulty == question.difficulty
    ).first()
    
    if not perf:
        perf = UserPerformance(
            user_id=user_id,
            section=question.section,
            domain=question.domain,
            difficulty=question.difficulty
        )
        db.add(perf)
    
    perf.questions_attempted += 1
    if is_correct:
        perf.questions_correct += 1
    
    # Update average time
    if perf.average_time_seconds:
        perf.average_time_seconds = (
            (perf.average_time_seconds * (perf.questions_attempted - 1) + time_spent) 
            / perf.questions_attempted
        )
    else:
        perf.average_time_seconds = time_spent
    
    db.commit()
    
    # Check if this completes any daily tasks
    update_daily_task_progress(user_id, question, db)

def update_daily_task_progress(user_id: str, question: SATQuestion, db: Session):
    """Automatically increment task progress when questions are answered"""
    
    today = datetime.now(timezone.utc).date()
    
    # Get today's tasks that match this question
    tasks = db.query(DailyTask).filter(
        DailyTask.user_id == user_id,
        func.date(DailyTask.task_date) == today,
        DailyTask.is_completed == False,
        DailyTask.section == question.section  # Matches the question's section
    ).all()
    
    for task in tasks:
        # Check if task applies to this question
        task_matches = True
        
        # If task has specific domain/difficulty requirements, check them
        if task.domain and task.domain != question.domain:
            task_matches = False
        if task.difficulty and task.difficulty != question.difficulty:
            task_matches = False
        
        if task_matches:
            # Increment progress
            task.progress_count += 1
            
            # Check if task is complete
            if task.progress_count >= task.target_count:
                task.is_completed = True
                task.completed_at = datetime.now(timezone.utc)
                
                # Optional: Award points to user
                # user = db.query(User).filter(User.id == user_id).first()
                # if user:
                #     user.level += 1 
    
    db.commit()