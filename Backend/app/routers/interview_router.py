"""
Interview router for mock interviews and practice sessions.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json
import re

from app.database.session import get_db
from app.models import User, Resume, InterviewSession, InterviewQuestion, InterviewAnswer
from app.schemas.ai import (
    InterviewSessionCreate,
    InterviewAnswerSubmit,
    InterviewQuestionResponse,
    InterviewSessionResponse,
    InterviewAnswerResponse,
    QuestionGenerationRequest
)
from app.utils.dependencies import get_current_user
from app.services.ai_services.interview_ai import generate_interview_questions
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/interview", tags=["Interview"])

# Rate limiting configuration
RATE_LIMIT_SECONDS = 60  # Minimum seconds between feedback requests
MAX_ANSWER_LENGTH = 5000  # Maximum characters for answer text

# ==================== Helper Functions ====================

def validate_answer_text(answer_text: Optional[str]) -> str:
    """Validate and sanitize answer text."""
    if not answer_text or not answer_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Answer text cannot be empty"
        )
    if len(answer_text) > MAX_ANSWER_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Answer text exceeds maximum length of {MAX_ANSWER_LENGTH} characters"
        )
    # Basic sanitization - remove potential script tags
    sanitized = re.sub(r'<script.*?</script>', '', answer_text, flags=re.DOTALL | re.IGNORECASE)
    return sanitized.strip()


def check_rate_limit(last_feedback_time: Optional[str]) -> bool:
    """Check if enough time has passed since last feedback request."""
    if not last_feedback_time:
        return True
    try:
        last_time = datetime.fromisoformat(last_feedback_time)
        return datetime.now() - last_time > timedelta(seconds=RATE_LIMIT_SECONDS)
    except (ValueError, TypeError):
        return True


# ==================== Endpoints ====================

from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: Optional[str] = "career_assistant"

@router.post("/ai-chat")
async def ai_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI Career Assistant chat endpoint.
    """
    try:
        # Build prompt from conversation history
        history_str = "\n".join([f"{m.role}: {m.content}" for m in request.messages])
        
        prompt = f"""
You are an expert AI Career Assistant for GrobsAI. Your goal is to help the user with their career, resume, interviews, and professional growth.
Be professional, encouraging, and provide specific, actionable advice.

Conversation history:
{history_str}

Assistant:"""

        # Use LLM service to generate response
        response = llm_service.generate_text(prompt)
        
        return {"reply": response.content}
    except Exception as e:
        print(f"Error in AI Chat: {e}")
        # Fallback response if LLM fails
        return {"reply": "I'm having a bit of trouble connecting to my brain right now. Could you try rephrasing your question?"}

