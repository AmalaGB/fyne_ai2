import os
import json
import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from google import genai 
from google.genai import types 
from google.api_core import exceptions
import database, schemas

# Initialize Database
from database import engine, Base
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.post("/api/submit", response_model=schemas.SubmissionResponse)
async def submit_feedback(request: schemas.SubmissionRequest, db: Session = Depends(database.get_db)):
    try:
        # Request AI Analysis
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"Rating: {request.rating}/5. Review: {request.review_text}",
            config=types.GenerateContentConfig(
                system_instruction="Analyze feedback. Return ONLY JSON: {'user_reply': '...', 'summary': '...', 'actions': ['...']}",
                response_mime_type="application/json"
            )
        )

        # Robust JSON parsing
        text_content = response.text.strip()
        # Remove markdown code blocks if AI accidentally includes them
        if text_content.startswith("```json"):
            text_content = text_content.replace("```json", "").replace("```", "").strip()
        
        ai_data = json.loads(text_content)

        # Create Database Record
        new_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response=ai_data.get('user_reply', "Thanks for your feedback!"),
            ai_summary=ai_data.get('summary', "Review analyzed."),
            ai_actions=ai_data.get('actions', [])
        )
        db.add(new_entry)
        db.commit()
        return {"status": "success", "ai_user_response": ai_data.get('user_reply')}

    except Exception as e:
        print(f"!!! SYSTEM ERROR: {str(e)}")
        
        # Professional Fallback for the Dashboard
        error_summary = "AI Limit Reached" if "429" in str(e) else "Processing Pending"
        
        fallback_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response="Thank you! We have received your feedback.",
            ai_summary=error_summary,
            ai_actions=["Manual review recommended"]
        )
        db.add(fallback_entry)
        db.commit()
        return {"status": "partial_success", "ai_user_response": "Thank you for your feedback!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    return db.query(database.FeedbackRecord).order_by(database.FeedbackRecord.created_at.desc()).all()