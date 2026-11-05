"""Resilient simulation service for Drishti (converted from mockService.js)."""
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..schemas.vision_schemas import (
        VisionAssistResult,
        DetectedObject,
        TextReading,
        CurrencyDetection,
    )
    from ..schemas.chat_schemas import ChatResult
except (ImportError, ValueError):
    from src.schemas.vision_schemas import (
        VisionAssistResult,
        DetectedObject,
        TextReading,
        CurrencyDetection,
    )
    from src.schemas.chat_schemas import ChatResult

LOCALIZED_ALERTS = {
    "en": {
        "safety_clear": "Path is clear. You can safely walk 3 meters forward.",
        "safety_obstacle": "Chair detected 1.5 meters ahead at 11 o'clock. Step right.",
        "read": "Sign reads: Room 204 Doctor Consultation Office.",
        "currency": "Indian Rupee 500 note detected. Mahatma Gandhi series.",
        "chat_reply": "You are currently facing a quiet indoor hallway. Ahead of you is a clear tiled floor. On your right at 2 o'clock is an open wooden door. No immediate hazards are in your path.",
        "chat_spoken": "You are in a hallway. Clear floor ahead, open door on your right.",
    },
    "hi": {
        "safety_clear": "रास्ता साफ़ है। आप सुरक्षित रूप से 3 मीटर आगे बढ़ सकते हैं।",
        "safety_obstacle": "11 बजे की दिशा में 1.5 मीटर आगे कुर्सी है। दाईं ओर मुड़ें।",
        "read": "बोर्ड पर लिखा है: कमरा 204 डॉक्टर परामर्श कक्ष।",
        "currency": "भारतीय 500 रुपये का नोट पहचाना गया। महात्मा गांधी श्रृंखला।",
        "chat_reply": "आप एक शांत हॉलवे में हैं। आपके आगे का फ़र्श साफ़ है। आपके दाईं ओर 2 बजे की दिशा में एक खुला दरवाज़ा है। कोई ख़तरा नहीं है।",
        "chat_spoken": "रास्ता साफ़ है। आगे का फ़र्श खुला है और दाईं ओर दरवाज़ा है।",
    },
    "kn": {
        "safety_clear": "ದಾರಿ ಸ್ಪಷ್ಟವಾಗಿದೆ. ನೀವು ಸುರಕ್ಷಿತವಾಗಿ 3 ಮೀಟರ್ ಮುಂದಕ್ಕೆ ನಡೆಯಬಹುದು.",
        "safety_obstacle": "11 ಗಂಟೆಯ ದಿಕ್ಕಿನಲ್ಲಿ 1.5 ಮೀಟರ್ ದೂರದಲ್ಲಿ ಕುರ್ಚಿ ಇದೆ. ಬಲಕ್ಕೆ ಹೆಜ್ಜೆ ಇಡಿ.",
        "read": "ಫಲಕದಲ್ಲಿದೆ: ಕೊಠಡಿ 204 ವೈದ್ಯರ ಸಮಾಲೋಚನಾ ಕೊಠಡಿ.",
        "currency": "500 ರೂಪಾಯಿ ಭಾರತೀಯ ನೋಟು ಪತ್ತೆಯಾಗಿದೆ.",
        "chat_reply": "ನೀವು ಶಾಂತವಾದ ಹಜಾರದಲ್ಲಿದ್ದೀರಿ. ಮುಂದೆ ಯಾವುದೇ ಅಡೆತಡೆಗಳಿಲ್ಲ. ನಿಮ್ಮ ಬಲಭಾಗದಲ್ಲಿ ಬಾಗಿಲು ತೆರೆದಿದೆ.",
        "chat_spoken": "ದಾರಿ ಸ್ಪಷ್ಟವಾಗಿದೆ. ಮುಂದುವರಿಯಿರಿ, ಬಲಭಾಗದಲ್ಲಿ ಬಾಗಿಲಿದೆ.",
    },
    "te": {
        "safety_clear": "దారి స్పష్టంగా ఉంది. మీరు సురಕ್ಷితంగా 3 మీటర్లు ముందుకు నడవవచ్చు.",
        "safety_obstacle": "11 గంటల దిశలో 1.5 మీటర్ల దూరంలో కుర్చీ ఉంది. కుడివైపుకి అడుగు వేయండి.",
        "read": "బోర్డుపై ఉంది: గది 204 డాక్టర్ సంప్రదింపు గది.",
        "currency": "భారతీయ 500 రూపాయల నోటు గుర్తించబడింది.",
        "chat_reply": "మీరు ప్రశాంతమైన హాలులో ఉన్నారు. మీ ముందు దారి ఖాళీగా ఉంది. కుడివైపున తలుపు తెరిచి ఉంది.",
        "chat_spoken": "దారి స్పష్టంగా ఉంది. మీ కుడివైపున తలుపు ఉంది.",
    },
    "ta": {
        "safety_clear": "பாதை தெளிவாக உள்ளது. நீங்கள் 3 மீட்டர் முன்னோக்கி நடக்கலாம்.",
        "safety_obstacle": "11 மணி திசையில் 1.5 மீட்டர் தொலைவில் நாற்காலி உள்ளது. வலதுபுறம் செல்லவும்.",
        "read": "பலகையில் உள்ளது: அறை 204 மருத்துவர் ஆலோசனை அறை.",
        "currency": "இந்திய 500 ரூபாய் நோட்டு கண்டறியப்பட்டது.",
        "chat_reply": "நீங்கள் ஒரு அமைதியான நடைபாதையில் உள்ளீர்கள். பாதை தெளிவாக உள்ளது. உங்கள் வலதுபுறம் ஒரு கதவு திறந்துள்ளது.",
        "chat_spoken": "பாதை தெளிவாக உள்ளது. வலதுபுறம் கதவு திறந்துள்ளது.",
    },
}


