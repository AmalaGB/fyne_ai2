import os
import json
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
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

SYSTEM_PROMPT = """
You are a Senior Strategic Product Manager and Customer Success Analyst. 

TASK:
Analyze user feedback and convert it into high-level business intelligence.

COLUMN GUIDELINES:
1. "summary" (AI ANALYSIS):
   - Identify the underlying business theme (e.g., "Critical UX Friction," "Service Latency").
   - 1-2 Stars: Focus on the "Failure Point".
   - 3 Stars: Focus on the "Gap" or "Trade-off".
   - 4-5 Stars: Focus on the "Competitive Advantage".

2. "actions" (NEXT STEPS):
   - Provide 2-3 professional, actionable tasks using verbs like "Audit," "Optimize," or "Investigate."

OUTPUT RULES:
- Return ONLY a single valid JSON object. No code blocks or preamble.
- Keys: "user_reply", "summary", "actions".
""".strip()

# --- ROUTES ---

@app.get("/")
async def health_check():
    return {"status": "running", "message": "API is live"}

@app.post("/api/submit", response_model=schemas.SubmissionResponse)
async def submit_feedback(request: schemas.SubmissionRequest, db: Session = Depends(database.get_db)):
    try:
        # Generate structured AI analysis with correct v1 SDK parameters
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=f"Rating: {request.rating}/5. Review: {request.review_text}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json"
            )
        )

        # Use the SDK's built-in parser
        ai_data = response.parsed if response.parsed else json.loads(response.text)

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
        db.rollback()
        print(f"!!! DIAGNOSTIC ERROR: {str(e)}")
        # Professional fallback for UI
        return {"status": "partial_success", "ai_user_response": "Thank you for your feedback!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    """Retrieve all feedback for the dashboard"""
    return db.query(database.FeedbackRecord).order_by(database.FeedbackRecord.id.desc()).all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
