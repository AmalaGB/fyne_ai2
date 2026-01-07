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

# ACCURATE INITIALIZATION: Force API version 'v1' to avoid v1beta 404s
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(api_version='v1')
)

@app.post("/api/submit", response_model=schemas.SubmissionResponse)
async def submit_feedback(request: schemas.SubmissionRequest, db: Session = Depends(database.get_db)):
    try:
        # Use the most stable production model name
        response = client.models.generate_content(
            model='gemini-pro', 
            contents=f"Rating: {request.rating}/5. Review: {request.review_text}",
            config=types.GenerateContentConfig(
                system_instruction="Analyze feedback. Return ONLY JSON: {'user_reply': '...', 'summary': '...', 'actions': ['...']}",
                response_mime_type="application/json"
            )
        )

        # Extraction logic
        if response.parsed:
            ai_data = response.parsed
        else:
            clean_text = response.text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            ai_data = json.loads(clean_text)

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
        print(f"!!! FINAL DIAGNOSTIC ERROR: {str(e)}")
        # Save record even on failure
        db.add(database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response="Thank you for your feedback!",
            ai_summary="Analysis Pending (Provider Limit)",
            ai_actions=["Manual review required"]
        ))
        db.commit()
<<<<<<< HEAD
        return {"status": "partial_success", "ai_user_response": "Thank you!"}
=======
        return {"status": "partial_success", "ai_user_response": "Thank you for your feedback!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    return db.query(database.FeedbackRecord).order_by(database.FeedbackRecord.created_at.desc()).all()
>>>>>>> 640bf58091b0579d12cc61ec0a48e77d990d59dd
