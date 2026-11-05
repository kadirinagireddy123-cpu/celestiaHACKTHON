# Drishti: Voice & Vision AI - Assistive Python Backend

> **Empowering Visually Impaired Users with Real-Time Multimodal Intelligence**  
> Developed for **CELESTIA: 24-Hour National Hackathon** by **Team Tech Trojan**  
> Ballari Institute of Technology & Management

---

## 🌟 Overview

**Drishti** is an assistive AI backend built in **Python with FastAPI** designed to provide blind and low-vision individuals with safe, independent mobility and environmental awareness. Powered by Google Gemini multimodal models (`google-genai` and `google-generativeai`), Drishti processes camera frames and voice queries to deliver real-time, hands-free spoken guidance in multiple Indian and international languages.

---

## 🚀 Key Features

1. **Obstacle & Safety Navigation (`/vision-assist` with `mode: "safety"`)**:
   - Detects physical hazards, ground drop-offs, stairs, furniture, and pedestrians.
   - Provides clock-face spatial positioning (e.g. `11 o'clock`, `12 o'clock`).
   - Estimates distance in meters.
   - Flags severity (`none`, `low`, `medium`, `high`).
   - Speaks an urgent, actionable spoken alert **under 15 words**.
   - Generates normalized bounding boxes (`[ymin, xmin, ymax, xmax]`, 0-1000 scale) for UI visualization overlay.

2. **OCR & Sign Reading (`/vision-assist` with `mode: "read"`)**:
   - Transcribes visible printed and handwritten text.
   - Categorizes text (medicine labels, door plates, signboards, expiry dates, menus).

3. **Banknote & Currency Recognition (`/vision-assist` with `mode: "currency"`)**:
   - Rapidly identifies banknote denominations (Indian Rupee ₹10, ₹20, ₹50, ₹100, ₹200, ₹500, USD, etc.).
   - Provides tactile and visual verification notes (Mahatma Gandhi series, color, bleed lines).

4. **Conversational Surroundings Q&A (`/chat`)**:
   - Hands-free conversational assistance with context memory.
   - Answers natural spoken questions like *"What is that bottle in my hand?"* or *"Can I walk forward safely?"*.
   - Directional, tactile, blind-friendly descriptions without sighted clichés.

5. **Multilingual Speech & Audio (`/tts` & `/languages`)**:
   - Language-aware outputs in English, Hindi (हिन्दी), Kannada (ಕನ್ನಡ), Telugu (తెలుగు), Tamil (தமிழ்), Marathi (मराठी), Bengali (বাংলা), Gujarati, Malayalam, Spanish, French, and more.
   - Server-side audio synthesis with instant fallback metadata for the browser's native `SpeechSynthesis`.

6. **Interactive OpenAPI / Swagger Documentation**:
   - Interactive UI available at `http://localhost:5000/docs` and `http://localhost:5000/redoc`.

7. **Engineered Resilience & Demo Mode**:
   - Built-in model fallback chain: Primary `gemini-2.5-flash` falls back to `gemini-1.5-flash`.
   - **Resilient Demo Mode**: If no API key is set, the server runs in zero-configuration simulation mode with realistic responses and bounding boxes—ensuring uninterrupted live demos and pitch tests.
   - 30MB payload limit for ultra-high-resolution camera frames.

---

## 🛠 Tech Stack

- **Runtime**: Python 3.10+ (tested on Python 3.14)
- **Framework**: FastAPI + Starlette ASGI
- **Server**: Uvicorn
- **Multimodal AI**: Official `google-genai` & `google-generativeai` with strict Pydantic schemas (`response_schema`)
- **Validation**: Pydantic v2
- **Documentation**: Automatic OpenAPI / Swagger UI at `/docs`

---

## 📋 API Endpoints

### 1. Vision Assist
- **URL**: `POST /vision-assist` (or `POST /api/vision-assist`)
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "image": "data:image/jpeg;base64,...",
  "mode": "safety", // "safety" | "read" | "currency" | "all"
  "language": "en", // "en", "hi", "kn", "te", "ta", etc.
  "userPrompt": "Is the pathway clear?" // optional
}
```
- **Response**:
```json
{
  "success": true,
  "timestamp": "2026-11-05T12:00:00.000Z",
  "mode": "safety",
  "language": "en",
  "data": {
    "spokenAlert": "Chair detected 1.5 meters ahead at 11 o'clock. Step right.",
    "isPathClear": false,
    "immediateAction": "Step right to avoid chair",
    "hazardSeverity": "medium",
    "detectedObjects": [
      {
        "label": "office chair",
        "clockPosition": "11 o'clock",
        "distanceMeters": 1.5,
        "severity": "medium",
        "box2d": [380, 150, 850, 480]
      }
    ],
    "textReadings": [],
    "currencyDetected": { "present": false },
    "sceneSummary": "Indoor corridor with an office chair partially encroaching the left side of your walking path.",
    "safetyNote": "Keep white cane extended 2 feet in front to confirm floor transitions.",
    "isDemoMode": false
  }
}
```

---

### 2. Conversational Q&A
- **URL**: `POST /chat` (or `POST /api/chat`)
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "message": "Where is the door?",
  "history": [
    { "role": "user", "text": "Describe my surroundings." },
    { "role": "model", "text": "You are in an office hallway." }
  ],
  "language": "en",
  "image": "data:image/jpeg;base64,..." // optional current frame
}
```

---

### 3. Text-to-Speech (TTS)
- **URL**: `POST /tts` (or `POST /api/tts`)
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "text": "Obstacle 1 meter ahead.",
  "language": "hi",
  "voice": "female"
}
```

---

### 4. System Diagnostics & Languages
- **Health Check**: `GET /health` (or `/api/health`)
- **Languages List**: `GET /languages` (or `/api/languages`)
- **Assistive Modes**: `GET /modes` (or `/api/modes`)
- **Interactive Swagger Docs**: `GET /docs`

---

## ⚙️ Setup and Running

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and set your Gemini API Key from Google AI Studio:
```env
GEMINI_API_KEY=AIzaSy...
PORT=5000
```
*(If `GEMINI_API_KEY` is left blank, Drishti automatically runs in fully responsive **Demo Mode** with realistic simulations!)*

### 3. Start the Server
```bash
# Direct run
python server.py

# Or via main
python main.py

# Or via Uvicorn CLI
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

### 4. Run Automated Tests
```bash
python -m unittest discover tests
```

---

## 👥 Team Tech Trojan
- **Nagireddy K** (Team Lead) – Gemini API, Prompts & Architecture
- **Prajwal B Naik** – Frontend Developer (React, TypeScript, Bounding Box UI)
- **Venkatesha D K** – Voice & Accessibility (Multilingual Audio, Speech)
- **Pranay Raj** – Testing, UX & Presentation