@router.post("/questions")
async def generate_questions(
    request: QuestionGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate interview questions based on resume and job description.
    """
    resume = None
    if request.resume_id:
        resume = db.query(Resume).filter(
            Resume.id == request.resume_id,
            Resume.user_id == current_user.id
        ).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
    
    # Use the existing interview AI service
    if resume:
        questions_data = generate_interview_questions(resume, request.job_description or "")
    else:
        # Generate generic questions if no resume
        questions_data = {
            'role': request.job_title or 'general',
            'interview_structure': {
                'behavioral_questions': [
                    {'question': 'Tell me about yourself.', 'tips': 'Use the present-past-future format'},
                    {'question': 'What are your strengths?', 'tips': 'Pick strengths relevant to the job'},
                    {'question': 'Where do you see yourself in 5 years?', 'tips': 'Show ambition and alignment'},
                ],
                'technical_questions': [],
                'role_specific_questions': [],
                'job_specific_questions': [],
            },
            'preparation_tips': [
                'Research the company',
                'Practice the STAR method',
                'Prepare questions for the interviewer',
            ]
        }
    
    # Flatten questions for the API response as expected by the frontend/tests
    all_questions = []
    structure = questions_data.get('interview_structure', {})
    
    for category in ['behavioral_questions', 'technical_questions', 'role_specific_questions', 'job_specific_questions']:
        for q in structure.get(category, []):
            q_copy = q.copy()
            q_copy['type'] = category.replace('_questions', '')
            all_questions.append(q_copy)
            
    return all_questions


@router.post("/sessions", response_model=InterviewSessionResponse)
async def create_session(
    session_data: InterviewSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new mock interview session.
    """
    # Verify resume belongs to user if provided
    resume = None
    if session_data.resume_id:
        resume = db.query(Resume).filter(
            Resume.id == session_data.resume_id,
            Resume.user_id == current_user.id
        ).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
    
    # Create session
    session = InterviewSession(
        user_id=current_user.id,
        resume_id=session_data.resume_id,
        job_title=session_data.job_title,
        company=session_data.company,
        job_description=session_data.job_description,
        question_count=session_data.question_count,
        interview_type=session_data.interview_type,
        status="in_progress",
        current_question_index=0,
        started_at=datetime.now().isoformat()
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Generate questions based on resume or generic
    if resume:
        questions_data = generate_interview_questions(resume, session_data.job_description or "")
    else:
        questions_data = {
            'role': session_data.job_title or 'general',
            'interview_structure': {
                'behavioral_questions': [
                    {'question': 'Tell me about yourself.', 'tips': 'Use the present-past-future format'},
                    {'question': 'What are your strengths?', 'tips': 'Pick strengths relevant to the job'},
                ],
                'technical_questions': [],
                'role_specific_questions': [],
                'job_specific_questions': [],
            },
        }
    
    # Add questions to session
    all_questions = []
    
    # Add behavioral questions
    for i, q in enumerate(questions_data.get('interview_structure', {}).get('behavioral_questions', [])[:3]):
        question = InterviewQuestion(
            session_id=session.id,
            question_text=q.get('question', ''),
            question_type='behavioral',
            category='star',
            order_index=len(all_questions),
            tips=q.get('tips'),
            focus_areas=q.get('focus_areas'),
            created_at=datetime.now().isoformat()
        )
        db.add(question)
        all_questions.append(question)
    
    # Add technical questions
    for q in questions_data.get('interview_structure', {}).get('technical_questions', [])[:2]:
        question = InterviewQuestion(
            session_id=session.id,
            question_text=q.get('question', ''),
            question_type='technical',
            category='technical',
            order_index=len(all_questions),
            tips=q.get('tips'),
            focus_areas=q.get('focus_areas'),
            created_at=datetime.now().isoformat()
        )
        db.add(question)
        all_questions.append(question)
    
    # Add role-specific questions
    for q in questions_data.get('interview_structure', {}).get('role_specific_questions', [])[:2]:
        question = InterviewQuestion(
            session_id=session.id,
            question_text=q.get('question', ''),
            question_type='role_specific',
            category='role',
            order_index=len(all_questions),
            tips=q.get('tips'),
            focus_areas=q.get('focus_areas'),
            created_at=datetime.now().isoformat()
        )
        db.add(question)
        all_questions.append(question)
    
    # Ensure we have at least some questions
    if not all_questions:
        # Add fallback questions
        fallback_questions = [
            "Tell me about yourself and why you're interested in this role.",
            "Describe a challenging project you worked on.",
            "What are your greatest strengths and weaknesses?",
        ]
        for i, q_text in enumerate(fallback_questions):
            question = InterviewQuestion(
                session_id=session.id,
                question_text=q_text,
                question_type='behavioral',
                category='general',
                order_index=i,
                tips='Be concise and relevant',
                created_at=datetime.now().isoformat()
            )
            db.add(question)
    
    db.commit()
    db.refresh(session)
    
    return session


@router.get("/sessions", response_model=List[InterviewSessionResponse])
async def get_sessions(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, description="Limit results"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all interview sessions for current user.
    """
    query = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    )
    
    if status:
        query = query.filter(InterviewSession.status == status)
    
    sessions = query.order_by(InterviewSession.created_at.desc()).limit(limit).all()
    return sessions


@router.get("/sessions/{session_id}", response_model=InterviewSessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific interview session.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.get("/sessions/{session_id}/questions", response_model=List[InterviewQuestionResponse])
async def get_session_questions(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all questions for a session.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id
    ).order_by(InterviewQuestion.order_index).all()
    
    return [
        {
            "id": q.id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "category": q.category,
            "order_index": q.order_index,
            "tips": q.tips,
            "focus_areas": q.focus_areas,
            "answered": q.answer is not None
        }
        for q in questions
    ]


@router.post("/sessions/{session_id}/answer")
async def submit_answer(
    session_id: int,
    answer_data: InterviewAnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit an answer to a question.
    """
    # Validate answer text
    validated_answer_text = validate_answer_text(answer_data.answer_text)
    
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Session already completed")
    
    # Get the question
    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == answer_data.question_id,
        InterviewQuestion.session_id == session_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check if answer already exists and has feedback (prevent resubmission after feedback)
    existing_answer = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session_id,
        InterviewAnswer.question_id == answer_data.question_id
    ).first()
    
    if existing_answer and existing_answer.feedback:
        raise HTTPException(
            status_code=400, 
            detail="Answer already submitted and feedback provided. Cannot resubmit."
        )
    
    if existing_answer:
        # Update existing answer (only if no feedback yet)
        existing_answer.answer_text = validated_answer_text
        existing_answer.time_taken_seconds = answer_data.time_taken_seconds
        answer = existing_answer
    else:
        # Create new answer
        answer = InterviewAnswer(
            session_id=session_id,
            question_id=answer_data.question_id,
            answer_text=validated_answer_text,
            time_taken_seconds=answer_data.time_taken_seconds
        )
        db.add(answer)
    
    db.commit()
    
    # Update session progress - count answered questions instead of using order_index
    answered_count = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session_id,
        InterviewAnswer.answer_text.isnot(None)
    ).count()
    
    total_questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id
    ).count()
    
    session.current_question_index = answered_count
    
    # Check if all questions have been answered
    if answered_count >= total_questions:
        session.status = "completed"
        session.completed_at = datetime.now().isoformat()
    
    db.commit()
    
    return {"message": "Answer submitted successfully", "session": session}