LOCALIZED_ACTIONS = {
    "en": "Demo sample only: stop and verify the path with your mobility aid.",
    "hi": "यह केवल डेमो नमूना है: रुकें और अपने सहायक साधन से रास्ता जाँचें।",
    "kn": "ಇದು ಡೆಮೋ ಮಾದರಿ ಮಾತ್ರ: ನಿಲ್ಲಿಸಿ, ನಿಮ್ಮ ಸಹಾಯಕ ಸಾಧನದಿಂದ ದಾರಿಯನ್ನು ಪರಿಶೀಲಿಸಿ.",
    "te": "ఇది డెమో నమూనా మాత్రమే: ఆగి, మీ సహాయక పరికరంతో దారిని తనిఖీ చేయండి.",
    "ta": "இது டெமோ மாதிரி மட்டுமே: நின்று, உங்கள் உதவி சாதனத்தால் பாதையைச் சரிபார்க்கவும்.",
    "mr": "हा केवळ डेमो नमुना आहे: थांबा आणि आपल्या सहाय्यक साधनाने मार्ग तपासा.",
    "bn": "এটি শুধু ডেমো নমুনা: থামুন এবং আপনার সহায়ক উপকরণ দিয়ে পথ যাচাই করুন।",
    "gu": "આ માત્ર ડેમો નમૂનો છે: થોભો અને તમારા સહાયક સાધનથી રસ્તો તપાસો.",
    "ml": "ഇത് ഡെമോ മാതൃക മാത്രമാണ്: നിർത്തി നിങ്ങളുടെ സഹായ ഉപകരണം ഉപയോഗിച്ച് വഴി പരിശോധിക്കുക."
}

