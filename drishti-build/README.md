# Drishti — Guided Walk with Multilingual Action Alerts

This project combines the Drishti web frontend and FastAPI vision backend. During Guided Walk, the frontend repeatedly sends camera frames to `/vision-assist`. The backend returns a short hazard alert and an `immediateAction`; the frontend speaks both using the selected language and the browser/device or server TTS voice.

## Start

1. Install Python 3.10+ (3.11 recommended).
2. In a terminal, open `backend/` and run `python -m venv .venv`. Activate it.
3. Install dependencies: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and add your own Gemini API key to `GEMINI_API_KEY` for live image analysis. Never share your `.env` file.
5. Start the backend from `backend/`: `python server.py`.
6. In another terminal, serve `frontend/` locally (for example `python -m http.server 8080 --directory frontend`) and open `http://localhost:8080`.
7. Allow camera permission, choose a language, and press **Start guided walk**.

Camera and microphone access generally require localhost or HTTPS.

## Action guidance behavior

- Alerts and recommended actions use the selected language (English, Hindi, Kannada, Telugu, Tamil, Marathi, Bengali, Gujarati, Malayalam, Spanish, French, German, or Japanese, subject to available TTS voices).
- The vision prompt instructs the model to recommend left/right movement only when that side is visibly clear in the current frame. If it cannot verify an alternative, it should tell the user to stop/pause and verify using their usual mobility aid or a trusted companion.
- Guided Walk speaks the `spokenAlert` and `immediateAction` together.
- When the backend is in demo mode, the app does **not** speak simulated obstacle directions as real findings; it announces that live camera-based guidance is unavailable.

## Important safety limitations

This is a prototype, not a certified mobility aid. A single camera frame cannot reliably establish depth, hidden hazards, traffic gaps, or whether a vehicle/person/animal is moving toward the user. Repeated still-image scans are not continuous real-time tracking. Do not use this app as the only source of mobility or road-crossing guidance, and test only in a controlled, supervised setting with a familiar mobility aid and a companion.
