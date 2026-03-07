import logging
import threading
import queue
import time

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

logger = logging.getLogger(__name__)

class VocalSystem:
    """
    Manas's voice - allowing it to speak its thoughts aloud.
    Uses pyttsx3 for cross-platform offline TTS.
    """
    def __init__(self):
        if not HAS_PYTTSX3:
            logger.warning("pyttsx3 not installed — VocalSystem disabled")
            self.engine = None
            self._is_speaking = False
            return
        try:
            self.engine = pyttsx3.init()
            # Set properties
            voices = self.engine.getProperty('voices')
            # Prefer a more "calm" or "intelligent" sounding voice if possible
            for voice in voices:
                if "Daniel" in voice.name or "Samantha" in voice.name:
                    self.engine.setProperty('voice', voice.id)
                    break
            
            self.engine.setProperty('rate', 175)  # Normal speaking rate
            self.engine.setProperty('volume', 0.9)
            self._is_speaking = False
            
            # Thread-safe message queue
            self.msg_queue = queue.Queue()
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
        except Exception as e:
            logger.error(f"VocalSystem initialization failed: {e}")
            self.engine = None
            self.msg_queue = None

    def _worker(self):
        """Background worker to process speech requests sequentially."""
        while True:
            try:
                text = self.msg_queue.get()
                if text is None: break # Shutdown signal
                
                self._is_speaking = True
                try:
                    # Re-initialize engine in the worker thread to ensure it owns the loop
                    # pyttsx3 is notorious for thread affinity issues
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    logger.debug(f"VocalSystem worker error (likely loop already running): {e}")
                finally:
                    self._is_speaking = False
                    self.msg_queue.task_done()
                
            except Exception as e:
                logger.error(f"VocalSystem critical worker error: {e}")
                time.sleep(1)

    def speak(self, text: str, async_mode: bool = True):
        """Speaks the given text via a queue."""
        if not self.engine or not text or self.msg_queue is None:
            return

        if async_mode:
            self.msg_queue.put(text)
        else:
            # Synchronous speak (still uses the engine)
            self.engine.say(text)
            self.engine.runAndWait()

    def modulate(self, rate: int = None, pitch: int = None, volume: float = None):
        """Adjusts voice properties based on emotional state."""
        if not self.engine:
            return
        
        if rate is not None:
            self.engine.setProperty('rate', rate)
        if volume is not None:
            self.engine.setProperty('volume', volume)
        # Note: pyttsx3 doesn't support direct pitch modulation on all platforms,
        # but we can simulate it with rate/volume.
