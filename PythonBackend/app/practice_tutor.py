from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models import SATQuestion
from app.auth import get_current_user

# Import your existing tutor classes
from app.threeagenttutor import ConversationalSATTutor
from app.english_tutor_agent import ConversationalEnglishSATTutor

practice_tutor_router = APIRouter(prefix="/api/practice-tutor", tags=["Practice Tutor"])

class PracticeTutorRequest(BaseModel):
    question_id: str
    user_question: str
    chat_history: Optional[List[dict]] = []

class PracticeTutorResponse(BaseModel):
    response: str
    question_context: dict
    hints_used: int
    difficulty_level: str

class StepByStepRequest(BaseModel):
    question_id: str
    step_requested: str  # "hint", "next_step", "explanation", "check_answer"
    user_attempt: Optional[str] = None

class StepByStepResponse(BaseModel):
    step_type: str
    content: str
    is_final_answer: bool
    next_available_steps: List[str]

class PracticeQuestionTutor:
    def __init__(self, llm_wrapper, wolfram_app_id=None):
        self.math_tutor = ConversationalSATTutor(llm_wrapper, wolfram_app_id)
        self.english_tutor = ConversationalEnglishSATTutor(llm_wrapper)
        self.llm = llm_wrapper
    
    def is_question_related(self, user_question: str, question_context: dict) -> bool:
        """
        Determine if the user's question is related to the current SAT problem
        """
        classification_prompt = f"""
        You are analyzing whether a student's question is related to a specific SAT practice question.
        
        CURRENT SAT QUESTION:
        Section: {question_context['section']}
        Domain: {question_context['domain']}
        Question: {question_context['question_text']}
        
        STUDENT'S QUESTION: {user_question}
        
        Determine if the student's question is about:
        1. This specific SAT question
        2. The concept/topic covered in this question
        3. General SAT strategy for this type of question
        4. How to solve this type of problem
        
        If the question is about something completely unrelated (personal life, other subjects, general conversation), respond with "UNRELATED"
        If the question is related to the SAT problem or similar problems, respond with "RELATED"
        
        Only respond with either "RELATED" or "UNRELATED" - nothing else.
        """
        
        classification = self.llm.predict(classification_prompt).strip().upper()
        return classification == "RELATED"
    
    def handle_general_question(self, user_question: str) -> str:
        """
        Handle general questions not related to the SAT problem
        """
        general_prompt = f"""
        You are a helpful AI assistant. A student using an SAT practice app has asked you a question that's not directly related to their current SAT practice problem.
        
        Student's question: {user_question}
        
        Respond helpfully and conversationally, but also gently remind them that you're primarily here to help with their SAT practice. If appropriate, try to relate your response back to learning or test preparation.
        
        Be friendly, helpful, and encouraging while staying focused on your role as an educational assistant.
        """
        
        return self.llm.predict(general_prompt)
    
    def get_contextual_guidance(self, question: SATQuestion, user_question: str, chat_history: List[dict] = None):
        """
        Provide guidance based on the specific question context and user's ask
        """
        question_context = {
            "id": question.id,
            "section": question.section,
            "domain": question.domain,
            "difficulty": question.difficulty,
            "question_text": question.question_text,
            "paragraph": question.paragraph,
            "choices": {
                "A": question.choice_a,
                "B": question.choice_b,
                "C": question.choice_c,
                "D": question.choice_d
            },
            "correct_answer": question.correct_answer,
            "explanation": question.explanation
        }
        
        # First, check if the question is related to the SAT problem
        if not self.is_question_related(user_question, question_context):
            return self.handle_general_question(user_question)
        
        # Build conversation context
        conversation_context = ""
        if chat_history:
            for msg in chat_history[-5:]:  # Last 5 messages for context
                conversation_context += f"User: {msg.get('user', '')}\nTutor: {msg.get('tutor', '')}\n"
        
        # Create guidance prompt based on question type
        if question.section == "Math":
            return self.get_math_guidance(question_context, user_question, conversation_context)
        else:
            return self.get_english_guidance(question_context, user_question, conversation_context)
    
    def get_math_guidance(self, question_context: dict, user_question: str, conversation_context: str):
        """
        Provide step-by-step math guidance without revealing the answer
        """
        guidance_prompt = f"""
        You are a patient SAT math tutor helping a student with a specific practice question.
        
        QUESTION CONTEXT:
        Domain: {question_context['domain']}
        Difficulty: {question_context['difficulty']}
        Question: {question_context['question_text']}
        Answer Choices: {question_context['choices']}
        
        PREVIOUS CONVERSATION:
        {conversation_context}
        
        STUDENT'S CURRENT QUESTION: {user_question}
        
        TUTORING GUIDELINES:
        1. DO NOT reveal the correct answer directly
        2. Guide them through the problem-solving process step by step
        3. If they ask for a hint, give the smallest helpful hint
        4. If they're stuck, break down the problem into smaller parts
        5. If they have the wrong approach, gently redirect them
        6. Encourage their thinking and validate correct partial steps
        7. Use COMPUTE[expression] when you need to calculate something
        
        RESPONSE TYPES based on what they're asking:
        - If asking for a hint: Give the next logical step without solving
        - If asking to check their work: Evaluate their approach and give feedback
        - If asking for explanation: Explain the concept, not the specific answer
        - If completely lost: Help them identify what the question is asking
        
        Respond as their helpful tutor, using encouraging language and Socratic questioning to guide their learning.
        Make sure that in the end, you don't reveal the answer.
        """
        
        # Use the existing math tutor but with modified prompt for guidance
        response = self.math_tutor.solve(guidance_prompt)
        return response
    
    def get_english_guidance(self, question_context: dict, user_question: str, conversation_context: str):
        """
        Provide step-by-step English guidance without revealing the answer
        """
        guidance_prompt = f"""
        You are a patient SAT English tutor helping a student with a specific practice question.
        
        QUESTION CONTEXT:
        Domain: {question_context['domain']}
        Difficulty: {question_context['difficulty']}
        Question: {question_context['question_text']}
        {f"Passage: {question_context['paragraph']}" if question_context['paragraph'] else ""}
        Answer Choices: {question_context['choices']}
        
        PREVIOUS CONVERSATION:
        {conversation_context}
        
        STUDENT'S CURRENT QUESTION: {user_question}
        
        TUTORING GUIDELINES:
        1. DO NOT reveal the correct answer directly
        2. Help them analyze the passage and question systematically
        3. If they ask for a hint, point them to relevant parts of the text
        4. If they're stuck, help them eliminate obviously wrong choices
        5. Guide them to understand what the question is really asking
        6. Use ANALYZE[type: description] when you need deep text analysis
        7. Teach them strategies for similar questions
        
        RESPONSE TYPES based on what they're asking:
        - If asking for a hint: Point to key words/phrases in the question or passage
        - If asking to check their reasoning: Evaluate their logic without giving the answer
        - If asking for strategy: Teach them how to approach this type of question
        - If confused about question: Help them parse what it's asking
        
        Guide their learning with thoughtful questions and encouragement.
        """
        
        # Use existing English tutor with guidance-focused prompt
        passage = question_context.get('paragraph', '')
        response = self.english_tutor.solve(guidance_prompt, passage)
        return response
    
    # ... rest of your existing methods remain the same ...
    def provide_step_by_step(self, question: SATQuestion, step_requested: str, user_attempt: str = None):
        """
        Provide specific types of help based on what step the user requests
        """
        question_context = {
            "question_text": question.question_text,
            "paragraph": question.paragraph,
            "choices": {
                "A": question.choice_a,
                "B": question.choice_b,
                "C": question.choice_c,
                "D": question.choice_d
            },
            "section": question.section,
            "domain": question.domain
        }
        
        if step_requested == "hint":
            return self.provide_hint(question_context)
        elif step_requested == "next_step":
            return self.provide_next_step(question_context, user_attempt)
        elif step_requested == "explanation":
            return self.provide_concept_explanation(question_context)
        elif step_requested == "check_answer":
            return self.check_user_answer(question_context, user_attempt)
        else:
            return {"error": "Invalid step requested"}
    
    def provide_hint(self, question_context: dict):
        """Provide the smallest helpful hint"""
        prompt = f"""
        Give the student a small hint for this SAT question. Don't solve it for them.
        
        Question: {question_context['question_text']}
        {f"Passage: {question_context['paragraph']}" if question_context.get('paragraph') else ""}
        
        Provide just enough guidance to get them thinking in the right direction.
        Format: "Hint: [your hint here]"
        """
        
        response = self.llm.predict(prompt)
        return {
            "step_type": "hint",
            "content": response,
            "is_final_answer": False,
            "next_available_steps": ["next_step", "explanation", "check_answer"]
        }
    
    def provide_next_step(self, question_context: dict, user_attempt: str):
        """Guide them to the next logical step"""
        prompt = f"""
        The student is working on this problem and has attempted: "{user_attempt}"
        
        Question: {question_context['question_text']}
        {f"Passage: {question_context['paragraph']}" if question_context.get('paragraph') else ""}
        
        Guide them to the next step in solving this problem. Don't give the final answer.
        Acknowledge their attempt and suggest what to do next.
        """
        
        response = self.llm.predict(prompt)
        return {
            "step_type": "next_step",
            "content": response,
            "is_final_answer": False,
            "next_available_steps": ["hint", "explanation", "check_answer"]
        }
    
    def provide_concept_explanation(self, question_context: dict):
        """Explain the underlying concept without solving the specific problem"""
        prompt = f"""
        Explain the key concept needed to solve this type of SAT question.
        
        Question Type: {question_context['section']} - {question_context['domain']}
        Question: {question_context['question_text']}
        
        Explain the concept clearly with examples, but don't solve this specific question.
        Help them understand the general approach for similar problems.
        """
        
        response = self.llm.predict(prompt)
        return {
            "step_type": "explanation",
            "content": response,
            "is_final_answer": False,
            "next_available_steps": ["hint", "next_step", "check_answer"]
        }
    
    def check_user_answer(self, question_context: dict, user_attempt: str):
        """Evaluate their answer attempt and provide feedback"""
        prompt = f"""
        The student chose "{user_attempt}" for this SAT question.
        
        Question: {question_context['question_text']}
        Choices: {question_context['choices']}
        
        Without revealing the correct answer, give them feedback on their choice.
        - If correct: Confirm and explain why it's right
        - If incorrect: Gently explain why this choice doesn't work and guide them toward the right approach
        
        Be encouraging and educational.
        """
        
        response = self.llm.predict(prompt)
        return {
            "step_type": "check_answer",
            "content": response,
            "is_final_answer": False,
            "next_available_steps": ["hint", "next_step", "explanation"]
        }