@router.post("/sessions/{session_id}/feedback/{question_id}")
async def get_question_feedback(
    session_id: int,
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI feedback for a specific answer.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get the answer
    answer = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session_id,
        InterviewAnswer.question_id == question_id
    ).first()
    
    if not answer or not answer.answer_text:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    # Generate AI feedback if not already generated
    if not answer.feedback:
        try:
            # Get the question
            question = db.query(InterviewQuestion).filter(
                InterviewQuestion.id == question_id
            ).first()
            
            # Generate feedback using LLM
            prompt = f"""
Provide professional feedback for this interview answer. 

Question: {question.question_text}
Question Type: {question.question_type}
Answer: {answer.answer_text}

Analyze the answer based on:
1. Relevancy: How well it addresses the question.
2. Structure: Use of STAR method (for behavioral) or technical depth (for technical).
3. Tone: Professionalism and confidence level.
4. Language: Use of action verbs and impact-oriented results.

Provide feedback in this JSON format:
{{
    "score": <score 0-100>,
    "feedback": "<detailed constructive feedback>",
    "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "improvements": ["<area for improvement 1>", "<area for improvement 2>"],
    "suggested_improvements": ["<specific rephrased example or suggestion 1>", "<specific suggestion 2>"],
    "tone_analysis": "<analysis of the tone and confidence>",
    "filler_words_detected": ["<filler word if any, or empty list>"]
}}
"""
            
            response = llm_service.generate_structured_output(
                prompt=prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "score": {"type": "number"},
                        "feedback": {"type": "string"},
                        "strengths": {"type": "array", "items": {"type": "string"}},
                        "improvements": {"type": "array", "items": {"type": "string"}},
                        "suggested_improvements": {"type": "array", "items": {"type": "string"}},
                        "tone_analysis": {"type": "string"},
                        "filler_words_detected": {"type": "array", "items": {"type": "string"}}
                    }
                }
            )
            
            if isinstance(response, dict):
                answer.score = response.get('score', 0)
                answer.feedback = response.get('feedback', '')
                answer.strengths = response.get('strengths', [])
                answer.improvements = response.get('improvements', [])
                answer.suggested_improvements = response.get('suggested_improvements', [])
                answer.tone_analysis = response.get('tone_analysis', '')
                answer.filler_words_detected = response.get('filler_words_detected', [])
                
                db.commit()
                
        except Exception as e:
            print(f"Error generating feedback: {e}")
            # Provide fallback feedback
            answer.score = 70
            answer.feedback = "Good attempt! Consider being more specific with examples."
            answer.strengths = ["Clear communication"]
            answer.improvements = ["Add more specifics"]
            answer.suggested_improvements = ["Use the STAR method"]
            db.commit()
    
    return {
        "question_id": question_id,
        "answer": {
            "answer_text": answer.answer_text,
            "score": answer.score,
            "feedback": answer.feedback,
            "strengths": answer.strengths,
            "improvements": answer.improvements,
            "suggested_improvements": answer.suggested_improvements,
            "tone_analysis": answer.tone_analysis,
            "filler_words_detected": answer.filler_words_detected,
            "time_taken_seconds": answer.time_taken_seconds
        }
    }


@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete an interview session and get overall feedback.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Calculate overall score
    answers = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session_id
    ).all()
    
    if answers:
        scores = [a.score for a in answers if a.score is not None]
        if scores:
            session.overall_score = sum(scores) / len(scores)
    
    session.status = "completed"
    session.completed_at = datetime.now().isoformat()
    db.commit()
    
    # Generate summary feedback
    total_questions = len(answers)
    answered_questions = len([a for a in answers if a.answer_text])
    
    session.feedback_summary = f"You completed {answered_questions} out of {total_questions} questions. "
    if session.overall_score:
        session.feedback_summary += f"Overall score: {session.overall_score:.0f}%"
    
    db.commit()
    
    return {
        "session": session,
        "summary": session.feedback_summary,
        "answers_count": answered_questions,
        "total_questions": total_questions
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an interview session.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}

