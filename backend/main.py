import os
import json
import time
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from google import genai 
from google.genai import types 
from google.api_core import exceptions # Important for catching rate limits
import database, schemas

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
    retry_delay = 2  # Initial wait time in seconds
    
    for attempt in range(max_retries):
        try:
            # Using 1.5-flash for more stable rate limits on free tier
            response = client.models.generate_content(
                model='gemini-1.5-flash-8b', 
                contents=f"Analyze feedback: {request.rating}/5 stars. Text: {request.review_text}",
                config=types.GenerateContentConfig(
                    system_instruction="""
                    You are a feedback analyzer. Respond ONLY with a JSON object.
                    {
                        "user_reply": "short polite reply",
                        "summary": "1 sentence summary",
                        "actions": ["action 1", "action 2"]
                    }
                    """,
                    response_mime_type="application/json"
                )
            )

            ai_data = response.parsed if response.parsed else json.loads(response.text)

            # Success: Save to Database
            new_entry = database.FeedbackRecord(
                rating=request.rating,
                review_text=request.review_text,
                ai_user_response=ai_data.get('user_reply', "Thank you!"),
                ai_summary=ai_data.get('summary', "Summary processed"),
                ai_actions=ai_data.get('actions', [])
            )
            db.add(new_entry)
            db.commit()

            return {"status": "success", "ai_user_response": ai_data.get('user_reply', "Thank you!")}

        except exceptions.ResourceExhausted:
            # If we hit a rate limit (429), wait and try again
            if attempt < max_retries - 1:
                print(f"Rate limit hit. Retrying in {retry_delay}s... (Attempt {attempt + 1})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Wait longer next time
                continue
            else:
                break # Give up and use fallback after 3 tries

        except Exception as e:
            print(f"AI ERROR: {str(e)}")
            break # Go to fallback for other errors

    # FINAL FALLBACK: If AI fails or is exhausted
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