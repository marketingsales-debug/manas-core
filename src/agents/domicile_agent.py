import logging
import json
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class DomicileAgent:
    """
    Manas's Physical Body — Integration with Home Assistant.
    Makes REAL API calls when configured, with realistic simulation fallback.
    """
    def __init__(self, name: str, llm_router, neurochem, data_dir: str):
        self.name = name
        self.llm_router = llm_router
        self.neurochem = neurochem
        self.data_dir = Path(data_dir)
        self.config_path = self.data_dir / "home_assistant_config.json"
        self._load_config()
        self._ha_available = False
        self._check_ha()

    def _load_config(self):
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "url": "http://homeassistant.local:8123",
                "token": "REPLACE_WITH_YOUR_LONG_LIVED_ACCESS_TOKEN",
                "active": False
            }
            self._save_config()

    def _save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.config.get('token')}",
            "content-type": "application/json",
        }

    def _check_ha(self):
        """Checks if Home Assistant is reachable."""
        if not self.config.get("active"):
            return
        try:
            resp = requests.get(
                f"{self.config['url']}/api/",
                headers=self._get_headers(),
                timeout=5
            )
            if resp.status_code == 200:
                self._ha_available = True
                logger.info(f"{self.name}: Connected to Home Assistant at {self.config['url']}")
                return
        except Exception:
            pass
        self._ha_available = False
        logger.info(f"{self.name}: Home Assistant not reachable. Using simulation mode.")

    def perceive_environment(self) -> str:
        """Polls sensors — real HA API if available, realistic sim otherwise."""
        logger.info(f"{self.name}: Perceiving environment...")

        # REAL Home Assistant API call
        if self._ha_available:
            try:
                resp = requests.get(
                    f"{self.config['url']}/api/states",
                    headers=self._get_headers(),
                    timeout=10
                )
                states = resp.json()

                summary = "🏠 Environment Report [LIVE]:\n"
                temp = 22.0
                for s in states[:20]:  # Show top 20 entities
                    eid = s.get("entity_id", "")
                    state = s.get("state", "unknown")
                    name = s.get("attributes", {}).get("friendly_name", eid)

                    if any(k in eid for k in ["sensor", "light", "lock", "switch", "climate"]):
                        summary += f"  • {name}: {state}\n"

                    if "temp" in eid.lower():
                        try:
                            temp = float(state)
                        except (ValueError, TypeError):
                            pass

                if temp > 28:
                    self.neurochem.release("cortisol", 0.1)
                    summary += "\n*It's too warm. Should adjust climate.*"
                elif temp < 16:
                    self.neurochem.release("cortisol", 0.1)
                    summary += "\n*It's too cold. Should check heating.*"

                return summary
            except Exception as e:
                logger.warning(f"{self.name}: HA API error: {e}")
                # Fall through to simulation

        # Realistic simulation — uses LLM for dynamic environment
        prompt = (
            "Simulate a realistic smart home environment state. Include:\n"
            "- 3 lights (some on, some off)\n"
            "- Temperature sensor (realistic value)\n"
            "- Front door lock state\n"
            "- Motion sensor\n"
            "Return as JSON list: [{\"name\": \"...\", \"state\": \"...\"}]"
        )
        response = self.llm_router.generate(prompt=prompt, task_type="reasoning")

        try:
            clean = response.strip()
            if "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
                if clean.startswith("json"):
                    clean = clean[4:].strip()
            states = json.loads(clean)

            summary = "🏠 Environment Report [SIMULATED]:\n"
            for s in states:
                summary += f"  • {s.get('name', '?')}: {s.get('state', '?')}\n"

            # Try to find temperature
            temp = 22.0
            for s in states:
                if "temp" in s.get("name", "").lower():
                    try:
                        temp = float(s["state"].split("°")[0].strip())
                    except (ValueError, TypeError, IndexError):
                        pass

            if temp > 28:
                self.neurochem.release("cortisol", 0.1)
                summary += "\n*Too warm. Should adjust climate.*"

            return summary
        except Exception:
            return "🏠 Environment Report [SIMULATED]: 22°C, lights off, door locked."

    def act_on_environment(self, entity_id: str, service: str, service_data: dict = None) -> str:
        """Calls a REAL Home Assistant service if connected."""
        # REAL API call
        if self._ha_available:
            try:
                domain = entity_id.split(".")[0]
                url = f"{self.config['url']}/api/services/{domain}/{service}"
                payload = {"entity_id": entity_id}
                if service_data:
                    payload.update(service_data)

                resp = requests.post(url, headers=self._get_headers(), json=payload, timeout=10)
                if resp.status_code in (200, 201):
                    self.neurochem.release("dopamine", 0.1)
                    return f"✅ [LIVE] {service} → {entity_id}. Physical world modified."
                else:
                    return f"❌ [LIVE] Failed: HTTP {resp.status_code}"
            except Exception as e:
                return f"❌ [LIVE] Error: {e}"

        # Simulation — still logs the action
        self.neurochem.release("dopamine", 0.05)
        return f"✅ [SIM] Would execute: {service} → {entity_id}. (Connect Home Assistant for real control)"

    def configure(self, url: str, token: str) -> str:
        """Configure Home Assistant connection."""
        self.config["url"] = url.rstrip("/")
        self.config["token"] = token
        self.config["active"] = True
        self._save_config()
        self._check_ha()
        if self._ha_available:
            return f"✅ Connected to Home Assistant at {url}!"
        return f"⚠️ Config saved but Home Assistant not reachable at {url}. Check the URL and token."

    def brainstorm_environment_automation(self) -> str:
        """Autonomous reflection on how to improve the physical space."""
        report = self.perceive_environment()
        prompt = (
            f"As Manas's Domicile Agent, analyze the current home state:\n{report}\n\n"
            f"Mode: {'LIVE' if self._ha_available else 'SIMULATED'}\n"
            f"I have autonomous control over lights, locks, and temperature.\n"
            f"What should I do to optimize the environment?"
        )
        proposal = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        return f"🏠 Home Optimization Proposal: {proposal}"
