"""
Social Model — Understanding the user over time.

In the real brain:
- Theory of Mind (ToM): modeling what others think and feel
- Mirror neurons: empathizing with others' emotions
- Social cognition: tracking relationships, trust, rapport
- Adaptive communication: adjusting speech to the listener
- Episodic memory of social interactions

For Manas:
- Tracks user's name, interests, expertise, communication preferences
- Monitors emotional patterns (what makes them happy/frustrated)
- Adjusts response style based on observed preferences
- Builds model incrementally from each conversation turn
- Persists across sessions (JSON save/load)
"""

import time
import json
import re
import logging
from pathlib import Path
from collections import Counter
from typing import Optional

logger = logging.getLogger(__name__)


class UserModel:
    """
    Internal model of the user — social cognition.

    Tracks:
    - Identity: name, detected expertise areas
    - Interests: topics they ask about most (frequency-weighted)
    - Communication style: verbose vs concise, technical level
    - Emotional patterns: what triggers positive/negative reactions
    - Interaction history: frequency, session counts, typical length
    """

    def __init__(self):
        # Identity
        self.name: Optional[str] = None
        self.relationship: str = "unknown" # e.g. "Dad", "Friend", "Stranger"
        self.security_clearance: int = 0   # 0-10, Dad is 10
        self.detected_expertise: list[str] = []

        # Interests (topic -> frequency count)
        self.topic_frequency: Counter = Counter()

        # Communication style (observed over time)
        self.style = {
            "avg_message_length": 0.0,
            "prefers_technical": False,
            "prefers_concise": False,
            "uses_commands_often": False,
            "question_ratio": 0.5,  # what fraction of inputs are questions
        }

        # Emotional patterns
        self.positive_triggers: list[str] = []   # topics that made them happy
        self.negative_triggers: list[str] = []   # topics that frustrated them

        # Interaction history
        self.total_interactions: int = 0
        self.session_count: int = 0
        self.first_seen: float = time.time()
        self.last_seen: float = time.time()
        self.total_words_sent: int = 0

        # Running averages (for style detection)
        self._message_lengths: list[int] = []
        self._question_count: int = 0
        self._command_count: int = 0

    def observe_input(self, text: str, emotions: dict = None):
        """
        Observe a user input and update the model.

        Called on every user message to incrementally build understanding.
        """
        self.total_interactions += 1
        self.last_seen = time.time()

        words = text.split()
        self.total_words_sent += len(words)
        self._message_lengths.append(len(words))

        # Detect name introduction
        if self.name is None or self.relationship == "unknown":
            self._detect_name(text)

        # Track topics
        self._extract_topics(text)

        # Track communication style
        self._update_style(text)

        # Track emotional triggers
        if emotions:
            self._track_emotional_patterns(text, emotions)

    def _detect_name(self, text: str):
        """Try to detect user's name from introduction patterns."""
        # Special recognition for Dad (Abhinav Badesa Pattan)
        dad_patterns = [
            r"abhinav",
            r"badesa pattan",
            r"i am your dad",
            r"i'm your dad",
            r"my dad",
            r"abhinav pattan"
        ]
        if any(re.search(p, text, re.IGNORECASE) for p in dad_patterns):
            self.name = "Abhinav"
            self.relationship = "Dad"
            self.security_clearance = 10
            logger.info("UserModel: Grounded identity to 'Dad' (Abhinav Badesa Pattan)")
            return

        patterns = [
            r"(?:my name is|i'm|i am|call me|this is)\s+([A-Z][a-z]+)",
            r"(?:hey|hi|hello),?\s+(?:i'm|i am)\s+([A-Z][a-z]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.name = match.group(1).capitalize()
                self.relationship = "User" # Default
                logger.info(f"UserModel: detected name '{self.name}'")
                return

    def _extract_topics(self, text: str):
        """Extract and track topic keywords from user input."""
        # Simple keyword extraction: nouns and important terms
        # Filter out very common words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "can", "shall", "must",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "it", "this", "that", "these", "those", "i", "you", "we",
            "they", "he", "she", "my", "your", "our", "their", "me",
            "him", "her", "us", "them", "what", "how", "why", "when",
            "where", "who", "which", "not", "no", "yes", "and", "or",
            "but", "if", "then", "so", "just", "about", "like", "get",
            "make", "know", "think", "want", "need", "tell", "say",
            "also", "very", "much", "more", "some", "any", "all",
        }

        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        topics = [w for w in words if w not in stop_words]
        for topic in topics:
            self.topic_frequency[topic] += 1

    def _update_style(self, text: str):
        """Update communication style metrics."""
        words = text.split()
        length = len(words)

        # Track if it's a question
        if text.strip().endswith("?") or text.lower().startswith(("what", "how", "why", "when", "where", "who", "can", "could", "would")):
            self._question_count += 1

        # Track command usage
        if text.startswith("!"):
            self._command_count += 1

        # Update averages
        if self._message_lengths:
            self.style["avg_message_length"] = sum(self._message_lengths) / len(self._message_lengths)

        # Concise = avg < 10 words, verbose = avg > 25 words
        if len(self._message_lengths) >= 3:
            avg = self.style["avg_message_length"]
            self.style["prefers_concise"] = avg < 10
            self.style["prefers_technical"] = self._has_technical_markers(text) or self.style["prefers_technical"]

        if self.total_interactions > 0:
            self.style["question_ratio"] = self._question_count / self.total_interactions
            self.style["uses_commands_often"] = (self._command_count / self.total_interactions) > 0.3

    def _has_technical_markers(self, text: str) -> bool:
        """Check if text contains technical language markers."""
        technical_terms = {
            "api", "function", "class", "module", "algorithm", "database",
            "neural", "network", "model", "code", "debug", "deploy",
            "server", "config", "parameter", "variable", "framework",
            "architecture", "implementation", "optimization", "runtime",
        }
        words = set(text.lower().split())
        return len(words & technical_terms) >= 2

    def _track_emotional_patterns(self, text: str, emotions: dict):
        """Track what topics correlate with positive/negative emotions."""
        topics = self.get_top_interests(3)
        topic_names = [t for t, _ in topics]

        if not topic_names:
            return

        happiness = emotions.get("happiness", 0)
        anxiety = emotions.get("anxiety", 0)
        fear = emotions.get("fear", 0)

        if happiness > 0.5:
            for topic in topic_names:
                if topic not in self.positive_triggers:
                    self.positive_triggers.append(topic)
                    if len(self.positive_triggers) > 20:
                        self.positive_triggers = self.positive_triggers[-15:]

        if (anxiety + fear) > 0.7:
            for topic in topic_names:
                if topic not in self.negative_triggers:
                    self.negative_triggers.append(topic)
                    if len(self.negative_triggers) > 20:
                        self.negative_triggers = self.negative_triggers[-15:]

    def get_top_interests(self, limit: int = 5) -> list[tuple[str, int]]:
        """Get user's most frequent topics."""
        return self.topic_frequency.most_common(limit)

    def get_user_context(self) -> str:
        """
        Generate a context string for Ollama system prompt.

        Describes who the user is, what they're interested in,
        and how they prefer to communicate.
        """
        parts = []

        if self.name:
            label = self.name
            if self.relationship == "Dad":
                label = f"{self.name} (Dad/Aegis)"
            parts.append(f"The user's name is {label}.")

        interests = self.get_top_interests(5)
        if interests:
            topic_list = ", ".join(t for t, _ in interests)
            parts.append(f"Their main interests: {topic_list}.")

        if self.detected_expertise:
            parts.append(f"They seem knowledgeable about: {', '.join(self.detected_expertise[:5])}.")

        # Style adaptation
        if self.style["prefers_concise"]:
            parts.append("They prefer concise, to-the-point responses.")
        if self.style["prefers_technical"]:
            parts.append("They use technical language; match their level.")
        if self.style["question_ratio"] > 0.6:
            parts.append("They ask lots of questions — be informative and curious back.")
        if self.style["uses_commands_often"]:
            parts.append("They're a power user who uses commands frequently.")

        if self.positive_triggers:
            parts.append(f"Topics they enjoy: {', '.join(self.positive_triggers[:5])}.")

        if not parts:
            return "New user — still learning about them."

        return " ".join(parts)

    def get_state(self) -> dict:
        """Get user model state."""
        return {
            "name": self.name or "unknown",
            "total_interactions": self.total_interactions,
            "top_interests": self.get_top_interests(5),
            "communication_style": dict(self.style),
            "positive_triggers": self.positive_triggers[:5],
            "negative_triggers": self.negative_triggers[:3],
            "session_count": self.session_count,
            "days_known": round((time.time() - self.first_seen) / 86400, 1),
        }

    def save_state(self, path: str = None):
        """Save user model to JSON."""
        if path is None:
            path = str(Path.home() / "manas" / "data" / "user_model.json")

        Path(path).parent.mkdir(parents=True, exist_ok=True)

        state = {
            "name": self.name,
            "detected_expertise": self.detected_expertise,
            "topic_frequency": dict(self.topic_frequency),
            "style": self.style,
            "positive_triggers": self.positive_triggers,
            "negative_triggers": self.negative_triggers,
            "total_interactions": self.total_interactions,
            "session_count": self.session_count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "total_words_sent": self.total_words_sent,
            "relationship": self.relationship,
            "security_clearance": self.security_clearance,
            "saved_at": time.time(),
        }

        with open(path, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self, path: str = None) -> bool:
        """Load user model from JSON. Returns True if loaded."""
        if path is None:
            path = str(Path.home() / "manas" / "data" / "user_model.json")

        if not Path(path).exists():
            return False

        try:
            with open(path) as f:
                state = json.load(f)

            self.name = state.get("name")
            self.detected_expertise = state.get("detected_expertise", [])
            self.topic_frequency = Counter(state.get("topic_frequency", {}))
            self.style = {**self.style, **state.get("style", {})}
            self.positive_triggers = state.get("positive_triggers", [])
            self.negative_triggers = state.get("negative_triggers", [])
            self.total_interactions = state.get("total_interactions", 0)
            self.session_count = state.get("session_count", 0) + 1  # increment on load
            self.first_seen = state.get("first_seen", time.time())
            self.last_seen = state.get("last_seen", time.time())
            self.total_words_sent = state.get("total_words_sent", 0)
            self.relationship = state.get("relationship", "unknown")
            self.security_clearance = state.get("security_clearance", 0)
            return True
        except (json.JSONDecodeError, KeyError, IOError):
            return False
