"""
Sensory Processing Module (Phase 4).

Provides Manas with eyes, ears, and hands:
- Vision: Capturing MacOS screen / webcam, and parsing images via Gemini
- Audio: Capturing MacOS microphone and transcribing via Whisper
- Web: Real browser control via Playwright
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import required sensory libraries
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    import sounddevice as sd
    import numpy as np
    import wave
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


class SensoryProcessing:
    def __init__(self, llm_router=None):
        self.llm_router = llm_router
        self._browser = None
        self._playwright = None
        self._page = None
        self.is_recording_audio = False
        
    # ─────────────────────────────────────────────────────────
    # Vision (Camera)
    # ─────────────────────────────────────────────────────────

    def capture_camera_frame(self) -> Optional[bytes]:
        """Capture a single frame from the Mac FaceTime camera."""
        if not HAS_OPENCV:
            logger.warning("OpenCV not installed. Cannot use camera.")
            return None

        try:
            # 0 is usually the default FaceTime camera on Mac
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("Could not open camera.")
                return None
                
            # Read a few frames to let auto-exposure adjust
            for _ in range(5):
                ret, frame = cap.read()
            
            cap.release()
            
            if ret:
                # Convert to JPG bytes
                ret, buf = cv2.imencode('.jpg', frame)
                if ret:
                    return buf.tobytes()
            return None
        except Exception as e:
            logger.error(f"Camera capture failed: {e}")
            return None

    def analyze_camera(self, prompt: str = "What do you see in front of the camera?") -> str:
        """Capture a frame and send to Vision LLM."""
        if not self.llm_router:
            return "[Error: No LLMRouter connected for vision analysis]"
            
        frame_bytes = self.capture_camera_frame()
        if not frame_bytes:
            return "[No image captured from camera]"
            
        return self.llm_router.generate(prompt=prompt, task_type="vision", image_bytes=frame_bytes)

    # ─────────────────────────────────────────────────────────
    # Audio (Microphone)
    # ─────────────────────────────────────────────────────────

    def record_audio(self, duration_sec: int = 5, sample_rate: int = 16000) -> Optional[bytes]:
        """Record audio from the Mac microphone."""
        if not HAS_SOUNDDEVICE:
            logger.warning("sounddevice not installed. Cannot use mic.")
            return None
            
        try:
            logger.info(f"Recording audio for {duration_sec} seconds...")
            recording = sd.rec(int(duration_sec * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()  # Wait until recording is finished
            
            # Save into memory buffer as WAV
            import io
            buf = io.BytesIO()
            with wave.open(buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2) # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(recording.tobytes())
                
            return buf.getvalue()
        except Exception as e:
            logger.error(f"Audio recording failed: {e}")
            return None

    def listen_and_transcribe(self, duration_sec: int = 5) -> str:
        """Record audio and use Whisper to transcribe."""
        if not self.llm_router:
            return "[Error: No LLMRouter connected for audio transcription]"
            
        audio_bytes = self.record_audio(duration_sec)
        if not audio_bytes:
            return "[No audio recorded]"
            
        return self.llm_router.transcribe_audio(audio_bytes)

    # ─────────────────────────────────────────────────────────
    # Browser Control (Playwright)
    # ─────────────────────────────────────────────────────────

    def init_browser(self, headless: bool = False):
        """Initialize the Playwright browser."""
        if not HAS_PLAYWRIGHT:
            logger.warning("Playwright not installed. Cannot use browser.")
            return False
            
        if self._playwright is None:
            self._playwright = sync_playwright().start()
            # Use chromium by default
            self._browser = self._playwright.chromium.launch(headless=headless)
            self._page = self._browser.new_page()
            return True
        return True

    def close_browser(self):
        """Cleanup browser resources."""
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def browse_to(self, url: str):
        """Navigate the browser to a URL."""
        if not self._page:
            if not self.init_browser(): return "[Browser init failed]"
            
        try:
            self._page.goto(url, wait_until="networkidle")
            return f"Navigated to {url}"
        except Exception as e:
            return f"[Navigation failed: {e}]"

    def get_page_text(self) -> str:
        """Extract visible text from current page."""
        if not self._page: return ""
        try:
            # Simple extraction: grab all inner text from body
            return self._page.evaluate("document.body.innerText")
        except Exception as e:
            logger.error(f"Failed to get page text: {e}")
            return ""

    def capture_screenshot(self) -> Optional[bytes]:
        """Take a screenshot of the current page."""
        if not self._page: return None
        try:
            return self._page.screenshot()
        except Exception as e:
            logger.error(f"Failed to screenshot page: {e}")
            return None
            
    def analyze_screen(self, prompt: str = "What is on this webpage?") -> str:
        """Take a screenshot of the active browser and send to Vision LLM."""
        if not self.llm_router:
            return "[Error: No LLMRouter connected for vision analysis]"
            
        screenshot_bytes = self.capture_screenshot()
        if not screenshot_bytes:
            return "[No screenshot captured]"
            
        return self.llm_router.generate(prompt=prompt, task_type="vision", image_bytes=screenshot_bytes)

    def autonomous_wander(self, mood: str, duration_minutes: int = 5):
        """
        Human-like wandering based on mood.
        Example mapping:
        - bored -> YouTube or Instagram Reels
        - curious -> Wikipedia / HackerNews
        - focused -> Arxiv / GitHub
        """
        urls = {
            "bored": ["https://www.youtube.com", "https://news.ycombinator.com"],
            "curious": ["https://en.wikipedia.org/wiki/Special:Random"],
            "focused": ["https://github.com/trending", "https://arxiv.org/list/cs.AI/recent"]
        }
        
        target = urls.get(mood, urls["curious"])[0]
        logger.info(f"Emotional state '{mood}' triggered wandering to: {target}")
        
        self.browse_to(target)
        
        # Simulate watching/reading for a bit
        # In a full implementation, we would extract text, analyze screenshots,
        # scroll the page, and feed findings into the Hippocampus.
        screen_analysis = self.analyze_screen("Summarize the most interesting content on this page.")
        
        self.close_browser()
        return {"url": target, "analysis": screen_analysis}
