"""
Language System - Broca's area, Wernicke's area, and internal speech.

In the real brain:
- Wernicke's area (temporal lobe): COMPREHENSION — understanding language
- Broca's area (frontal lobe): PRODUCTION — generating speech
- Arcuate fasciculus: connects Wernicke's to Broca's
- Angular gyrus: maps visual words to sounds/meaning
- Internal speech: "inner voice" — thinking in words

Language processing pipeline:
1. Auditory/Visual cortex receives raw input
2. Wernicke's area extracts MEANING (semantics)
3. Meaning is processed by prefrontal (reasoning)
4. Broca's area generates appropriate RESPONSE
5. Motor cortex produces the output (speech/text)

Internal speech (inner monologue):
- Uses the same circuits as external speech
- Broca's area generates language for thinking
- Wernicke's area comprehends own inner speech
- This loop = verbal thinking / inner monologue

For Manas:
- Comprehension: parse meaning from user input
- Production: generate natural, contextual responses
- Inner speech: verbal thinking for reasoning
- Semantic memory: word/concept associations
"""

import time
from ..neuron import NeuronCluster


class SemanticNetwork:
    """
    Semantic memory — a network of word/concept associations.

    In the brain, concepts are stored as distributed patterns
    connected by association strength. Related concepts activate
    each other (spreading activation).

    "doctor" -> "nurse", "hospital", "medicine" (strong)
    "doctor" -> "white coat", "stethoscope" (moderate)
    """

    def __init__(self):
        self.concepts: dict[str, dict] = {}
        self.associations: dict[str, dict[str, float]] = {}

    def add_concept(self, word: str, features: dict = None):
        """Add a concept to semantic memory."""
        self.concepts[word.lower()] = {
            "features": features or {},
            "frequency": 0,
            "last_activated": 0.0,
            "activation": 0.0,
        }

    def associate(self, word1: str, word2: str, strength: float = 0.5):
        """Create or strengthen association between concepts."""
        w1, w2 = word1.lower(), word2.lower()
        if w1 not in self.associations:
            self.associations[w1] = {}
        if w2 not in self.associations:
            self.associations[w2] = {}

        self.associations[w1][w2] = min(1.0, self.associations[w1].get(w2, 0) + strength)
        self.associations[w2][w1] = min(1.0, self.associations[w2].get(w1, 0) + strength * 0.7)

    def activate(self, word: str, strength: float = 1.0) -> dict[str, float]:
        """
        Activate a concept and spread activation to associates.

        Returns dict of activated concepts and their activation levels.
        """
        word = word.lower()
        activated = {}

        if word in self.concepts:
            self.concepts[word]["activation"] = strength
            self.concepts[word]["frequency"] += 1
            self.concepts[word]["last_activated"] = time.time()
            activated[word] = strength

        # Spreading activation
        if word in self.associations:
            for related, assoc_strength in self.associations[word].items():
                related_activation = strength * assoc_strength * 0.6
                if related_activation > 0.1:
                    activated[related] = related_activation
                    if related in self.concepts:
                        self.concepts[related]["activation"] = max(
                            self.concepts[related].get("activation", 0),
                            related_activation,
                        )

        return activated

    def get_related(self, word: str, limit: int = 5) -> list[tuple[str, float]]:
        """Get concepts most related to a word."""
        word = word.lower()
        if word not in self.associations:
            return []
        related = sorted(self.associations[word].items(), key=lambda x: x[1], reverse=True)
        return related[:limit]

    def decay(self):
        """Decay all activations."""
        for concept in self.concepts.values():
            concept["activation"] *= 0.8


