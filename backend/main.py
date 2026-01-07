import os
import json
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

# Explicitly initialize the client for Google AI (not Vertex AI)
# Ensure GEMINI_API_KEY is your key from AI Studio
client = genai.Client(api_key=os.getenv("AIzaSyA1wDoksDgybCSOkdkCreE1UI4IWbHjQBI"))

@app.post("/api/submit", response_model=schemas.SubmissionResponse)
async def submit_feedback(request: schemas.SubmissionRequest, db: Session = Depends(database.get_db)):
    try:
        # ACCURATE MODEL NAME: Use 'gemini-1.5-flash' directly.
        # This is the standard string for the v1beta generateContent endpoint.
        response = client.models.generate_content(
            model='gemini-pro', 
            contents=f"Rating: {request.rating}/5. Review: {request.review_text}",
            config=types.GenerateContentConfig(
                system_instruction="You are a feedback analyzer. Return ONLY JSON.",
                response_mime_type="application/json"
            )
        )

        # Handle the parsed response correctly
        # The latest SDK uses .parsed for JSON mode
        if response.parsed:
            ai_data = response.parsed
        else:
            # Manual fallback if parsed is unavailable
            clean_text = response.text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            ai_data = json.loads(clean_text)

        # Success: Save to Database
        new_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response=ai_data.get('user_reply', "Thank you for your feedback!"),
            ai_summary=ai_data.get('summary', "Review received and processed."),
            ai_actions=ai_data.get('actions', [])
        )
        db.add(new_entry)
        db.commit()
        return {"status": "success", "ai_user_response": ai_data.get('user_reply')}

    except Exception as e:
        # Logging for your Render console
        print(f"!!! DIAGNOSTIC ERROR: {str(e)}")
        
        # Professional Fallback
        fallback_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response="Thank you for your feedback!",
            ai_summary="AI Analysis Pending",
            ai_actions=["Manual review needed"]
        )
        db.add(fallback_entry)
        db.commit()
        return {"status": "partial_success", "ai_user_response": "Thank you for your feedback!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    return db.query(database.FeedbackRecord).order_by(database.FeedbackRecord.created_at.desc()).all()
