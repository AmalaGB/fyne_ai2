import os
import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from google import genai  # NEW SDK
from google.genai import types # For configuration
import database, schemas

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the new Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.post("/api/submit", response_model=schemas.SubmissionResponse)
async def submit_feedback(request: schemas.SubmissionRequest, db: Session = Depends(database.get_db)):
    try:
        # Using the new model 'gemini-2.0-flash' for better JSON support
        # We specify the response_mime_type so the AI sends valid JSON directly
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=f"Analyze feedback: {request.rating}/5 stars. Text: {request.review_text}",
            config=types.GenerateContentConfig(
                system_instruction="""
                You are a feedback analyzer. You must respond ONLY with a JSON object.
                Structure: 
                {
                    "user_reply": "string",
                    "summary": "string",
                    "actions": ["list", "of", "strings"]
                }
                """,
                response_mime_type="application/json"
            )
        )

        # The new SDK provides a direct way to parse JSON if mime_type is set
        ai_data = response.parsed if response.parsed else json.loads(response.text)

        new_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response=ai_data.get('user_reply', "Thank you!"),
            ai_summary=ai_data.get('summary', "Summary not available"),
            ai_actions=ai_data.get('actions', [])
        )
        db.add(new_entry)
        db.commit()

        return {"status": "success", "ai_user_response": ai_data.get('user_reply', "Thank you!")}

    except Exception as e:
        print(f"AI ERROR: {str(e)}") # Critical for checking Render logs
        
        # Fallback logic
        fallback_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response="Thank you for your feedback!",
            ai_summary=f"AI Error: {str(e)[:50]}",
            ai_actions=[]
        )
        db.add(fallback_entry)
        db.commit()
        return {"status": "partial_success", "ai_user_response": "Thank you for your feedback!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    return db.query(database.FeedbackRecord).all()