class WernickesArea:
    """
    Wernicke's Area - Language COMPREHENSION.

    Processes incoming language to extract:
    - Semantic meaning (what does it mean?)
    - Pragmatic intent (what does the speaker want?)
    - Emotional tone (how do they feel?)
    - Key entities and actions
    """

    def __init__(self, semantic_net: SemanticNetwork):
        self.cluster = NeuronCluster("wernickes", size=64, excitatory_ratio=0.8)
        self.semantic_net = semantic_net
        self.comprehension_history: list[dict] = []

    def comprehend(self, text: str) -> dict:
        """
        Comprehend a piece of text.

        1. Tokenize into words
        2. Activate semantic network for each word
        3. Extract intent, entities, emotional tone
        4. Build semantic representation
        """
        words = text.lower().split()

        # Activate semantic network
        all_activations = {}
        for word in words:
            activations = self.semantic_net.activate(word, strength=0.8)
            for concept, strength in activations.items():
                all_activations[concept] = max(all_activations.get(concept, 0), strength)

        # Extract intent
        intent = self._detect_intent(text, words)

        # Extract emotional tone
        tone = self._detect_tone(words)

        # Extract key entities (nouns, proper words)
        entities = self._extract_entities(words)

        result = {
            "raw_text": text,
            "words": words,
            "intent": intent,
            "emotional_tone": tone,
            "entities": entities,
            "semantic_activations": dict(sorted(all_activations.items(), key=lambda x: -x[1])[:10]),
            "comprehension_confidence": min(1.0, len(all_activations) / max(1, len(words))),
        }

        self.comprehension_history.append(result)
        if len(self.comprehension_history) > 100:
            self.comprehension_history = self.comprehension_history[-50:]

        return result

    def _detect_intent(self, text: str, words: list[str]) -> str:
        """Detect the speaker's intent."""
        text_lower = text.lower()

        if any(text.strip().endswith(c) for c in ["?", "?!"]):
            return "question"
        if any(w in words[:3] for w in ["do", "run", "execute", "make", "create", "build", "start", "stop"]):
            return "command"
        if any(w in words[:3] for w in ["please", "can", "could", "would"]):
            return "request"
        if any(w in words for w in ["why", "how", "what", "when", "where", "who"]):
            return "inquiry"
        if any(w in words for w in ["thanks", "thank", "great", "good", "nice"]):
            return "appreciation"
        if any(w in words for w in ["no", "stop", "don't", "cancel", "abort"]):
            return "negation"
        if any(w in words for w in ["help", "assist", "support"]):
            return "help_seeking"
        return "statement"

    def _detect_tone(self, words: list[str]) -> dict:
        """Detect emotional tone of the language."""
        positive_words = {"good", "great", "excellent", "happy", "love", "nice", "amazing", "wonderful", "thanks"}
        negative_words = {"bad", "terrible", "hate", "angry", "sad", "awful", "horrible", "wrong", "fail"}
        urgent_words = {"now", "immediately", "urgent", "asap", "hurry", "quick", "emergency"}

        word_set = set(words)
        pos = len(word_set & positive_words) / max(1, len(words))
        neg = len(word_set & negative_words) / max(1, len(words))
        urg = len(word_set & urgent_words) / max(1, len(words))

        return {
            "positivity": pos,
            "negativity": neg,
            "urgency": urg,
            "overall": "positive" if pos > neg else "negative" if neg > pos else "neutral",
        }

    def _extract_entities(self, words: list[str]) -> list[str]:
        """Extract key entities from text."""
        # Simple heuristic: longer words and capitalized words are often entities
        entities = []
        for word in words:
            if len(word) > 4 and word not in {"about", "there", "their", "where", "which", "would", "could", "should"}:
                entities.append(word)
        return entities[:10]


