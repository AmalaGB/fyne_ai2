import os
import json
import asyncio # Changed from time
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
            # Using the 8b model for the highest possible free-tier stability
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=f"Rating: {request.rating}/5. Review: {request.review_text}",
                config=types.GenerateContentConfig(
                    system_instruction="Return ONLY a JSON object: {\"user_reply\": \"...\", \"summary\": \"...\", \"actions\": []}",
                    response_mime_type="application/json"
                )
            )

            # Safely parse the response
            try:
                ai_data = response.parsed if response.parsed else json.loads(response.text)
            except:
                # Emergency fallback if JSON parsing fails
                ai_data = {
                    "user_reply": "Thank you for your rating!",
                    "summary": "User provided a rating.",
                    "actions": []
                }

            # Success: Save to Database
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
                # CRITICAL: Use asyncio.sleep instead of time.sleep
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                break 

        except Exception as e:
            print(f"DEBUG ERROR: {str(e)}")
            break 

    # FINAL FALLBACK (Saves to DB even if AI is dead)
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