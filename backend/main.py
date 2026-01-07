import os
import json
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from google import genai 
from google.genai import types 

# Internal imports
import database, schemas
from database import engine, Base

# Initialize Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Feedback Analysis System")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AI CONFIGURATION ---
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(api_version='v1')
)

# Structured Prompt (PROMPT_V3)
SYSTEM_PROMPT = """
You are a senior Customer Success Analyst. 

Rules:
1. Return ONLY a single JSON object.
2. Keys: "user_reply" (empathetic response), "summary" (brief internal notes), "actions" (list of tasks).
3. No code fences (```), no backticks, no preamble.

Example:
Review: "App is great but keeps crashing."
Output: {"user_reply": "Thanks for the feedback! We are fixing the crash.", "summary": "Positive sentiment with technical bug.", "actions": ["Fix checkout crash"]}
""".strip()

# --- ROUTES ---

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "AI Feedback API is running.",
        "docs": "/docs"
    }

@app.post("/api/submit", response_model=schemas.SubmissionResponse)
async def submit_feedback(request: schemas.SubmissionRequest, db: Session = Depends(database.get_db)):
    try:
        # Generate structured AI analysis
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=f"Rating: {request.rating}/5. Review: {request.review_text}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json"
            )
        )

        # Parse JSON response
        if response.parsed:
            ai_data = response.parsed
        else:
            # Fallback for raw text cleanup
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
            ai_data = json.loads(clean_text)

        # Create Database Record
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
        # Graceful degradation: Save raw data if AI fails
        fallback = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response="Thank you for your feedback!",
            ai_summary="AI Analysis Pending (Service Error)",
            ai_actions=["Manual review required"]
        )
        db.add(fallback)
        db.commit()
        return {"status": "partial_success", "ai_user_response": "Thank you for your feedback!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    """Retrieve all feedback records for the dashboard"""
    return db.query(database.FeedbackRecord).order_by(database.FeedbackRecord.id.desc()).all()

# --- SERVER STARTUP ---
if __name__ == "__main__":
    # Ensure the app binds to 0.0.0.0 and the port provided by Render
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)