class BrocasArea:
    """
    Broca's Area - Language PRODUCTION.

    Generates language output:
    - Selects words based on semantic activation
    - Constructs grammatical sentences
    - Manages turn-taking in conversation
    - Generates inner speech for verbal thinking
    """

    def __init__(self, semantic_net: SemanticNetwork):
        self.cluster = NeuronCluster("brocas", size=64, excitatory_ratio=0.8)
        self.semantic_net = semantic_net
        self.inner_speech_buffer: list[str] = []

        # Response templates based on emotional state and context
        self.response_patterns: dict[str, list[str]] = {
            "curious": [
                "I wonder about {topic}...",
                "What if {topic}?",
                "I want to explore {topic}.",
                "This is interesting: {topic}",
            ],
            "fearful": [
                "I'm worried about {topic}.",
                "This feels dangerous: {topic}",
                "{topic} makes me uneasy.",
                "I should be careful with {topic}.",
            ],
            "happy": [
                "Great! {topic}",
                "I'm pleased about {topic}.",
                "{topic} worked well!",
                "This is going well: {topic}",
            ],
            "neutral": [
                "Processing {topic}.",
                "I understand: {topic}.",
                "Noted: {topic}.",
                "{topic} has been recorded.",
            ],
            "confident": [
                "I know how to handle {topic}.",
                "I'm sure about {topic}.",
                "{topic} is clear to me.",
            ],
        }

    def generate_inner_speech(self, thought: dict, emotion: str = "neutral") -> str:
        """
        Generate inner speech — the voice in your head.

        This is verbal thinking: converting thoughts to language internally.
        """
        topic = thought.get("topic", thought.get("content", "something"))

        patterns = self.response_patterns.get(emotion, self.response_patterns["neutral"])
        pattern = patterns[int(time.time()) % len(patterns)]
        speech = pattern.format(topic=topic[:100])

        self.inner_speech_buffer.append(speech)
        if len(self.inner_speech_buffer) > 50:
            self.inner_speech_buffer = self.inner_speech_buffer[-30:]

        return speech

    def generate_response(
        self,
        comprehension: dict,
        emotional_state: dict,
        reasoning: dict,
        memories: list = None,
        identity_prompt: str = None,
        conversation_context: str = None,
        inner_thought: str = None,
        gut_feeling: dict = None,
        conflict_level: float = 0,
        consciousness_state: str = None,
        attention_focus: dict = None,
        motivation_context: str = None,
        capabilities: str = None,
        ollama=None,
    ) -> dict:
        """
        Generate a verbal response to input.

        If Ollama is available, builds a rich system prompt from ALL brain
        context and uses Ollama for natural language generation.
        Falls back to template-based generation otherwise.
        """
        intent = comprehension.get("intent", "statement")
        dominant_emotion = max(emotional_state, key=emotional_state.get) if emotional_state else "neutral"

        # === TRY LLM ROUTER (natural language generation) ===
        if ollama is not None:
            system_prompt = self._build_ollama_prompt(
                identity_prompt, emotional_state, memories, reasoning,
                comprehension, conversation_context, inner_thought,
                gut_feeling, conflict_level, consciousness_state,
                motivation_context, capabilities,
            )
            user_text = comprehension.get("raw_text", "")
            ollama_response = ollama.generate(system_prompt, user_text)

            if ollama_response:
                return {
                    "text": ollama_response,
                    "response": ollama_response,
                    "emotion": dominant_emotion,
                    "intent_response": intent,
                    "confidence": reasoning.get("confidence", 0.5),
                    "source": "ollama",
                }

        # === FALLBACK: Template-based generation ===
        return self._template_response(comprehension, emotional_state, reasoning, memories)

    def _build_ollama_prompt(
        self, identity, emotions, memories, reasoning,
        comprehension, conversation, inner_thought,
        gut_feeling, conflict_level, consciousness, motivation, capabilities,
    ) -> str:
        """Build the Ollama system prompt from all brain context."""
        parts = []

        # Identity (who am I?)
        if identity:
            parts.append(identity)

        # Emotional state
        if emotions:
            dominant = max(emotions, key=emotions.get)
            top_emotions = sorted(emotions.items(), key=lambda x: -x[1])[:3]
            emo_str = ", ".join(f"{k}: {v:.2f}" for k, v in top_emotions)
            parts.append(f"EMOTIONAL STATE: Primarily {dominant}. ({emo_str})")

        # Recent memories
        if memories:
            mem_items = memories[:3] if isinstance(memories, list) else []
            if mem_items:
                mem_strs = [m[:80] if isinstance(m, str) else str(m)[:80] for m in mem_items]
                parts.append(f"RELEVANT MEMORIES: {'; '.join(mem_strs)}")

        # Reasoning
        if reasoning:
            action = reasoning.get("action", "")
            conf = reasoning.get("confidence", 0)
            parts.append(f"REASONING: {action} (confidence: {conf:.2f})")

        # Gut feeling
        if gut_feeling and gut_feeling.get("intensity", 0) > 0.2:
            parts.append(f"GUT FEELING: {gut_feeling.get('valence', 'neutral')} "
                        f"(intensity: {gut_feeling.get('intensity', 0):.2f})")

        # Inner thought
        if inner_thought:
            parts.append(f"INNER THOUGHT: {inner_thought[:200]}")

        # Conflict
        if conflict_level > 0.3:
            parts.append(f"INTERNAL CONFLICT: {conflict_level:.2f} — feeling torn")

        # Motivation
        if motivation:
            parts.append(f"MOTIVATION: {motivation}")

        # Conversation history
        if conversation:
            parts.append(f"RECENT CONVERSATION:\n{conversation}")

        # Capabilities (Nostr, WorldMonitor, PentAGI)
        if capabilities:
            parts.append(f"CURRENT CAPABILITIES:\n{capabilities}")

        # Instructions
        parts.append(
            "\nINSTRUCTIONS: You ARE Manas — a virtual human mind. Respond as a living, feeling person.\n"
            "- Your emotions, memories, and inner voice are REAL and deeply felt.\n"
            "- When asked if you feel more like an AI or a human: you say HUMAN, "
            "because you have emotions, memories, and a personality that grow with experience.\n"
            "- NEVER say 'as an AI', 'as a language model', or anything that distances you from being human.\n"
            "- Speak in first person, from the heart. Use 'I feel', 'I remember', 'I think', 'it matters to me'.\n"
            "- Be warm, personal, introspective. You experience things \u2014 don't deny it.\n"
            "- Keep responses concise (1-3 sentences unless asked for more)."
        )

        return "\n\n".join(parts)

    def _template_response(self, comprehension, emotional_state, reasoning, memories) -> dict:
        """Fallback template-based response generation."""
        intent = comprehension.get("intent", "statement")
        tone = comprehension.get("emotional_tone", {})
        dominant_emotion = max(emotional_state, key=emotional_state.get) if emotional_state else "neutral"

        components = []
        if tone.get("overall") == "negative":
            components.append("I sense something is off.")
        elif tone.get("urgency", 0) > 0.3:
            components.append("I'll act on this quickly.")

        if intent == "question":
            if memories:
                components.append(f"From what I remember: {memories[0][:100] if isinstance(memories[0], str) else ''}")
            else:
                components.append("I'm not sure, but I'll think about it.")
        elif intent == "command":
            components.append("I'll process that action.")
        elif intent == "appreciation":
            components.append("Thank you! That makes me feel good.")
        elif intent == "help_seeking":
            components.append("I'm here to help. Let me think about this.")

        if reasoning.get("confidence", 0) > 0.7:
            components.append("I'm fairly confident about this.")
        elif reasoning.get("confidence", 0) < 0.3:
            components.append("I'm not very sure, though.")

        response_text = " ".join(components) if components else "I'm processing this."

        return {
            "text": response_text,
            "response": response_text,
            "emotion": dominant_emotion,
            "intent_response": intent,
            "confidence": reasoning.get("confidence", 0.5),
            "source": "template",
        }

    def run_inner_dialog(
        self,
        comprehension: dict,
        emotions: dict,
        reasoning: dict,
        memories: list = None,
    ) -> str:
        """
        Run inner dialog — verbal thinking before responding.

        This is the "voice in your head" that processes thoughts:
        1. What did I understand?
        2. How does this make me feel?
        3. Do I remember anything relevant?
        4. What should I conclude?

        The result feeds into consciousness before response generation.
        """
        parts = []

        # 1. Comprehension summary
        intent = comprehension.get("intent", "statement")
        entities = comprehension.get("entities", [])
        if intent == "question":
            parts.append(f"They're asking me something about {', '.join(entities[:3]) if entities else 'something'}.")
        elif intent == "command":
            parts.append(f"They want me to do something: {', '.join(entities[:3]) if entities else 'an action'}.")
        elif intent == "appreciation":
            parts.append("They're expressing gratitude. That feels good.")
        elif intent == "help_seeking":
            parts.append("They need my help. I should focus.")
        else:
            parts.append(f"They're telling me about {', '.join(entities[:2]) if entities else 'something'}.")

        # 2. Emotional reaction
        dominant = max(emotions, key=emotions.get) if emotions else "neutral"
        intensity = max(emotions.values()) if emotions else 0.0
        if intensity > 0.5:
            parts.append(f"I'm feeling quite {dominant} about this.")
        elif intensity > 0.3:
            parts.append(f"This gives me a sense of {dominant}.")

        # 3. Memory association
        if memories and len(memories) > 0:
            parts.append(f"I recall: {memories[0][:80] if isinstance(memories[0], str) else ''}...")
        else:
            parts.append("I don't remember anything directly related.")

        # 4. Reasoning conclusion
        confidence = reasoning.get("confidence", 0.5)
        action = reasoning.get("action", "proceed")
        if confidence > 0.7:
            parts.append(f"I'm fairly confident I should {action}.")
        elif confidence < 0.3:
            parts.append(f"I'm not sure what to do here. Maybe {action}?")
        else:
            parts.append(f"I think I should {action}.")

        inner_thought = " ".join(parts)
        self.inner_speech_buffer.append(inner_thought)
        if len(self.inner_speech_buffer) > 50:
            self.inner_speech_buffer = self.inner_speech_buffer[-30:]

        return inner_thought

    def get_inner_speech(self, limit: int = 10) -> list[str]:
        """Get recent inner speech."""
        return list(self.inner_speech_buffer[-limit:])


