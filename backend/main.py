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
        # FIX: Changed model string to 'models/gemini-1.5-flash'
        response = client.models.generate_content(
            model='models/gemini-1.5-flash', 
            contents=f"Rating: {request.rating}/5. Review: {request.review_text}",
            config=types.GenerateContentConfig(
                system_instruction="Analyze feedback. Return ONLY JSON: {'user_reply': '...', 'summary': '...', 'actions': ['...']}",
                response_mime_type="application/json"
            )
        )

        # Robust Parsing
        if response.parsed:
            ai_data = response.parsed
        else:
            # Fallback for older SDK versions
            ai_data = json.loads(response.text.replace("```json", "").replace("```", "").strip())

        new_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response=ai_data.get('user_reply', "Thank you!"),
            ai_summary=ai_data.get('summary', "Review processed."),
            ai_actions=ai_data.get('actions', [])
        )
        db.add(new_entry)
        db.commit()
        return {"status": "success", "ai_user_response": ai_data.get('user_reply')}

    except Exception as e:
        # Log the actual error to Render
        print(f"!!! DIAGNOSTIC ERROR: {str(e)}")
        
        fallback_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response="Thank you for your feedback!",
            ai_summary="AI Analysis Pending",
            ai_actions=["Manual check needed"]
        )
        db.add(fallback_entry)
        db.commit()
        return {"status": "partial_success", "ai_user_response": "Thank you for your feedback!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    return db.query(database.FeedbackRecord).order_by(database.FeedbackRecord.created_at.desc()).all()