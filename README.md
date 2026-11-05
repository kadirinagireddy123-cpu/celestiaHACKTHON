# 👁️ Drishti — Multilingual Guided Walk with Voice & Vision AI

> **Empowering Visually Impaired Users with Real-Time Multimodal Intelligence**  
> Developed for **CELESTIA: 24-Hour National Hackathon** by **Team Tech Trojan**  
> Ballari Institute of Technology & Management

---

## 🌟 Overview

**Drishti** (दृष्टि / ದೃಷ್ಟಿ) is an assistive AI application designed to provide blind and low-vision individuals with safe, independent mobility and environmental awareness. Powered by Google Gemini multimodal models (`gemini-3.5-flash`), Drishti processes camera frames and voice queries to deliver real-time, hands-free spoken guidance in multiple Indian and international languages.

---

## ✨ Key Features

1. **Obstacle & Safety Navigation (`mode: "safety"`)**:
   - Detects physical hazards, ground drop-offs, stairs, furniture, pedestrians, and vehicles.
   - Provides clock-face spatial positioning (e.g., `11 o'clock`, `12 o'clock`).
   - Estimates distance in meters and severity flags (`none`, `low`, `medium`, `high`).
   - Speaks concise, urgent spoken alerts **under 15 words**.
   - Generates normalized bounding boxes (`[ymin, xmin, ymax, xmax]`, 0-1000 scale) for visual overlay.

2. **OCR & Sign Reading (`mode: "read"`)**:
   - Transcribes visible printed and handwritten text.
   - Categorizes text (medicine labels, door plates, signboards, expiry dates, menus).

3. **Banknote & Currency Recognition (`mode: "currency"`)**:
   - Rapidly identifies banknote denominations (Indian Rupee ₹10, ₹20, ₹50, ₹100, ₹200, ₹500, USD, etc.).
   - Provides tactile and visual verification notes (Mahatma Gandhi series, color, bleed lines).

4. **Conversational Surroundings Q&A (`/chat`)**:
   - Hands-free conversational assistance with context memory.
   - Answers natural spoken questions like *"What is that bottle in my hand?"* or *"Can I walk forward safely?"*.

5. **Multilingual Speech & Audio (`/tts` & `/languages`)**:
   - Language-aware guidance in English, Hindi (हिन्दी), Kannada (ಕನ್ನಡ), Telugu (తెలుగు), Tamil (தமிழ்), Marathi (मराठी), Bengali (বাংলা), Gujarati, Malayalam, Spanish, French, German, and Japanese.
   - Server-side audio synthesis with instant fallback to browser native `SpeechSynthesis`.

6. **Interactive OpenAPI / Swagger Documentation**:
   - Interactive UI available at `/docs` and `/redoc`.

---

## 🏗️ Architecture

```
drishti-multilingual-guided-walk/
├── README.md               # Root repository documentation
├── start.bat               # One-click startup script (Windows)
├── .gitignore              # Git ignore rules (protects API keys & caches)
└── drishti-build/
    ├── backend/            # FastAPI Vision & Voice AI Backend
    │   ├── server.py       # Uvicorn server entrypoint
    │   ├── requirements.txt # Python dependencies
    │   ├── .env.example    # Environment configuration template
    │   ├── src/
    │   │   ├── app.py      # FastAPI application factory
    │   │   ├── config/     # Environment & language configurations
    │   │   ├── routes/     # Vision, chat, TTS, and info endpoints
    │   │   ├── schemas/    # Pydantic v2 schemas
    │   │   ├── services/   # Gemini multimodal & mock services
    │   │   └── utils/      # Prompt templates & image utilities
    │   └── tests/          # Unit and integration tests
    └── frontend/           # Modern assistive web interface
        ├── index.html      # Responsive accessible UI
        ├── styles.css      # High-contrast, WCAG-compliant styling
        └── js/             # API client, app controller, speech recognition & TTS
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Google Gemini API key ([Google AI Studio](https://aistudio.google.com/))

### 2. Setup & Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd drishti-multilingual-guided-walk

# Navigate to backend
cd drishti-build/backend

# Create and activate virtual environment (optional but recommended)
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_gemini_api_key
```

### 3. Run the Application

#### One-Click Launch (Windows):
Double-click `start.bat` in the root folder.

#### Or Manual Launch:

**Terminal 1 (Backend):**
```bash
cd drishti-build/backend
python server.py
```

**Terminal 2 (Frontend):**
```bash
cd drishti-build/frontend
python -m http.server 8080
```

Open **`http://localhost:5000`** (or `http://localhost:8080`) in your web browser.

---

## 🧪 Testing

Run backend test suite:
```bash
cd drishti-build/backend
python -m unittest tests/test_api.py
```

---

## 🔒 Security Note

Never commit `.env` or any sensitive API keys to GitHub. Drishti includes a preconfigured `.gitignore` file to safeguard your credentials.

---

## 📜 License

MIT License. Developed for **CELESTIA Hackathon** by **Team Tech Trojan**.