def get_mock_vision_assist(
    mode: str = "safety",
    language: str = "en",
    user_prompt: str = ""
) -> VisionAssistResult:
    lang = (language or "en").lower().split("-")[0]
    dict_msg = LOCALIZED_ALERTS.get(lang, LOCALIZED_ALERTS["en"])

    if mode == "read":
        return VisionAssistResult(
            spokenAlert=dict_msg["read"],
            isPathClear=True,
            immediateAction="You may proceed or listen to details",
            hazardSeverity="none",
            detectedObjects=[
                DetectedObject(
                    label="door signage",
                    clockPosition="12 o'clock",
                    distanceMeters=1.8,
                    severity="none",
                    box2d=[200, 250, 450, 750],
                )
            ],
            textReadings=[
                TextReading(
                    text="ROOM 204 - DOCTOR CONSULTATION",
                    category="signboard",
                    confidence=0.98,
                    box2d=[220, 270, 410, 720],
                ),
                TextReading(
                    text="TIMINGS: 9:00 AM - 1:00 PM",
                    category="signboard",
                    confidence=0.95,
                    box2d=[420, 310, 480, 680],
                ),
            ],
            currencyDetected=CurrencyDetection(present=False),
            sceneSummary="Wall with wooden office door and clinic consultation signage plate mounted at eye level.",
            safetyNote="Flat indoor surface. No trip hazards detected near the door.",
            isDemoMode=True,
        )

    if mode == "currency":
        return VisionAssistResult(
            spokenAlert=dict_msg["currency"],
            isPathClear=True,
            immediateAction="Hold note steady to verify watermarks if needed",
            hazardSeverity="none",
            detectedObjects=[
                DetectedObject(
                    label="banknote",
                    clockPosition="12 o'clock",
                    distanceMeters=0.35,
                    severity="none",
                    box2d=[300, 180, 700, 820],
                )
            ],
            textReadings=[
                TextReading(
                    text="RESERVE BANK OF INDIA - 500",
                    category="document",
                    confidence=0.99,
                    box2d=[320, 210, 420, 780],
                )
            ],
            currencyDetected=CurrencyDetection(
                present=True,
                currency="INR",
                denomination=500.0,
                confidence=0.97,
                description="Stone grey Mahatma Gandhi new series 500 Rupee note with Red Fort motif on reverse.",
            ),
            sceneSummary="Hand holding a genuine Indian Rupee 500 banknote under good indoor lighting.",
            safetyNote="Safe stationary position.",
            isDemoMode=True,
        )

    # Safety mode
    prompt_lower = (user_prompt or "").lower()
    has_chemical = any(w in prompt_lower for w in ["acid", "bleach", "bleaching", "chemical", "poison", "cleaner", "toxic"])
    has_biological = any(w in prompt_lower for w in ["insect", "spider", "scorpion", "wasp", "bee", "centipede", "fungus", "mold", "cockroach"])
    has_sharp = any(w in prompt_lower for w in ["sharp", "knife", "scissor", "blade", "razor", "needle", "glass", "nail", "pin", "stapler", "bed"])
    has_obstacle = "clear" not in prompt_lower

    if has_chemical:
        return VisionAssistResult(
            spokenAlert="Danger: Chemical hazard or acid bottle detected ahead. Do not touch.",
            isPathClear=False,
            immediateAction="Stop: corrosive chemical detected, keep distance and avoid touching",
            hazardSeverity="high",
            sharpHazardDetected=False,
            chemicalHazardDetected=True,
            biologicalHazardDetected=False,
            hazardCategories=["chemical"],
            surfaceAlert="Corrosive chemical or acid container on surface",
            detectedObjects=[
                DetectedObject(
                    label="acid / chemical bottle",
                    clockPosition="12 o'clock",
                    distanceMeters=1.0,
                    severity="high",
                    isChemicalHazard=True,
                    hazardCategory="chemical",
                    surfaceLocation="floor",
                    box2d=[400, 450, 750, 620],
                )
            ],
            textReadings=[],
            currencyDetected=CurrencyDetection(present=False),
            sceneSummary="Chemical or corrosive substance container identified on floor.",
            safetyNote="Corrosive hazard. Risk of skin burns and inhalation danger.",
            isDemoMode=True,
        )

    if has_biological:
        return VisionAssistResult(
            spokenAlert="Caution: Insect or fungal growth detected on surface. Avoid contact.",
            isPathClear=False,
            immediateAction="Pause: inspect surface before sitting or touching",
            hazardSeverity="high",
            sharpHazardDetected=False,
            chemicalHazardDetected=False,
            biologicalHazardDetected=True,
            hazardCategories=["biological"],
            surfaceAlert="Biological pest or fungus detected on surface",
            detectedObjects=[
                DetectedObject(
                    label="insect / fungus",
                    clockPosition="1 o'clock",
                    distanceMeters=0.6,
                    severity="high",
                    isBiologicalHazard=True,
                    hazardCategory="biological",
                    surfaceLocation="bed" if "bed" in prompt_lower else "surface",
                    box2d=[350, 500, 550, 700],
                )
            ],
            textReadings=[],
            currencyDetected=CurrencyDetection(present=False),
            sceneSummary="Biological pest or fungal patch detected on surface.",
            safetyNote="Bite, sting, or allergen hazard.",
            isDemoMode=True,
        )

    if has_sharp:
        return VisionAssistResult(
            spokenAlert="Warning: Sharp object detected on surface. Do not touch or step.",
            isPathClear=False,
            immediateAction="Pause: check surface carefully with an aid before touching",
            hazardSeverity="high",
            sharpHazardDetected=True,
            chemicalHazardDetected=False,
            biologicalHazardDetected=False,
            hazardCategories=["sharp"],
            surfaceAlert="Sharp cutting hazard lying on surface",
            detectedObjects=[
                DetectedObject(
                    label="sharp blade / knife / stapler pin",
                    clockPosition="1 o'clock",
                    distanceMeters=0.8,
                    severity="high",
                    isSharpHazard=True,
                    hazardCategory="sharp",
                    surfaceLocation="bed" if "bed" in prompt_lower else "floor",
                    box2d=[420, 520, 680, 820],
                )
            ],
            textReadings=[],
            currencyDetected=CurrencyDetection(present=False),
            sceneSummary="Surface inspection identified a sharp cutting object lying exposed.",
            safetyNote="High puncture or laceration hazard. Never sit or step on surface blindly.",
            isDemoMode=True,
        )

    return VisionAssistResult(
        spokenAlert=dict_msg["safety_obstacle"] if has_obstacle else dict_msg["safety_clear"],
        isPathClear=not has_obstacle,
        immediateAction=LOCALIZED_ACTIONS.get(lang, LOCALIZED_ACTIONS["en"]),
        hazardSeverity="medium" if has_obstacle else "none",
        sharpHazardDetected=False,
        chemicalHazardDetected=False,
        biologicalHazardDetected=False,
        hazardCategories=[],
        surfaceAlert=None,
        detectedObjects=[
            DetectedObject(
                label="office chair",
                clockPosition="11 o'clock",
                distanceMeters=1.5,
                severity="medium",
                box2d=[380, 150, 850, 480],
            ),
            DetectedObject(
                label="open hallway",
                clockPosition="1 o'clock",
                distanceMeters=3.5,
                severity="none",
                box2d=[200, 520, 920, 950],
            ),
        ] if has_obstacle else [
            DetectedObject(
                label="clear path",
                clockPosition="12 o'clock",
                distanceMeters=3.0,
                severity="none",
                box2d=[400, 250, 980, 750],
            )
        ],
        textReadings=[],
        currencyDetected=CurrencyDetection(present=False),
        sceneSummary="Indoor corridor with an office chair partially encroaching the left side of your walking path." if has_obstacle else "Open, flat walkway with no obstacles within 3 meters.",
        safetyNote="Keep white cane extended 2 feet in front to confirm floor transitions.",
        isDemoMode=True,
    )

def get_mock_chat_response(message: str = "", language: str = "en") -> ChatResult:
    lang = (language or "en").lower().split("-")[0]
    dict_msg = LOCALIZED_ALERTS.get(lang, LOCALIZED_ALERTS["en"])

    return ChatResult(
        reply=dict_msg["chat_reply"],
        spokenText=dict_msg["chat_spoken"],
        suggestedActions=[
            "Is the floor wet or uneven?",
            "Read any signs nearby",
            "Guide me to the door on the right",
        ],
        urgency="normal",
        isDemoMode=True,
    )
