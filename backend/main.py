import os
import json
import asyncio
from fastapi import FastAPI, Depends, HTTPException
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
    # 1. Validation: Gemini sometimes fails on empty or 1-character reviews
    review_content = request.review_text if len(request.review_text) > 2 else f"User gave a {request.rating} star rating."

    try:
        # 2. Call Gemini with the most stable settings
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"Rating: {request.rating}/5. Review: {review_content}",
            config=types.GenerateContentConfig(
                system_instruction="Analyze feedback. Return ONLY JSON: {'user_reply': '...', 'summary': '...', 'actions': ['...']}",
                response_mime_type="application/json"
            )
        )

        # 3. Handle the response
        if response.parsed:
            ai_data = response.parsed
        else:
            ai_data = json.loads(response.text)

        # 4. Success Path: Save to Database
        new_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response=ai_data.get('user_reply', "Thank you for your feedback!"),
            ai_summary=ai_data.get('summary', "Review processed successfully."),
            ai_actions=ai_data.get('actions', [])
        )
        db.add(new_entry)
        db.commit()
        return {"status": "success", "ai_user_response": ai_data.get('user_reply')}

    except Exception as e:
        # This will show the EXACT error in your Render logs (e.g., 429 Resource Exhausted)
        print(f"!!! CRITICAL AI ERROR: {str(e)}")
        
        # 5. Fallback Path: Save as 'Pending' instead of 'Busy' to make it look better
        fallback_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response="Thank you! Your feedback has been received.",
            ai_summary="Analysis Pending (Provider Limit)",
            ai_actions=["Manual review required"]
        )
        db.add(fallback_entry)
        db.commit()
        return {"status": "partial_success", "ai_user_response": "Thank you for your feedback!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    return db.query(database.FeedbackRecord).order_by(database.FeedbackRecord.created_at.desc()).all()