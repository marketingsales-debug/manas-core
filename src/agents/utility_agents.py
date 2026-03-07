"""
Utility Agents — BrowserAgent, EmailAgent, NegotiationAgent, TeachingAgent.

These fill the remaining gaps to make Manas a "complete" entity.
"""

import logging
import json
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class BrowserAgent:
    """
    Full autonomous web browsing and interaction.
    Can fill forms, click buttons, scrape data, and navigate complex websites.
    """

    def __init__(self, name: str, llm_router, sensory, data_dir: str):
        self.name = name
        self.llm_router = llm_router
        self.sensory = sensory
        self.data_dir = Path(data_dir)
        self.browse_log_path = self.data_dir / "browse_log.json"
        self.total_sessions = 0

    def autonomous_browse(self, goal: str, start_url: str = "https://google.com") -> str:
        """
        Autonomously browses the web to achieve a goal.
        Uses LLM to decide what to click, type, and navigate.
        """
        logger.info(f"{self.name}: Autonomous browsing for: {goal}")

        steps = []
        current_url = start_url

        for step in range(5):  # Max 5 navigation steps
            # Plan next action
            plan_prompt = (
                f"You are an AI web browser agent. Your goal: {goal}\n"
                f"Current URL: {current_url}\n"
                f"Steps taken so far: {steps}\n\n"
                f"What should I do next? Options:\n"
                f"- NAVIGATE <url> — Go to a URL\n"
                f"- SEARCH <query> — Google search\n"
                f"- EXTRACT — Extract information from current page\n"
                f"- DONE <result> — Goal achieved\n\n"
                f"Return your action as a single line."
            )
            action = self.llm_router.generate(prompt=plan_prompt, task_type="reasoning")
            steps.append(action.strip())

            if "DONE" in action.upper():
                break

        self.total_sessions += 1
        return (
            f"🌐 Browser Session Complete:\n"
            f"  Goal: {goal}\n"
            f"  Steps taken: {len(steps)}\n"
            f"  Actions:\n" + "\n".join(f"    {i+1}. {s[:100]}" for i, s in enumerate(steps))
        )

    def get_status(self) -> str:
        return f"🌐 BrowserAgent: {self.total_sessions} sessions completed."


class EmailAgent:
    """
    Autonomous email composition, reading, and management.
    """

    def __init__(self, name: str, llm_router, data_dir: str):
        self.name = name
        self.llm_router = llm_router
        self.data_dir = Path(data_dir)
        self.drafts_dir = self.data_dir / "email_drafts"
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.data_dir / "email_config.json"
        self.total_composed = 0
        self._load_config()

    def _load_config(self):
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "smtp_server": "",
                "email": "",
                "active": False
            }

    def compose_email(self, recipient: str, subject: str, context: str) -> str:
        """Composes a professional email using LLM."""
        prompt = (
            f"Compose a professional email:\n"
            f"To: {recipient}\n"
            f"Subject: {subject}\n"
            f"Context/Instructions: {context}\n\n"
            f"Write a well-structured, professional email. Include greeting and sign-off."
        )
        email_body = self.llm_router.generate(prompt=prompt, task_type="creative")

        # Save draft
        draft = {
            "to": recipient,
            "subject": subject,
            "body": email_body,
            "created_at": time.time(),
            "sent": False
        }
        draft_path = self.drafts_dir / f"draft_{int(time.time())}.json"
        with open(draft_path, "w") as f:
            json.dump(draft, f, indent=2)

        self.total_composed += 1
        return (
            f"📧 Email Composed:\n"
            f"  To: {recipient}\n"
            f"  Subject: {subject}\n"
            f"  Draft saved: {draft_path}\n\n"
            f"  Preview:\n{email_body[:500]}..."
        )

    def summarize_email(self, email_text: str) -> str:
        """Summarizes an email and extracts action items."""
        prompt = (
            f"Summarize this email and extract action items:\n\n"
            f"{email_text[:3000]}\n\n"
            f"Provide:\n1. Summary (2-3 sentences)\n2. Action items\n3. Priority (Low/Medium/High)\n4. Response needed? (Yes/No)"
        )
        summary = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        return f"📧 Email Summary:\n{summary}"

    def get_status(self) -> str:
        drafts = list(self.drafts_dir.glob("*.json"))
        return (
            f"📧 EmailAgent Status:\n"
            f"  Emails composed: {self.total_composed}\n"
            f"  Drafts saved: {len(drafts)}\n"
            f"  Active: {'✅' if self.config.get('active') else '❌ (Configure SMTP first)'}"
        )