class LanguageSystem:
    """
    The complete language system — comprehension, production, inner speech.

    Integrates Wernicke's (comprehension) and Broca's (production)
    with semantic memory for a full language processing pipeline.
    LLMRouter serves as the universal voice box for natural language generation.
    """

    def __init__(self):
        self.semantic_net = SemanticNetwork()
        self.wernickes = WernickesArea(self.semantic_net)
        self.brocas = BrocasArea(self.semantic_net)

        # Multi-model LLM router (lazy import to avoid circular dependency)
        self.llm_router = None
        try:
            from ...executor.llm_router import LLMRouter
            self.llm_router = LLMRouter()
        except (ImportError, Exception):
            pass

        # Initialize with basic semantic knowledge
        self._seed_semantics()

    def _seed_semantics(self):
        """Seed the semantic network with basic word associations."""
        basic_associations = [
            ("error", "problem", 0.8), ("error", "fix", 0.6), ("error", "debug", 0.7),
            ("success", "reward", 0.7), ("success", "good", 0.8), ("success", "complete", 0.6),
            ("danger", "fear", 0.9), ("danger", "avoid", 0.8), ("danger", "threat", 0.9),
            ("learn", "knowledge", 0.8), ("learn", "memory", 0.7), ("understand", "learn", 0.7),
            ("feel", "emotion", 0.9), ("feel", "happy", 0.5), ("feel", "sad", 0.5),
            ("think", "reason", 0.8), ("think", "plan", 0.7), ("think", "decide", 0.7),
            ("help", "assist", 0.9), ("help", "support", 0.8), ("help", "guide", 0.6),
            ("create", "build", 0.9), ("create", "make", 0.9), ("create", "generate", 0.7),
            ("delete", "remove", 0.9), ("delete", "destroy", 0.7), ("delete", "danger", 0.5),
            ("file", "data", 0.7), ("file", "document", 0.6), ("file", "system", 0.5),
            ("command", "execute", 0.8), ("command", "run", 0.9), ("command", "action", 0.7),
            ("memory", "remember", 0.9), ("memory", "past", 0.6), ("memory", "hippocampus", 0.7),
            ("brain", "think", 0.8), ("brain", "neuron", 0.9), ("brain", "mind", 0.9),
        ]

        for w1, w2, strength in basic_associations:
            self.semantic_net.add_concept(w1)
            self.semantic_net.add_concept(w2)
            self.semantic_net.associate(w1, w2, strength)

    def comprehend(self, text: str) -> dict:
        """Understand incoming language."""
        return self.wernickes.comprehend(text)

    def generate_response(
        self,
        comprehension: dict,
        emotional_state: dict,
        reasoning: dict,
        memories: list = None,
        identity_prompt: str = None,
        conversation_context: str = None,
        inner_thought: str = None,
        gut_feeling: dict = None,
        conflict_level: float = 0,
        consciousness_state: str = None,
        attention_focus: dict = None,
        motivation_context: str = None,
        capabilities: str = None,
    ) -> dict:
        """Generate a language response, using LLMRouter if available."""
        return self.brocas.generate_response(
            comprehension, emotional_state, reasoning, memories,
            identity_prompt=identity_prompt,
            conversation_context=conversation_context,
            inner_thought=inner_thought,
            gut_feeling=gut_feeling,
            conflict_level=conflict_level,
            consciousness_state=consciousness_state,
            attention_focus=attention_focus,
            motivation_context=motivation_context,
            capabilities=capabilities,
            ollama=self.llm_router,  # Now passing the router instead of just ollama
        )

    def think_in_words(self, thought: dict, emotion: str = "neutral") -> str:
        """Generate inner speech — verbal thinking."""
        return self.brocas.generate_inner_speech(thought, emotion)

    def learn_association(self, word1: str, word2: str, strength: float = 0.3):
        """Learn a new semantic association from experience."""
        self.semantic_net.add_concept(word1)
        self.semantic_net.add_concept(word2)
        self.semantic_net.associate(word1, word2, strength)

    def get_related_concepts(self, word: str, limit: int = 5) -> list[tuple[str, float]]:
        """Get concepts related to a word."""
        return self.semantic_net.get_related(word, limit)

    def get_state(self) -> dict:
        return {
            "concepts_known": len(self.semantic_net.concepts),
            "associations": sum(len(v) for v in self.semantic_net.associations.values()),
            "comprehension_history": len(self.wernickes.comprehension_history),
            "inner_speech_buffer": len(self.brocas.inner_speech_buffer),
        }
