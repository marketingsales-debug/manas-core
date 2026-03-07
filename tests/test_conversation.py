"""Tests for ConversationManager."""

import pytest
import os
from src.brain.mechanisms.conversation import ConversationManager


class TestConversationManager:
    def test_init_creates_db(self, tmp_data_dir):
        db_path = os.path.join(tmp_data_dir, "conv.db")
        cm = ConversationManager(db_path)
        assert os.path.exists(db_path)
        assert cm.turn_counter == 0

    def test_store_and_retrieve_turns(self, tmp_data_dir):
        cm = ConversationManager(os.path.join(tmp_data_dir, "conv.db"))

        cm.store_turn("user", "Hello!", {"happiness": 0.5})
        cm.store_turn("manas", "Hi there!", {"curiosity": 0.7})

        turns = cm.get_recent_turns(10)
        assert len(turns) == 2
        assert turns[0].role == "user"
        assert turns[0].content == "Hello!"
        assert turns[1].role == "manas"

    def test_context_window_format(self, tmp_data_dir):
        cm = ConversationManager(os.path.join(tmp_data_dir, "conv.db"))

        cm.store_turn("user", "What is 2+2?")
        cm.store_turn("manas", "4!")
        cm.store_turn("user", "Thanks")

        window = cm.get_context_window(5)
        assert "User: What is 2+2?" in window
        assert "Manas: 4!" in window
        assert "User: Thanks" in window

    def test_context_window_empty(self, tmp_data_dir):
        cm = ConversationManager(os.path.join(tmp_data_dir, "conv.db"))
        assert cm.get_context_window(5) == ""

    def test_turn_counter_increments(self, tmp_data_dir):
        cm = ConversationManager(os.path.join(tmp_data_dir, "conv.db"))
        cm.store_turn("user", "a")
        cm.store_turn("manas", "b")
        assert cm.turn_counter == 2

    def test_new_session(self, tmp_data_dir):
        cm = ConversationManager(os.path.join(tmp_data_dir, "conv.db"))
        cm.store_turn("user", "hello")
        old_session = cm.current_session_id

        cm.start_new_session()
        assert cm.current_session_id != old_session
        assert cm.turn_counter == 0

        # Old turns not in new session
        turns = cm.get_recent_turns(10)
        assert len(turns) == 0

    def test_session_summary(self, tmp_data_dir):
        cm = ConversationManager(os.path.join(tmp_data_dir, "conv.db"))
        cm.store_turn("user", "a")
        cm.store_turn("manas", "b")

        summary = cm.get_session_summary()
        assert summary["turns"] == 2
        assert summary["session_id"] == cm.current_session_id