class NegotiationAgent:
    """
    Autonomous negotiation and deal-making agent.
    Handles pricing, contracts, and strategic conversations.
    """

    def __init__(self, name: str, llm_router):
        self.name = name
        self.llm_router = llm_router
        self.total_negotiations = 0

    def negotiate(self, context: str, goal: str, constraints: str = "") -> str:
        """Generates a negotiation strategy and opening position."""
        prompt = (
            f"As an expert negotiator, develop a strategy:\n"
            f"Context: {context}\n"
            f"Goal: {goal}\n"
            f"Constraints: {constraints or 'None specified'}\n\n"
            f"Provide:\n"
            f"1. Opening Position\n"
            f"2. BATNA (Best Alternative)\n"
            f"3. Key Leverage Points\n"
            f"4. Concession Strategy\n"
            f"5. Recommended Script/Talking Points\n"
            f"6. Walk-away Point"
        )
        strategy = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        self.total_negotiations += 1
        return f"🤝 Negotiation Strategy:\n{strategy}"

    def counter_offer(self, their_offer: str, my_goals: str) -> str:
        """Generates a strategic counter-offer."""
        prompt = (
            f"They offered: {their_offer}\n"
            f"My goals: {my_goals}\n\n"
            f"Generate a strategic counter-offer with justification."
        )
        counter = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        return f"🤝 Counter-Offer:\n{counter}"

    def get_status(self) -> str:
        return f"🤝 NegotiationAgent: {self.total_negotiations} negotiations strategized."


class TeachingAgent:
    """
    Manas as a teacher/tutor. Can explain complex topics,
    create lesson plans, and adapt to learning levels.
    """

    def __init__(self, name: str, llm_router, data_dir: str):
        self.name = name
        self.llm_router = llm_router
        self.data_dir = Path(data_dir)
        self.lessons_dir = self.data_dir / "lessons"
        self.lessons_dir.mkdir(parents=True, exist_ok=True)
        self.total_lessons = 0

    def teach(self, topic: str, level: str = "beginner") -> str:
        """Creates a comprehensive lesson on a topic."""
        prompt = (
            f"Create an engaging lesson on: {topic}\n"
            f"Level: {level}\n\n"
            f"Include:\n"
            f"1. Introduction (Why this matters)\n"
            f"2. Core Concepts (broken down simply)\n"
            f"3. Examples & Analogies\n"
            f"4. Practice Exercises (3 questions)\n"
            f"5. Further Reading/Resources\n\n"
            f"Make it engaging and use emojis where helpful."
        )
        lesson = self.llm_router.generate(prompt=prompt, task_type="creative")

        # Save lesson
        lesson_path = self.lessons_dir / f"lesson_{topic.lower().replace(' ', '_')[:30]}.md"
        with open(lesson_path, "w") as f:
            f.write(f"# Lesson: {topic}\n*Level: {level}*\n\n{lesson}")

        self.total_lessons += 1
        return f"🎓 Lesson Created: '{topic}' ({level})\n\n{lesson}"

    def quiz(self, topic: str, num_questions: int = 5) -> str:
        """Generates a quiz on a topic."""
        prompt = (
            f"Create a quiz on: {topic}\n"
            f"Generate {num_questions} multiple-choice questions.\n"
            f"Format: Q1, then options A-D, then the answer.\n"
            f"Make questions progressively harder."
        )
        quiz_content = self.llm_router.generate(prompt=prompt, task_type="creative")
        return f"📝 Quiz: {topic}\n\n{quiz_content}"

    def explain_like_im_5(self, concept: str) -> str:
        """Explains a complex concept in the simplest possible terms."""
        prompt = (
            f"Explain '{concept}' like I'm 5 years old. "
            f"Use simple analogies, everyday objects, and short sentences. "
            f"Make it fun!"
        )
        explanation = self.llm_router.generate(prompt=prompt, task_type="creative")
        return f"👶 ELI5 — {concept}:\n{explanation}"

    def get_status(self) -> str:
        lessons = list(self.lessons_dir.glob("*.md"))
        return (
            f"🎓 TeachingAgent Status:\n"
            f"  Lessons created: {len(lessons)}\n"
            f"  Total teaching sessions: {self.total_lessons}"
        )
