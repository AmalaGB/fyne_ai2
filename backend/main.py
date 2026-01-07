import os
import json
import uvicorn
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

# --- THE STABLE SETUP ---
# We force 'v1' to avoid the 'v1beta' 404 errors.
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(api_version='v1')
)

@app.post("/api/submit", response_model=schemas.SubmissionResponse)
async def submit_feedback(request: schemas.SubmissionRequest, db: Session = Depends(database.get_db)):
    try:
        # Use the base production model name
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
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
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
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
        print(f"!!! DIAGNOSTIC ERROR: {str(e)}")
        # Save record even on AI failure so you don't lose customer data
        fallback = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response="Thank you for your feedback!",
            ai_summary="AI Analysis Pending",
            ai_actions=["Manual review"]
        )
        db.add(fallback)
        db.commit()
        return {"status": "partial_success", "ai_user_response": "Thank you!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    return db.query(database.FeedbackRecord).order_by(database.FeedbackRecord.created_at.desc()).all()
@app.get("/")
async def root():
    return {"message": "AI Feedback API is running. Go to /docs for API documentation."}
# --- RENDER PORT BINDING ---
if __name__ == "__main__":
    # Render sets the PORT env var; we must listen on 0.0.0.0
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)