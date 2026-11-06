import sys
from pathlib import Path
import unittest
from fastapi.testclient import TestClient

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from src.app import app
from src.config.env import config
from src.config.languages import SUPPORTED_LANGUAGES, get_language_metadata

SAMPLE_BASE64_IMAGE = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

class DrishtiApiTests(unittest.TestCase):
    def setUp(self):
        self._orig_key = config.GEMINI_API_KEY
        config.GEMINI_API_KEY = ""
        self.client = TestClient(app)

    def tearDown(self):
        config.GEMINI_API_KEY = self._orig_key

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["team"], "Tech Trojan")
        self.assertIn("aiConfig", data)
        self.assertIn("uptime", data)

    def test_languages_endpoint(self):
        response = self.client.get("/languages")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["languages"]), 10)
        
        codes = [l["code"] for l in data["languages"]]
        self.assertIn("en", codes)
        self.assertIn("hi", codes)
        self.assertIn("kn", codes)
        self.assertIn("te", codes)
        self.assertIn("ta", codes)

    def test_modes_endpoint(self):
        response = self.client.get("/modes")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["modes"]), 4)
        mode_ids = [m["id"] for m in data["modes"]]
        self.assertIn("safety", mode_ids)
        self.assertIn("read", mode_ids)
        self.assertIn("currency", mode_ids)
        self.assertIn("all", mode_ids)

    def test_vision_assist_validation_failure(self):
        response = self.client.post("/vision-assist", json={"mode": "safety"})
        self.assertEqual(response.status_code, 422)

    def test_vision_assist_safety_mode(self):
        response = self.client.post(
            "/vision-assist",
            json={
                "image": SAMPLE_BASE64_IMAGE,
                "mode": "safety",
                "language": "en",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["mode"], "safety")

        result = payload["data"]
        self.assertIn("spokenAlert", result)
        word_count = len(result["spokenAlert"].split())
        self.assertLessEqual(word_count, 15, f"Alert has {word_count} words; max 15 allowed.")
        self.assertIsInstance(result["isPathClear"], bool)
        self.assertIn("immediateAction", result)
        self.assertIsInstance(result["detectedObjects"], list)
        self.assertGreater(len(result["detectedObjects"]), 0)

        first_box = result["detectedObjects"][0]["box2d"]
        self.assertEqual(len(first_box), 4)
        for coord in first_box:
            self.assertTrue(0 <= coord <= 1000)

    def test_vision_assist_sharp_hazard_detection(self):
        response = self.client.post(
            "/vision-assist",
            json={
                "image": SAMPLE_BASE64_IMAGE,
                "mode": "safety",
                "language": "en",
                "userPrompt": "Is there a sharp knife on the bed?",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertTrue(data["sharpHazardDetected"])
        self.assertEqual(data["hazardSeverity"], "high")
        self.assertIsNotNone(data["surfaceAlert"])
        self.assertTrue(any(o.get("isSharpHazard") for o in data["detectedObjects"]))

    def test_vision_assist_chemical_hazard_detection(self):
        response = self.client.post(
            "/vision-assist",
            json={
                "image": SAMPLE_BASE64_IMAGE,
                "mode": "safety",
                "language": "en",
                "userPrompt": "Is there an acid cleaner or bleaching powder spill on the floor?",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertTrue(data["chemicalHazardDetected"])
        self.assertEqual(data["hazardSeverity"], "high")
        self.assertIn("chemical", data["hazardCategories"])
        self.assertTrue(any(o.get("isChemicalHazard") for o in data["detectedObjects"]))

    def test_vision_assist_biological_hazard_detection(self):
        response = self.client.post(
            "/vision-assist",
            json={
                "image": SAMPLE_BASE64_IMAGE,
                "mode": "safety",
                "language": "en",
                "userPrompt": "Are there any insects, spiders, or fungus mold on the bed?",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertTrue(data["biologicalHazardDetected"])
        self.assertEqual(data["hazardSeverity"], "high")
        self.assertIn("biological", data["hazardCategories"])
        self.assertTrue(any(o.get("isBiologicalHazard") for o in data["detectedObjects"]))

    def test_vision_assist_multilingual_hindi_kannada(self):
        # Hindi
        res_hi = self.client.post(
            "/vision-assist",
            json={"image": SAMPLE_BASE64_IMAGE, "mode": "safety", "language": "hi"}
        )
        self.assertEqual(res_hi.status_code, 200)
        alert_hi = res_hi.json()["data"]["spokenAlert"]
        self.assertTrue(any(char in alert_hi for char in ["क", "र", "स", "त"]))

        # Kannada
        res_kn = self.client.post(
            "/vision-assist",
            json={"image": SAMPLE_BASE64_IMAGE, "mode": "safety", "language": "kn"}
        )
        self.assertEqual(res_kn.status_code, 200)
        alert_kn = res_kn.json()["data"]["spokenAlert"]
        self.assertTrue(any(char in alert_kn for char in ["ದ", "ರ", "ಕ", "ಲ"]))

    def test_vision_assist_read_mode_ocr(self):
        response = self.client.post(
            "/vision-assist",
            json={
                "image": SAMPLE_BASE64_IMAGE,
                "mode": "read",
                "language": "en",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertGreater(len(data["textReadings"]), 0)
        self.assertIn("text", data["textReadings"][0])
        self.assertIn("category", data["textReadings"][0])

    def test_vision_assist_currency_mode(self):
        response = self.client.post(
            "/vision-assist",
            json={
                "image": SAMPLE_BASE64_IMAGE,
                "mode": "currency",
                "language": "en",
            },
        )
        self.assertEqual(response.status_code, 200)
        currency = response.json()["data"]["currencyDetected"]
        self.assertTrue(currency["present"])
        self.assertEqual(currency["currency"], "INR")
        self.assertEqual(currency["denomination"], 500)

    def test_chat_endpoint(self):
        response = self.client.post(
            "/chat",
            json={
                "message": "Is the pathway clear in front of me?",
                "language": "en",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIn("reply", data)
        self.assertIn("spokenText", data)
        self.assertIn("suggestedActions", data)
        self.assertIsInstance(data["suggestedActions"], list)

    def test_tts_endpoint(self):
        response = self.client.post(
            "/tts",
            json={
                "text": "Office chair ahead on your left.",
                "language": "en",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["text"], "Office chair ahead on your left.")
        self.assertEqual(data["bcp47"], "en-US")
        self.assertIn("speechConfig", data)
        self.assertEqual(data["speechConfig"]["lang"], "en-US")

    def test_tts_kannada_gtts(self):
        response = self.client.post(
            "/tts",
            json={
                "text": "ಎಚ್ಚರಿಕೆ: ಮುಂದೆ ವ್ಯಕ್ತಿಯೊಬ್ಬರು ಇದ್ದಾರೆ.",
                "language": "kn",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["language"], "kn")
        self.assertIn(data["source"], ["gtts", "browser_speech_synthesis"])
        if data["source"] == "gtts":
            self.assertIsNotNone(data["audioData"])
            self.assertEqual(data["audioMimeType"], "audio/mp3")

    def test_tts_stream_endpoint(self):
        response = self.client.get(
            "/tts/stream",
            params={
                "text": "ಎಚ್ಚರಿಕೆ",
                "language": "kn",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "audio/mpeg")
        self.assertGreater(len(response.content), 0)

    def test_generate_multilingual_audio_function(self):
        from src.services.tts_service import generate_multilingual_audio
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            res = generate_multilingual_audio("ನಮಸ್ಕಾರ", lang_code="kn", filename=tmp_path)
            self.assertEqual(res, tmp_path)
            self.assertTrue(os.path.exists(tmp_path))
            self.assertGreater(os.path.getsize(tmp_path), 0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_api_prefix_aliases(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
