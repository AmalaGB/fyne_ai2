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
    max_retries = 3
    retry_delay = 2 
    
    for attempt in range(max_retries):
        try:
            # Generate content using Gemini 1.5 Flash
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=f"Rating: {request.rating}/5. Review: {request.review_text}",
                config=types.GenerateContentConfig(
                    system_instruction="""
                    You are a feedback analyzer. 
                    Output ONLY raw JSON. No markdown, no backticks.
                    Expected format:
                    {
                        "user_reply": "string",
                        "summary": "string",
                        "actions": ["string", "string"]
                    }
                    """,
                    response_mime_type="application/json"
                )
            )

            # Parse AI response
            try:
                ai_data = response.parsed if response.parsed else json.loads(response.text)
            except Exception:
                ai_data = {
                    "user_reply": "Thank you for your rating!",
                    "summary": "User provided a rating.",
                    "actions": []
                }

            # Save to Database
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

        except exceptions.ResourceExhausted:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
                continue
            break 
        except Exception as e:
            print(f"!!! REAL AI ERROR: {type(e).__name__} - {str(e)}")
            break 

    # FINAL FALLBACK
    fallback_entry = database.FeedbackRecord(
        rating=request.rating,
        review_text=request.review_text,
        ai_user_response="Thank you for your feedback!",
        ai_summary="AI Busy (Rate Limit)",
        ai_actions=[]
    )
    db.add(fallback_entry)
    db.commit()
    return {"status": "partial_success", "ai_user_response": "Thank you for your feedback!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    return db.query(database.FeedbackRecord).order_by(database.FeedbackRecord.created_at.desc()).all()