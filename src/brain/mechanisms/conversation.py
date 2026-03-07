"""
Conversation Memory — Multi-turn dialog tracking.

Like human conversational memory:
- Remembers what was said recently (working memory for dialog)
- Tracks emotional context at each turn
- Provides context window for language generation
- Persists across sessions via SQLite

This is NOT long-term memory (that's hippocampus).
This is the short-term "what were we just talking about?" buffer.
"""

import time
import json
import sqlite3
import uuid
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""
    role: str                # "user" or "manas"
    content: str
    timestamp: float
    emotional_context: dict  # snapshot of emotional state
    turn_number: int
    session_id: str


class ConversationManager:
    """
    Tracks multi-turn dialog with emotional context.

    Uses SQLite for persistence (pattern from hippocampus.py).
    Provides formatted context windows for Ollama prompts.
    """

    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.current_session_id = str(uuid.uuid4())[:8]
        self.turn_counter = 0
        self._init_db()

    def _init_db(self):
        """Initialize the conversation database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                emotional_context TEXT DEFAULT '{}',
                turn_number INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_session
            ON conversations(session_id, turn_number)
        """)
        conn.commit()
        conn.close()

    def store_turn(
        self,
        role: str,
        content: str,
        emotional_context: dict = None,
    ) -> ConversationTurn:
        """Store a conversation turn."""
        self.turn_counter += 1
        now = time.time()
        emotions = emotional_context or {}

        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=now,
            emotional_context=emotions,
            turn_number=self.turn_counter,
            session_id=self.current_session_id,
        )

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO conversations
            (session_id, role, content, timestamp, emotional_context, turn_number)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (turn.session_id, turn.role, turn.content[:5000],
             turn.timestamp, json.dumps(emotions), turn.turn_number),
        )
        conn.commit()
        conn.close()

        return turn

    def get_recent_turns(self, n: int = 10) -> list[ConversationTurn]:
        """Get the last N turns from the current session."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT * FROM conversations
            WHERE session_id = ?
            ORDER BY turn_number DESC LIMIT ?""",
            (self.current_session_id, n),
        ).fetchall()
        conn.close()

        turns = []
        for row in reversed(rows):  # oldest first
            turns.append(ConversationTurn(
                role=row["role"],
                content=row["content"],
                timestamp=row["timestamp"],
                emotional_context=json.loads(row["emotional_context"]),
                turn_number=row["turn_number"],
                session_id=row["session_id"],
            ))
        return turns

    def get_context_window(self, n: int = 5) -> str:
        """
        Get formatted conversation context for Ollama prompt injection.

        Returns a string like:
        User: Hello there
        Manas: Hello! I'm feeling curious today.
        User: What can you do?
        """
        turns = self.get_recent_turns(n)
        if not turns:
            return ""

        lines = []
        for turn in turns:
            speaker = "User" if turn.role == "user" else "Manas"
            lines.append(f"{speaker}: {turn.content[:300]}")
        return "\n".join(lines)

    def get_turn_count(self) -> int:
        """Total turns in current session."""
        return self.turn_counter

    def get_session_summary(self) -> dict:
        """Summary of the current conversation session."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT COUNT(*) FROM conversations WHERE session_id = ?",
            (self.current_session_id,),
        ).fetchone()
        total = row[0] if row else 0
        conn.close()

        return {
            "session_id": self.current_session_id,
            "turns": total,
            "turn_counter": self.turn_counter,
        }

    def start_new_session(self):
        """Start a new conversation session."""
        self.current_session_id = str(uuid.uuid4())[:8]
        self.turn_counter = 0
