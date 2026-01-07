import os
import json
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from google import genai 
from google.genai import types 

import database, schemas
from database import engine, Base

# Create tables in Neon PostgreSQL
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(api_version='v1')
)

SYSTEM_PROMPT = """
You are a Senior Strategic Product Manager and Customer Success Analyst. 

TASK:
Analyze the user's feedback (Rating and Review) and convert it into high-level business intelligence.

COLUMN GUIDELINES:
1. "summary" (AI ANALYSIS Column):
   - Do NOT just repeat the review. 
   - Identify the underlying sentiment or business theme (e.g., "Critical UX Friction," "Service Latency," "Product Validation").
   - 1-2 Stars: Focus on the "Failure Point".
   - 3 Stars: Focus on the "Gap" or "Trade-off".
   - 4-5 Stars: Focus on the "Competitive Advantage".

2. "actions" (NEXT STEPS Column):
   - Provide a list of 2-3 professional, actionable business tasks.
   - Use professional verbs: "Audit," "Optimize," "Investigate," "Incorporate," "Incentivize."

OUTPUT RULES:
- Return ONLY a single valid JSON object.
- NO code fences (```), no backticks, no preamble.
- JSON Keys: "user_reply", "summary", "actions".

EXAMPLE FOR 3-STARS ("Dark mode needed"):
{
  "user_reply": "Thanks for the suggestion! We've logged this feature request for our design team.",
  "summary": "Functional satisfaction is currently limited by a specific UI/UX customization gap (Dark Mode).",
  "actions": ["Prioritize Dark Mode in Q3 UI Roadmap", "Audit existing accessibility themes"]
}
""".strip()




@app.get("/")
async def health_check():
    return {"status": "running", "docs": "/docs"}

@app.post("/api/submit", response_model=schemas.SubmissionResponse)
async def submit_feedback(request: schemas.SubmissionRequest, db: Session = Depends(database.get_db)):
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=f"Rating: {request.rating}/5. Review: {request.review_text}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json"
            )
        )

        ai_data = response.parsed if response.parsed else json.loads(response.text.strip().replace("```json", "").replace("```", ""))

        new_entry = database.FeedbackRecord(
            rating=request.rating,
            review_text=request.review_text,
            ai_user_response=ai_data.get('user_reply'),
            ai_summary=ai_data.get('summary'),
            ai_actions=ai_data.get('actions', [])
        )
        db.add(new_entry)
        db.commit()
        
        return {"status": "success", "ai_user_response": ai_data.get('user_reply')}

    except Exception as e:
        db.rollback()
        return {"status": "error", "ai_user_response": "Thank you for your feedback!"}

@app.get("/api/admin/list")
async def list_feedback(db: Session = Depends(database.get_db)):
    return db.query(database.FeedbackRecord).order_by(database.FeedbackRecord.id.desc()).all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
