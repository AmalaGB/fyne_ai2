import os
import json
import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from google import genai 
from google.genai import types 
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

# Initialize Client - Explicitly using the Gemini API Key
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.post("/api/submit", response_model=schemas.SubmissionResponse)
async def submit_feedback(request: schemas.SubmissionRequest, db: Session = Depends(database.get_db)):
    try:
        # THE FIX: Try 'gemini-1.5-flash-8b' or 'gemini-1.5-flash'. 
        # If 'models/...' failed, we use the bare string.
        response = client.models.generate_content(
            model='gemini-1.5-flash-8b', 
            contents=f"Rating: {request.rating}/5. Review: {request.review_text}",
            config=types.GenerateContentConfig(
                system_instruction="You are a feedback analyzer. Return ONLY JSON.",
                response_mime_type="application/json"
            )
        )

        # Handling different response formats
        if hasattr(response, 'parsed') and response.parsed:
            ai_data = response.parsed
        else:
            # Manual extraction
            clean_text = response.text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            ai_data = json.loads(clean_text)

        new_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response=ai_data.get('user_reply', "Thank you for your feedback!"),
            ai_summary=ai_data.get('summary', "Review processed."),
            ai_actions=ai_data.get('actions', [])
        )
        db.add(new_entry)
        db.commit()
        return {"status": "success", "ai_user_response": ai_data.get('user_reply', "Success")}

    except Exception as e:
        print(f"!!! DIAGNOSTIC ERROR: {str(e)}")
        
        # Fallback record so the dashboard still shows the review
        fallback_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response="Thank you!",
            ai_summary="AI Processing Error (Check Logs)",
            ai_actions=["Manual Review Required"]
        )
        db.add(fallback_entry)
        db.commit()
        return {"status": "partial_success", "ai_user_response": "Thank you!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    return db.query(database.FeedbackRecord).order_by(database.FeedbackRecord.created_at.desc()).all()