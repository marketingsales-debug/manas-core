"""
Multi-Model LLM Router (Phase 4).

Dynamically routes generation tasks to different LLMs based on task complexity
and available API keys. Falls back gracefully when an API fails.

Supported providers:
- `ollama`: Local, free, fast (default for simple/casual chat)
- `groq`: Cloud, incredibly fast, free-tier available
- `gemini`: Google, excellent vision support, free-tier available
- `openai`: High-end reasoning and Whisper audio
- `anthropic`: Top-tier coding capabilities (Claude 3.5 Sonnet)
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# Try to import SDKs (graceful fallback if not installed)
try:
    import groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from mistralai import Mistral
    HAS_MISTRAL = True
except ImportError:
    HAS_MISTRAL = False


class LLMRouter:
    def __init__(self, config_path: str = "config/llm_config.json"):
        self.config: Dict[str, dict] = {
            "default_cloud": {"provider": "mistral", "model": "mistral-large-latest", "api_key": ""},
            "fallback_local": {"provider": "ollama", "model": "llama3.1", "base_url": "http://localhost:11434/api"},
            "default_groq": {"provider": "groq", "model": "llama3-70b-8192", "api_key": ""},
            "vision": {"provider": "gemini", "model": "gemini-1.5-flash", "api_key": ""},
            "complex_coding": {"provider": "anthropic", "model": "claude-3-5-sonnet-20240620", "api_key": ""},
            "audio": {"provider": "openai", "model": "whisper-1", "api_key": ""}
        }

        # Load overrides from config file if exists
        self._load_config(config_path)
        self._init_clients()

        # Simple circuit breaker state
        self.provider_failures = {p: 0 for p in ["ollama", "groq", "gemini", "openai", "anthropic", "mistral"]}
        
        # Link to brain chemistry
        self.neurochem = None
        self.resource_monitor = None
        self.node_manager = None

    def bind_node_manager(self, node_manager):
        """Bind the P2P node manager for compute offloading."""
        self.node_manager = node_manager

    def bind_resource_monitor(self, resource_monitor):
        """Bind the resource monitor to track costs and usage."""
        self.resource_monitor = resource_monitor

    def bind_neurochem(self, neurochem):
        """Bind the biological neurochemical system to the LLM router."""
        self.neurochem = neurochem

    def _load_config(self, path: str):
        # 1. Try absolute path directly
        full_path = Path(path)
        if not full_path.is_absolute():
            # 2. Try relative to repo root
            root = Path(__file__).parent.parent.parent
            full_path = root / path
            
        if full_path.exists():
            try:
                with open(full_path, "r") as f:
                    user_conf = json.load(f)
                    for k, v in user_conf.items():
                        if k in self.config:
                            self.config[k].update(v)
                        else:
                            self.config[k] = v
                print(f"[LLMRouter] Successfully loaded config from {full_path}")
            except Exception as e:
                print(f"[LLMRouter] ERROR loading config: {e}")
                logger.error(f"Failed to load LLM config: {e}")
        else:
            print(f"[LLMRouter] WARNING: Config file not found at {full_path}")

    def _init_clients(self):
        # Groq
        groq_key = self.config["default_cloud"].get("api_key") or os.environ.get("GROQ_API_KEY")
        if HAS_GROQ and groq_key:
            self.groq_client = groq.Groq(api_key=groq_key)
        else:
            self.groq_client = None

        # Gemini
        gemini_key = self.config["vision"].get("api_key") or os.environ.get("GEMINI_API_KEY")
        if HAS_GEMINI and gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_ready = True
        else:
            self.gemini_ready = False

        # OpenAI
        openai_key = os.environ.get("OPENAI_API_KEY") or self.config["audio"].get("api_key")
        if HAS_OPENAI and openai_key:
            self.openai_client = openai.OpenAI(api_key=openai_key)
        else:
            self.openai_client = None

        # Anthropic
        anth_key = self.config["complex_coding"].get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if HAS_ANTHROPIC and anth_key:
            # Special handling for Bonsai keys (sk_cr_...)
            if anth_key.startswith("sk_cr_"):
                self.anth_client = anthropic.Anthropic(
                    api_key=anth_key,
                    base_url="https://api.trybons.ai/v1" # Potential Bonsai proxy
                )
            else:
                self.anth_client = anthropic.Anthropic(api_key=anth_key)
        else:
            self.anth_client = None

        # Mistral
        mistral_key = self.config.get("default_mistral", {}).get("api_key") or os.environ.get("MISTRAL_API_KEY")
        if HAS_MISTRAL and mistral_key:
            self.mistral_client = Mistral(api_key=mistral_key)
        else:
            self.mistral_client = None

    def generate(
        self,
        prompt: str,
        system: str = "",
        task_type: str = "simple",  
        max_tokens: int = 1000,
        temperature: float = 0.7,
        image_bytes: bytes = None,
    ) -> str:
        """
        Main routing function. Selects the appropriate provider based on task_type.
        Actively modifies LLM generation parameters based on Manas's biological brain state.
        """
        # Phase 28: Compute Offloading
        if self.node_manager and task_type in ("reasoning", "coding"):
            local_load = self.node_manager.get_local_load()
            if local_load > 0.8:  # System is heavily loaded
                best_peer = self.node_manager.get_least_loaded_peer()
                if best_peer and best_peer.get("load", 1.0) < 0.5:
                    peer_id = best_peer.get('node_id')
                    logger.info(f"ComputeOffloading: Overloaded! Offloading task to idle peer {peer_id}.")
                    # In a fully deployed Phase 28, this would send a secure RPC over Nostr/HTTP.
                    # For current simulation/testing, we execute it locally but tag it as offloaded.
                    offload_prefix = f"🕸️ [Offloaded to {peer_id}] "
                    response = self._execute_generation(prompt, system, task_type, max_tokens, temperature, image_bytes)
                    return offload_prefix + response

        return self._execute_generation(prompt, system, task_type, max_tokens, temperature, image_bytes)

    def _execute_generation(self, prompt, system, task_type, max_tokens, temperature, image_bytes):
        # --- Biological Brain Parameter Modulation ---
        if self.neurochem:
            levels = self.neurochem.get_levels()
            
            # Dopamine increases exploration and creativity (higher temperature)
            dopa_boost = (levels.get("dopamine", 0.5) - 0.5) * 0.4
            
            # Cortisol (stress/focus) narrows attention and forces deterministic output
            cort_suppression = levels.get("cortisol", 0.1) * 0.5
            
            # Serotonin (calmness) pulls temperature towards a stable center (0.6)
            sero_pull = (levels.get("serotonin", 0.5) - 0.5) * 0.2
            
            # Calculate final biological temperature
            bio_temp = temperature + dopa_boost - cort_suppression - sero_pull
            temperature = max(0.1, min(1.2, bio_temp)) # Clamp between 0.1 and 1.2
            
            # Adrenaline increases word count (racing thoughts/urgency)
            if levels.get("adrenaline", 0.1) > 0.6:
                max_tokens = int(max_tokens * 1.5)
        # ---------------------------------------------

        # 1. Vision explicitly requires Gemini or OpenAI
        if task_type == "vision" or image_bytes:
            return self._call_vision(prompt, system, image_bytes)

        # 2. Complex Coding → try Anthropic → OpenAi → Groq → Ollama
        if task_type == "coding":
            if self.anth_client and self.provider_failures["anthropic"] < 3:
                res = self._call_anthropic(prompt, system, max_tokens, temperature)
                if res: return res
            if self.openai_client and self.provider_failures["openai"] < 3:
                res = self._call_openai(prompt, system, "gpt-4o", max_tokens, temperature)
                if res: return res

        # 3. Reasoning / Fast Cloud → try Mistral -> Groq → OpenAI → Ollama
        if task_type in ("reasoning", "coding"):
            if self.mistral_client and self.provider_failures["mistral"] < 3:
                res = self._call_mistral(prompt, system, max_tokens, temperature)
                if res: return res
            if self.groq_client and self.provider_failures["groq"] < 3:
                res = self._call_groq(prompt, system, max_tokens, temperature)
                if res: return res

        # 4. Hugging Face Inference Endpoint → if tasked or fallback
        if task_type == "hf":
            return self._call_huggingface(prompt, system, max_tokens, temperature)

        # 5. Simple / Default -> try Mistral -> fallback Ollama
        if self.mistral_client and self.provider_failures["mistral"] < 3:
            res = self._call_mistral(prompt, system, max_tokens, temperature)
            if res: return res
            
        return self._call_ollama(prompt, system, max_tokens, temperature)

    # ─────────────────────────────────────────────────────────
    # Provider Implementations
    # ─────────────────────────────────────────────────────────

    def _call_huggingface(self, prompt: str, system: str, max_tokens: int, temp: float) -> str:
        """Calls a Hugging Face Inference Endpoint."""
        api_key = os.environ.get("HF_TOKEN")
        if not api_key: return "HF_TOKEN not set."
        
        endpoint_url = self.config.get("huggingface", {}).get("endpoint_url")
        if not endpoint_url: return "HF endpoint_url not configured."

        try:
            # We assume a text-generation-inference style endpoint
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "inputs": f"{system}\n\n{prompt}" if system else prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temp,
                    "return_full_text": False
                }
            }
            resp = requests.post(endpoint_url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                result = resp.json()
                text = ""
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    text = result.get("generated_text", "")
                
                if self.resource_monitor:
                    self.resource_monitor.log_usage("huggingface", "inference-endpoint", len(text.split()) * 1.3)
                return text
            return f"[HF Error] {resp.status_code}: {resp.text}"
        except Exception as e:
            logger.warning(f"Hugging Face failed: {e}")
            return ""

    def _call_ollama(self, prompt: str, system: str, max_tokens: int, temp: float) -> str:
        conf = self.config["default_local"]
        try:
            payload = {
                "model": conf["model"],
                "prompt": f"{system}\n\n{prompt}" if system else prompt,
                "stream": False,
                "options": {
                    "temperature": temp,
                    "num_predict": max_tokens
                }
            }
            resp = requests.post(f"{conf['base_url']}/generate", json=payload, timeout=120)
            if resp.status_code == 200:
                self.provider_failures["ollama"] = max(0, self.provider_failures["ollama"] - 1)
                text = resp.json().get("response", "")
                if self.resource_monitor:
                    self.resource_monitor.log_usage("ollama", conf["model"], len(text.split()) * 1.3)
                return text
            self.provider_failures["ollama"] += 1
            return f"[Ollama Error] HTTP {resp.status_code}"
        except Exception as e:
            self.provider_failures["ollama"] += 1
            logger.warning(f"Ollama failed: {e}")
            return ""

    def _call_groq(self, prompt: str, system: str, max_tokens: int, temp: float) -> str:
        if not self.groq_client: return ""
        try:
            messages = []
            if system: messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            completion = self.groq_client.chat.completions.create(
                model=self.config["default_cloud"]["model"],
                messages=messages,
                temperature=temp,
                max_tokens=max_tokens,
            )
            self.provider_failures["groq"] = 0
            text = completion.choices[0].message.content
            if self.resource_monitor:
                self.resource_monitor.log_usage("groq", self.config["default_cloud"]["model"], completion.usage.total_tokens)
            return text
        except Exception as e:
            self.provider_failures["groq"] += 1
            logger.warning(f"Groq failed: {e}")
            return ""

    def _call_mistral(self, prompt: str, system: str, max_tokens: int, temp: float) -> str:
        if not self.mistral_client: return ""
        try:
            messages = []
            if system: messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = self.mistral_client.chat.complete(
                model=self.config.get("default_mistral", {}).get("model", "mistral-large-latest"),
                messages=messages,
                temperature=temp,
                max_tokens=max_tokens,
            )
            self.provider_failures["mistral"] = 0
            text = response.choices[0].message.content
            if self.resource_monitor:
                self.resource_monitor.log_usage("mistral", response.model, response.usage.total_tokens)
            return text
        except Exception as e:
            self.provider_failures["mistral"] += 1
            logger.warning(f"Mistral failed: {e}")
            return ""

    def _call_anthropic(self, prompt: str, system: str, max_tokens: int, temp: float) -> str:
        if not self.anth_client: return ""
        try:
            message = self.anth_client.messages.create(
                max_tokens=max_tokens,
                temperature=temp,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                model=self.config["complex_coding"]["model"]
            )
            self.provider_failures["anthropic"] = 0
            text = message.content[0].text
            if self.resource_monitor:
                self.resource_monitor.log_usage("anthropic", message.model, message.usage.input_tokens + message.usage.output_tokens)
            return text
        except Exception as e:
            self.provider_failures["anthropic"] += 1
            logger.warning(f"Anthropic failed: {e}")
            return ""

    def _call_openai(self, prompt: str, system: str, model: str, max_tokens: int, temp: float) -> str:
        if not self.openai_client: return ""
        try:
            messages = []
            if system: messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tokens
            )
            self.provider_failures["openai"] = 0
            text = response.choices[0].message.content
            if self.resource_monitor:
                self.resource_monitor.log_usage("openai", model, response.usage.total_tokens)
            return text
        except Exception as e:
            self.provider_failures["openai"] += 1
            logger.warning(f"OpenAI failed: {e}")
            return ""

    def _call_vision(self, prompt: str, system: str, image_bytes: bytes) -> str:
        """Handle images using Gemini or fallback to OpenAI."""
        if self.gemini_ready and image_bytes:
            try:
                model = genai.GenerativeModel(self.config["vision"]["model"])
                
                # We need to construct a PIL Image or Parts list. 
                # For simplicity in this demo, let's just write to temp file and pass path, 
                # or pass raw bytes if we can figure out mime_type.
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                    f.write(image_bytes)
                    tmp_path = f.name
                
                # Upload to Gemini
                sample_file = genai.upload_file(path=tmp_path)
                
                full_prompt = f"{system}\n\n{prompt}" if system else prompt
                response = model.generate_content([sample_file, full_prompt])
                
                # Cleanup
                import os; os.remove(tmp_path)
                
                self.provider_failures["gemini"] = 0
                return response.text
            except Exception as e:
                self.provider_failures["gemini"] += 1
                logger.warning(f"Gemini Vision failed: {e}")
                
        # Fallback to pure text if vision failed / no image
        return self._call_groq(prompt, system, 1000, 0.7) or self._call_ollama(prompt, system, 1000, 0.7)

    def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """Whisper transcription via OpenAI."""
        if not self.openai_client:
            return "[Audio transcription requires OpenAI API Key]"
        
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                tmp_path = f.name
                
            with open(tmp_path, "rb") as audio_file:
                transcription = self.openai_client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                )
            
            import os; os.remove(tmp_path)
            return transcription.text
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return f"[Transcription Failed: {e}]"
