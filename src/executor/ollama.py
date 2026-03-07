"""
Ollama Executor — Broca's voice box.

Ollama serves as the speech production mechanism for Manas.
The spiking neural network thinks, feels, and remembers.
Ollama takes all that brain context and verbalizes it into natural language.

This is NOT the intelligence — it's the mouth.
Like how Broca's area converts thoughts into speech.
"""

import requests
import time
from typing import Optional


class OllamaExecutor:
    """
    HTTP client for the Ollama API.

    Handles:
    - Health checking (is Ollama running?)
    - Text generation with system prompts
    - Graceful fallback when unavailable
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
        })
        self._available: Optional[bool] = None
        self._last_health_check: float = 0.0
        self._health_cache_ttl: float = 30.0  # re-check every 30s
        self.generation_count: int = 0
        self.total_latency: float = 0.0

    def _check_health(self) -> bool:
        """Check if Ollama is running and responsive."""
        try:
            resp = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=2,
            )
            return resp.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    def is_available(self) -> bool:
        """Is Ollama available? Uses cached result for performance."""
        now = time.time()
        if self._available is None or (now - self._last_health_check) > self._health_cache_ttl:
            self._available = self._check_health()
            self._last_health_check = now
        return self._available

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> Optional[str]:
        """
        Generate text using Ollama.

        Returns the generated text, or None on failure.
        The caller is responsible for fallback behavior.
        """
        if not self.is_available():
            return None

        try:
            start = time.time()
            resp = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": user_message,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
                timeout=120,
            )
            elapsed = time.time() - start

            if resp.status_code == 200:
                data = resp.json()
                text = data.get("response", "").strip()
                if text:
                    self.generation_count += 1
                    self.total_latency += elapsed
                    return text
            return None

        except (requests.ConnectionError, requests.Timeout, requests.JSONDecodeError):
            self._available = False
            return None

    def get_stats(self) -> dict:
        """Get executor statistics."""
        avg_latency = (self.total_latency / self.generation_count) if self.generation_count > 0 else 0.0
        return {
            "available": self.is_available(),
            "model": self.model,
            "generations": self.generation_count,
            "avg_latency_s": round(avg_latency, 2),
            "base_url": self.base_url,
        }
