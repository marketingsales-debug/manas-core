"""Tests for the Social Model (UserModel)."""

import os
import json
import pytest
from src.brain.mechanisms.social import UserModel


class TestUserModel:
    def setup_method(self):
        self.model = UserModel()

    def test_initial_state(self):
        assert self.model.name is None
        assert self.model.total_interactions == 0
        assert len(self.model.topic_frequency) == 0

    def test_observe_input_tracks_interactions(self):
        self.model.observe_input("Hello, how are you?")
        assert self.model.total_interactions == 1
        assert self.model.total_words_sent == 4

    def test_name_detection_im(self):
        self.model.observe_input("Hi, I'm Avi")
        assert self.model.name == "Avi"

    def test_name_detection_my_name_is(self):
        self.model.observe_input("My name is Sarah")
        assert self.model.name == "Sarah"

    def test_name_detection_call_me(self):
        self.model.observe_input("Please call me John")
        assert self.model.name == "John"

    def test_topic_tracking(self):
        self.model.observe_input("Tell me about artificial intelligence and neural networks")
        self.model.observe_input("I want to learn about artificial intelligence")
        # "artificial" and "intelligence" should appear 2x each
        assert self.model.topic_frequency["artificial"] == 2
        assert self.model.topic_frequency["intelligence"] == 2

    def test_top_interests(self):
        for _ in range(5):
            self.model.observe_input("Python programming is great")
        for _ in range(3):
            self.model.observe_input("Machine learning models")

        interests = self.model.get_top_interests(3)
        topic_names = [t for t, _ in interests]
        assert "python" in topic_names or "programming" in topic_names

    def test_style_detection_concise(self):
        for _ in range(5):
            self.model.observe_input("short msg")
        assert self.model.style["prefers_concise"] is True

    def test_question_ratio(self):
        self.model.observe_input("What is AI?")
        self.model.observe_input("How does it work?")
        self.model.observe_input("Interesting point")
        assert self.model.style["question_ratio"] > 0.5

    def test_command_tracking(self):
        for _ in range(4):
            self.model.observe_input("!run ls")
        self.model.observe_input("hello")
        assert self.model.style["uses_commands_often"] is True

    def test_user_context_generation(self):
        self.model.name = "Avi"
        self.model.observe_input("Tell me about Python programming")
        ctx = self.model.get_user_context()
        assert "Avi" in ctx

    def test_user_context_new_user(self):
        ctx = self.model.get_user_context()
        assert "New user" in ctx

    def test_get_state(self):
        self.model.observe_input("test message")
        state = self.model.get_state()
        assert "name" in state
        assert "total_interactions" in state
        assert state["total_interactions"] == 1


class TestUserModelPersistence:
    def test_save_and_load(self, tmp_data_dir):
        model = UserModel()
        model.name = "TestUser"
        model.observe_input("Python machine learning")
        model.observe_input("Neural network training")

        path = os.path.join(tmp_data_dir, "user_model.json")
        model.save_state(path)

        model2 = UserModel()
        loaded = model2.load_state(path)
        assert loaded is True
        assert model2.name == "TestUser"
        assert model2.total_interactions == 2
        assert model2.session_count == 1  # incremented on load

    def test_load_nonexistent(self, tmp_data_dir):
        model = UserModel()
        assert model.load_state(os.path.join(tmp_data_dir, "nope.json")) is False
