"""Tests for the Phase 3 Tool Use System."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import tempfile
from src.executor.tools import (
    CalculatorTool, FileReaderTool, FileWriterTool, PythonREPLTool,
    NoteTakerTool, CalendarTool, ToolRegistry, ToolDispatcher,
)


# ── Calculator ────────────────────────────────────────────────

class TestCalculatorTool:
    def setup_method(self):
        self.calc = CalculatorTool()

    def test_simple_add(self):
        r = self.calc.run("2 + 2")
        assert r["success"]
        assert r["data"] == 4

    def test_complex(self):
        r = self.calc.run("(3 ** 4) / 2")
        assert r["success"]
        assert r["data"] == 40.5

    def test_math_func(self):
        r = self.calc.run("sqrt(144)")
        assert r["success"]
        assert r["data"] == 12.0

    def test_bad_expr(self):
        r = self.calc.run("not_valid()")
        assert not r["success"]

    def test_strips_prefix(self):
        r = self.calc.run("calculate 10 * 10")
        assert r["success"]
        assert r["data"] == 100


# ── File Reader / Writer ──────────────────────────────────────

class TestFileTools:
    def test_write_then_read(self, tmp_path):
        path = str(tmp_path / "test.txt")
        writer = FileWriterTool()
        reader = FileReaderTool()

        wr = writer.run(f"{path}|Hello Manas!")
        assert wr["success"]

        rr = reader.run(path)
        assert rr["success"]
        assert "Hello Manas!" in rr["output"]

    def test_nonexistent_file(self):
        reader = FileReaderTool()
        r = reader.run("/tmp/definitely_does_not_exist_manas_xyz.txt")
        assert not r["success"]

    def test_append(self, tmp_path):
        path = str(tmp_path / "append.txt")
        writer = FileWriterTool()
        writer.run(f"{path}|First.")
        writer.run(f"{path}|append|Second.")
        reader = FileReaderTool()
        r = reader.run(path)
        assert "First." in r["output"]
        assert "Second." in r["output"]


# ── Python REPL ──────────────────────────────────────────────

class TestPythonREPL:
    def setup_method(self):
        self.repl = PythonREPLTool()

    def test_simple_print(self):
        r = self.repl.run("print(2 + 2)")
        assert r["success"]
        assert "4" in r["output"]

    def test_list_comprehension(self):
        r = self.repl.run("print([x**2 for x in range(5)])")
        assert r["success"]
        assert "[0, 1, 4, 9, 16]" in r["output"]

    def test_syntax_error(self):
        r = self.repl.run("def bad(: pass")
        assert not r["success"]


# ── Note Taker ───────────────────────────────────────────────

class TestNoteTaker:
    def test_save_and_list(self, tmp_path):
        nt = NoteTakerTool(data_dir=str(tmp_path))
        nt.run("save|Remember to check hippocampus")
        nt.run("save|Always back up memories")
        r = nt.run("list")
        assert r["success"]
        assert "hippocampus" in r["output"]
        assert "memories" in r["output"]


# ── Calendar ─────────────────────────────────────────────────

class TestCalendar:
    def test_add_and_list(self, tmp_path):
        cal = CalendarTool(data_dir=str(tmp_path))
        cal.run("add|tomorrow 3pm|Review Manas logs")
        r = cal.run("list")
        assert r["success"]
        assert "Manas" in r["output"]


# ── Registry ─────────────────────────────────────────────────

class TestToolRegistry:
    def test_register_and_get(self):
        reg = ToolRegistry()
        reg.register(CalculatorTool())
        assert reg.get("calculator") is not None
        assert reg.get("nonexistent") is None

    def test_descriptions(self):
        reg = ToolRegistry()
        reg.register(CalculatorTool())
        descs = reg.descriptions()
        assert any(d["name"] == "calculator" for d in descs)


# ── Dispatcher ───────────────────────────────────────────────

class TestToolDispatcher:
    def test_explicit_calc_prefix(self, tmp_path):
        d = ToolDispatcher(data_dir=str(tmp_path))
        r = d.dispatch("calc: 7 * 8")
        assert r is not None
        assert r["success"]
        assert r["tool_name"] == "calculator"
        assert r["data"] == 56

    def test_natural_calculate(self, tmp_path):
        d = ToolDispatcher(data_dir=str(tmp_path))
        r = d.dispatch("calculate 5 + 5")
        assert r is not None
        assert r["success"]

    def test_no_tool_for_chitchat(self, tmp_path):
        d = ToolDispatcher(data_dir=str(tmp_path))
        r = d.dispatch("how are you feeling today?")
        assert r is None  # no tool should fire for casual chat

    def test_note_prefix(self, tmp_path):
        d = ToolDispatcher(data_dir=str(tmp_path))
        r = d.dispatch("note: remember to test everything")
        assert r is not None
        assert r["tool_name"] == "note_taker"
