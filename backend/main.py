import os
import json
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

import database
import schemas

# --- DB SETUP ---
from database import engine, Base
Base.metadata.create_all(bind=engine)

# --- APP ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GEMINI CLIENT (STABLE) ---
# IMPORTANT:
# - Uses default API version
# - Uses gemini-pro (ONLY stable text model)
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# --- SUBMIT FEEDBACK ---
@app.post("/api/submit", response_model=schemas.SubmissionResponse)
async def submit_feedback(
    request: schemas.SubmissionRequest,
    db: Session = Depends(database.get_db)
):
    prompt = f"""
You are an AI assistant analyzing user feedback for a product or service.

Input:
- Rating (1 to 5): {request.rating}
- Review text: {request.review_text}

Task:
Return ONLY a valid JSON object with EXACTLY these keys:

{{
  "user_reply": "",
  "summary": "",
  "actions": []
}}

Rules:
- No markdown
- No explanations
- No extra text
- Output must be valid JSON only
- Tone based on rating:
  - 1–2: apologetic and corrective
  - 3: neutral and improvement-focused
  - 4–5: appreciative and reinforcing positives
"""

    try:
        response = client.models.generate_content(
            model="gemini-pro",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        # Parse Gemini output
        if response.parsed:
            ai_data = response.parsed
        else:
            ai_data = json.loads(response.text)

        entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text[:1000],
            ai_user_response=ai_data.get(
                "user_reply", "Thank you for your feedback!"
            ),
            ai_summary=ai_data.get(
                "summary", "Feedback received."
            ),
            ai_actions=ai_data.get(
                "actions", ["Manual review recommended"]
            )
        )

        db.add(entry)
        db.commit()

        return {
            "status": "success",
            "ai_user_response": entry.ai_user_response
        }

    except Exception as e:
        # Graceful fallback (MANDATORY)
        print("AI ERROR:", str(e))

        fallback = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text[:1000],
            ai_user_response="Thank you for your feedback!",
            ai_summary="AI processing failed",
            ai_actions=["Manual review required"]
        )

        db.add(fallback)
        db.commit()

        return {
            "status": "partial_success",
            "ai_user_response": "Thank you for your feedback!"
        }

# --- ADMIN LIST ---
@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    return (
        db.query(database.FeedbackRecord)
        .order_by(database.FeedbackRecord.created_at.desc())
        .all()
    )

# --- ROOT ---
@app.get("/")
async def root():
    return {"message": "AI Feedback API running"}
