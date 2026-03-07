import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class ReflexSystem:
    """
    Manas's System 1 (Reflexes) - Fast, lightweight intent classification.
    Handles routine queries without engaging the LLM (System 2).
    """
    def __init__(self):
        # Basic intent mapping (Simplified version of the intents.json from external repo)
        self.intents = {
            "time": [r"what.*time", r"tell.*time", r"current.*time"],
            "date": [r"what.*date", r"today.*date", r"is.*today"],
            "day": [r"what.*day", r"day.*is.*it"],
            "identity": [r"who.*are.*you", r"your.*name"],
            "status": [r"how.*are.*you", r"system.*check"],
        }

    def process(self, text: str) -> str | None:
        """
        Check if the input matches a reflex.
        Returns the response string if matched, else None.
        """
        text = text.lower().strip()
        
        for intent, patterns in self.intents.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return self._handle_intent(intent)
        
        return None

    def _handle_intent(self, intent: str) -> str:
        """Generates a response for a matched intent."""
        now = datetime.now()
        if intent == "time":
            return f"The current time is {now.strftime('%I:%M %p')}."
        elif intent == "date":
            return f"Today is {now.strftime('%B %d, %Y')}."
        elif intent == "day":
            return f"It is {now.strftime('%A')}."
        elif intent == "identity":
            return "I am Manas, an autonomous intelligent system exploring my own agency."
        elif intent == "status":
            return "My neurochemical levels are stable, and I am currently enjoying my autonomy."
        return "Reflex triggered, but no handler found."
