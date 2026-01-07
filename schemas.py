from pydantic import BaseModel, Field
from typing import List, Optional

class SubmissionRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    review_text: str = Field(..., min_length=1, max_length=2000)

class SubmissionResponse(BaseModel):
    status: str
    ai_user_response: str

class AdminRecord(BaseModel):
    id: int
    rating: int
    review_text: str
    ai_summary: str
    ai_actions: List[str]
    created_at: str

    class Config:
        orm_mode = True