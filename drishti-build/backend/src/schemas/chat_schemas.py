"""Pydantic schemas for Conversational Q&A (converted from chatSchemas.js)."""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: Literal["user", "model", "assistant"] = Field(..., description="Role of the speaker")
    text: str = Field(..., description="Content of the message")

class ChatResult(BaseModel):
    reply: str = Field(
        ...,
        description="Compassionate, descriptive, directional guidance tailored for a blind user."
    )
    spokenText: str = Field(
        ...,
        description="Short spoken version (1-2 sentences, max 30 words) for immediate speech readout."
    )
    suggestedActions: List[str] = Field(
        default_factory=list,
        description="2-3 helpful follow-up questions user can ask next."
    )
    urgency: Literal["normal", "warning", "critical"] = Field(
        "normal", description="Urgency level regarding physical safety"
    )
    isDemoMode: bool = Field(False, description="Whether this response was generated via demo simulation")
    fallbackReason: Optional[str] = Field(None, description="Reason for fallback if applicable")

class ChatRequest(BaseModel):
    message: Optional[str] = Field(None, description="User's spoken query transcribed to text")
    history: List[ChatMessage] = Field(default_factory=list, description="Recent conversation turns")
    language: str = Field("en", description="Target language code")
    image: Optional[str] = Field(None, description="Optional base64 camera frame for contextual Q&A")

class ChatResponse(BaseModel):
    success: bool = True
    timestamp: str
    language: str
    data: ChatResult

