"""Pydantic schemas for Vision Assistance (converted from visionSchemas.js)."""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class DetectedObject(BaseModel):
    label: str = Field(..., description="Name of the obstacle or object detected")
    clockPosition: str = Field(
        ...,
        description="Clock face direction relative to user (e.g. '12 o\'clock', '10 o\'clock', '2 o\'clock')"
    )
    distanceMeters: float = Field(..., description="Estimated distance in meters from user")
    severity: Literal["none", "low", "medium", "high"] = Field(
        "low", description="Severity level of the hazard"
    )
    isSharpHazard: bool = Field(
        False,
        description="True if this item is sharp, pointed, cutting, or piercing (knife, scissors, blade, broken glass, needle, nail, stapler pin, etc.)"
    )
    isChemicalHazard: bool = Field(
        False,
        description="True if item is corrosive, acidic, caustic, or toxic (acid bottle, bleaching powder, drain cleaner, pesticide)"
    )
    isBiologicalHazard: bool = Field(
        False,
        description="True if item is an insect, venomous pest (wasp, spider, scorpion, centipede), or visible mold/fungus"
    )
    hazardCategory: Optional[Literal["sharp", "chemical", "biological", "dropoff", "obstacle", "none"]] = Field(
        "none",
        description="Categorization of the detected hazard"
    )
    surfaceLocation: Optional[str] = Field(
        None,
        description="Surface where object is lying (e.g. 'bed', 'floor', 'carpet', 'table', 'chair', 'stairs', 'wall')"
    )
    box2d: List[int] = Field(
        ...,
        description="Normalized bounding box [ymin, xmin, ymax, xmax] scaled 0 to 1000"
    )

class TextReading(BaseModel):
    text: str = Field(..., description="Exact transcribed text")
    category: str = Field(
        ...,
        description="Category: 'signboard', 'medicine', 'door', 'menu', 'packaging', 'document', 'other'"
    )
    confidence: float = Field(0.95, description="OCR confidence score between 0.0 and 1.0")
    box2d: List[int] = Field(
        ...,
        description="Normalized bounding box [ymin, xmin, ymax, xmax] scaled 0 to 1000"
    )

class CurrencyDetection(BaseModel):
    present: bool = Field(False, description="Whether a banknote was identified")
    currency: Optional[str] = Field(None, description="Currency code (e.g. 'INR', 'USD')")
    denomination: Optional[float] = Field(None, description="Denomination value (e.g. 500, 100, 50)")
    confidence: Optional[float] = Field(None, description="Confidence score 0.0 to 1.0")
    description: Optional[str] = Field(None, description="Spoken description of the note with color or key identifiers")

class VisionAssistResult(BaseModel):
    spokenAlert: str = Field(
        ...,
        description="Crisp spoken warning or guidance for blind person. MUST be under 15 words."
    )
    isPathClear: bool = Field(
        ...,
        description="True if user can take at least 2 safe steps forward, false if blocked."
    )
    immediateAction: str = Field(
        ...,
        description="Short, actionable safety instruction in the selected language. Recommend a direction only if that side is visibly clear; otherwise say stop/pause and verify with cane or companion."
    )
    hazardSeverity: Literal["none", "low", "medium", "high"] = Field(
        "none", description="Highest severity of hazard in immediate path"
    )
    sharpHazardDetected: bool = Field(
        False,
        description="True if any sharp, cutting, pointed, or piercing item (knife, scissors, razor blade, broken glass, needle, pin, nail, stapler pin, shattered ceramic) is detected on any surface like bed, floor, carpet, sofa, chair, or table."
    )
    chemicalHazardDetected: bool = Field(
        False,
        description="True if corrosive chemicals, acids, bleaching powders, caustic toilet cleaners, drain unblockers, or pesticides are spotted."
    )
    biologicalHazardDetected: bool = Field(
        False,
        description="True if harmful insects (bees, wasps, spiders, scorpions, centipedes, bedbugs, cockroaches) or fungus/mold are detected."
    )
    hazardCategories: List[str] = Field(
        default_factory=list,
        description="List of active hazard categories in this scan: 'sharp', 'chemical', 'biological', 'dropoff', etc."
    )
    surfaceAlert: Optional[str] = Field(
        None,
        description="Specific spoken hazard alert for sharp, chemical, or biological items lying on bed, floor, or furniture in the target language (e.g. 'Caution: Razor blade on bed', 'Danger: Acid spill on floor', 'Warning: Insect on pillow')."
    )
    detectedObjects: List[DetectedObject] = Field(
        default_factory=list,
        description="List of detected obstacles and objects"
    )
    textReadings: List[TextReading] = Field(
        default_factory=list,
        description="List of text and signs read from the scene"
    )
    currencyDetected: CurrencyDetection = Field(
        default_factory=lambda: CurrencyDetection(present=False),
        description="Detected banknote details"
    )
    sceneSummary: str = Field(..., description="Objective 1-2 sentence overview of the environment")
    safetyNote: Optional[str] = Field(
        None, description="Mobility tip or safety reminder"
    )
    isDemoMode: bool = Field(False, description="Whether this response was generated via demo simulation")
    modelUsed: Optional[str] = Field(None, description="Model that produced this inference")
    fallbackReason: Optional[str] = Field(None, description="Reason for fallback if applicable")

class VisionAssistRequest(BaseModel):
    image: str = Field(..., description="Base64 encoded image string or data URL")
    mode: Literal["safety", "read", "currency", "all"] = Field(
        "safety", description="Operational assistive mode"
    )
    language: str = Field("en", description="Target language code (e.g. 'en', 'hi', 'kn', 'te', 'ta')")
    userPrompt: Optional[str] = Field("", description="Optional user spoken question or instruction")

class VisionAssistResponse(BaseModel):
    success: bool = True
    timestamp: str
    mode: str
    language: str
    data: VisionAssistResult

