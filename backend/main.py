import os
import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import google.generativeai as genai
import database, schemas

app = FastAPI()

# Enable CORS for Next.js dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific Vercel URLs
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@app.post("/api/submit", response_model=schemas.SubmissionResponse)
async def submit_feedback(request: schemas.SubmissionRequest, db: Session = Depends(database.get_db)):
    try:
        # AI Prompt Logic
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Analyze feedback: {request.rating}/5 stars. Text: {request.review_text}
        Return JSON format: 
        {{
            "user_reply": "polite reply to user",
            "summary": "1 sentence for admin",
            "actions": ["action 1", "action 2"]
        }}
        """
        response = model.generate_content(prompt)
        ai_data = json.loads(response.text.replace('```json', '').replace('```', ''))

        # Save to Neon Database
        new_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response=ai_data['user_reply'],
            ai_summary=ai_data['summary'],
            ai_actions=ai_data['actions']
        )
        db.add(new_entry)
        db.commit()

        return {"status": "success", "ai_user_response": ai_data['user_reply']}

    except Exception as e:
        # Graceful Failure: Save raw data even if AI fails
        fallback_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response="Thank you for your feedback!",
            ai_summary="AI processing failed.",
            ai_actions=[]
        )
        db.add(fallback_entry)
        db.commit()
        return {"status": "partial_success", "ai_user_response": "Thank you for your feedback!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    return db.query(database.FeedbackRecord).all()