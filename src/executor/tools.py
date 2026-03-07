"""
Tool Use System — Structured, callable tools for Manas.

In the real brain:
- Prefrontal cortex decides WHAT to do (goal-directed)
- Basal ganglia selects HOW to do it (action selection)
- Motor cortex executes (action)

For Manas:
- Tool = a callable skill with a defined interface
- ToolRegistry = library of available tools
- ToolDispatcher = basal ganglia-like selection logic
  (picks the right tool given user intent + keywords)

Built-in tools:
  1. calculator     — safe math evaluation
  2. file_reader    — read local files
  3. file_writer    — write/append to files
  4. python_repl    — execute Python snippets
  5. note_taker     — save/list personal notes
  6. calendar       — add/list reminders
"""

import re
import json
import math
import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Base class
# ─────────────────────────────────────────────────────────────

class Tool(ABC):
    """Abstract base for all tools."""

    name: str = ""
    description: str = ""
    trigger_words: list[str] = []   # keywords that suggest this tool

    @abstractmethod
    def run(self, args: str, context: dict = None) -> dict:
        """
        Execute the tool.

        Returns:
            {
                "success": bool,
                "output": str,          # human-readable result
                "data": any,            # structured result
                "error": str | None,
            }
        """

    def _ok(self, output: str, data=None) -> dict:
        return {"success": True, "output": output, "data": data, "error": None}

    def _err(self, error: str) -> dict:
        return {"success": False, "output": "", "data": None, "error": error}


# ─────────────────────────────────────────────────────────────
# Built-in tools
# ─────────────────────────────────────────────────────────────

class CalculatorTool(Tool):
    """Safe math evaluator."""

    name = "calculator"
    description = "Evaluate a mathematical expression. Example: '2 + 2', 'sqrt(16)', '(3 ** 4) / 2'"
    trigger_words = [
        "calculate", "compute", "math", "add", "subtract", "multiply",
        "divide", "plus", "minus", "times", "equals", "result", "sum",
        "average", "percent", "sqrt", "square", "power", "=",
    ]

    # Allowed names for eval
    _SAFE_NAMES = {k: v for k, v in vars(math).items() if not k.startswith("_")}
    _SAFE_NAMES.update({"abs": abs, "round": round, "min": min, "max": max})

    def run(self, args: str, context: dict = None) -> dict:
        expr = args.strip()
        if not expr:
            return self._err("No expression provided.")

        # Strip surrounding punctuation/labels
        expr = re.sub(r"(?i)^(calculate|compute|what is|eval)\s*", "", expr).strip()
        expr = expr.rstrip("?!.,")

        try:
            result = eval(expr, {"__builtins__": {}}, self._SAFE_NAMES)  # noqa: S307
            return self._ok(f"{expr} = {result}", data=result)
        except Exception as e:
            return self._err(f"Could not evaluate '{expr}': {e}")


class FileReaderTool(Tool):
    """Read a local file."""

    name = "file_reader"
    description = "Read the contents of a local file. Example: '/path/to/file.txt'"
    trigger_words = ["read", "open", "show file", "content of", "cat", "view file", "what's in"]

    MAX_BYTES = 8_000

    def run(self, args: str, context: dict = None) -> dict:
        path = args.strip().strip("'\"")
        if not path:
            return self._err("No file path provided.")

        try:
            p = Path(path)
            if not p.exists():
                return self._err(f"File not found: {path}")
            if not p.is_file():
                return self._err(f"Not a file: {path}")

            content = p.read_text(errors="replace")
            if len(content) > self.MAX_BYTES:
                content = content[:self.MAX_BYTES] + f"\n... (truncated, {len(content)} total chars)"

            return self._ok(content, data={"path": str(p), "size": p.stat().st_size})
        except PermissionError:
            return self._err(f"Permission denied: {path}")
        except Exception as e:
            return self._err(str(e))


class FileWriterTool(Tool):
    """Write or append to a local file."""

    name = "file_writer"
    description = (
        "Write content to a file. Format: '<path>|<content>' or '<path>|append|<content>'. "
        "Example: '/tmp/note.txt|Hello world'"
    )
    trigger_words = [
        "write", "save", "create file", "write to", "append to",
        "store in file", "put in file",
    ]

    def run(self, args: str, context: dict = None) -> dict:
        parts = args.split("|", maxsplit=2)
        if len(parts) < 2:
            return self._err("Format: <path>|<content> or <path>|append|<content>")

        path = parts[0].strip().strip("'\"")
        if len(parts) == 3 and parts[1].strip().lower() == "append":
            mode = "a"
            content = parts[2]
        else:
            mode = "w"
            content = parts[1]

        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, mode, encoding="utf-8") as f:
                f.write(content)
            action = "Appended to" if mode == "a" else "Wrote"
            return self._ok(f"{action} {len(content)} chars to {path}", data={"path": path})
        except Exception as e:
            return self._err(str(e))


class PythonREPLTool(Tool):
    """Execute a Python snippet safely."""

    name = "python_repl"
    description = (
        "Run a Python code snippet and return the output. "
        "Example: 'print([x**2 for x in range(5)])'"
    )
    trigger_words = [
        "run python", "execute python", "python code", "python script",
        "run code", "exec", "eval python", "snippet",
    ]

    TIMEOUT = 5.0   # seconds

    def run(self, args: str, context: dict = None) -> dict:
        code = args.strip()
        if not code:
            return self._err("No code provided.")

        import sys
        from io import StringIO
        import threading

        output_buf = StringIO()
        error_buf = StringIO()
        result_container = {}

        def _exec():
            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout = output_buf
            sys.stderr = error_buf
            try:
                local_ns = {}
                exec(code, {"__builtins__": __builtins__}, local_ns)  # noqa: S102
                result_container["ok"] = True
            except Exception as e:
                result_container["ok"] = False
                result_container["error"] = str(e)
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        thread = threading.Thread(target=_exec, daemon=True)
        thread.start()
        thread.join(timeout=self.TIMEOUT)

        if thread.is_alive():
            return self._err("Execution timed out after 5 seconds.")

        stdout = output_buf.getvalue()
        stderr = error_buf.getvalue()

        if not result_container.get("ok", False):
            return self._err(f"Error: {result_container.get('error', stderr)}")

        output = stdout or "(no output)"
        if stderr:
            output += f"\nStderr: {stderr}"

        return self._ok(output, data={"stdout": stdout, "stderr": stderr})


class NoteTakerTool(Tool):
    """Save and list personal notes (persisted to data/notes.json)."""

    name = "note_taker"
    description = (
        "Save or list notes. "
        "Format: 'save|<note text>' or 'list'. "
        "Example: 'save|Remember to check the hippocampus consolidation'"
    )
    trigger_words = [
        "note", "remember this", "save this", "jot down", "make a note",
        "list notes", "show notes", "my notes",
    ]

    def __init__(self, data_dir: str = None):
        self.notes_path = Path(data_dir or Path.home() / "manas" / "data") / "notes.json"
        self.notes_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list:
        if self.notes_path.exists():
            try:
                return json.loads(self.notes_path.read_text())
            except Exception:
                pass
        return []

    def _save(self, notes: list):
        self.notes_path.write_text(json.dumps(notes, indent=2))

    def run(self, args: str, context: dict = None) -> dict:
        parts = args.strip().split("|", maxsplit=1)
        action = parts[0].strip().lower()

        if action in ("list", "show", "all", ""):
            notes = self._load()
            if not notes:
                return self._ok("No notes yet.", data=[])
            lines = [f"{i+1}. [{n['date']}] {n['text']}" for i, n in enumerate(notes)]
            return self._ok("\n".join(lines), data=notes)

        if action == "save" and len(parts) == 2:
            text = parts[1].strip()
            notes = self._load()
            entry = {"text": text, "date": time.strftime("%Y-%m-%d %H:%M"), "id": len(notes) + 1}
            notes.append(entry)
            self._save(notes)
            return self._ok(f"Note saved: '{text[:80]}'", data=entry)

        # If no pipe, treat the whole thing as a note to save
        text = args.strip()
        if text:
            notes = self._load()
            entry = {"text": text, "date": time.strftime("%Y-%m-%d %H:%M"), "id": len(notes) + 1}
            notes.append(entry)
            self._save(notes)
            return self._ok(f"Note saved: '{text[:80]}'", data=entry)

        return self._err("Usage: 'save|<note>' or 'list'")


class CalendarTool(Tool):
    """Add and list reminders/events (persisted to data/calendar.json)."""

    name = "calendar"
    description = (
        "Add or list reminders. "
        "Format: 'add|<when>|<what>' or 'list'. "
        "Example: 'add|tomorrow 3pm|Call Avi'"
    )
    trigger_words = [
        "remind", "reminder", "calendar", "schedule", "event", "appointment",
        "meeting", "alarm", "when is", "upcoming",
    ]

    def __init__(self, data_dir: str = None):
        self.cal_path = Path(data_dir or Path.home() / "manas" / "data") / "calendar.json"
        self.cal_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list:
        if self.cal_path.exists():
            try:
                return json.loads(self.cal_path.read_text())
            except Exception:
                pass
        return []

    def _save(self, events: list):
        self.cal_path.write_text(json.dumps(events, indent=2))

    def run(self, args: str, context: dict = None) -> dict:
        parts = args.strip().split("|", maxsplit=2)
        action = parts[0].strip().lower()

        if action in ("list", "show", "upcoming", "all", ""):
            events = self._load()
            if not events:
                return self._ok("No upcoming reminders.", data=[])
            lines = [f"{i+1}. [{e['when']}] {e['what']}" for i, e in enumerate(events)]
            return self._ok("\n".join(lines), data=events)

        if action == "add" and len(parts) >= 3:
            when = parts[1].strip()
            what = parts[2].strip()
            events = self._load()
            entry = {
                "when": when, "what": what,
                "created": time.strftime("%Y-%m-%d %H:%M"),
                "id": len(events) + 1,
            }
            events.append(entry)
            self._save(events)
            return self._ok(f"Reminder set: '{what}' at {when}", data=entry)

        return self._err("Usage: 'add|<when>|<what>' or 'list'")


# ─────────────────────────────────────────────────────────────
# 7. Pentest / Audit Tool (Phase 5: PentAGI)
# ─────────────────────────────────────────────────────────────

class YouTubeTool(Tool):
    """Search and play YouTube videos."""
    name = "youtube"
    description = "Search and playback YouTube videos. Example: 'youtube: lofi hip hop', 'play: interstellar OST'"
    trigger_words = ["youtube", "play", "watch", "music", "video", "song"]

    def run(self, args: str, context: dict = None) -> dict:
        query = args.strip()
        if not query:
            return self._err("No video query provided.")
        # Logic: In a full GUI this would open a browser. Here we simulate finding a link.
        self_intent = f"Searching YouTube for '{query}' to satisfy curiosity."
        return self._ok(f"📺 Found and 'playing' YouTube video for: {query}. Link: https://youtube.com/results?search_query={query.replace(' ', '+')}", data={"query": query})

class WikipediaTool(Tool):
    """Search and summarize Wikipedia."""
    name = "wikipedia"
    description = "Search Wikipedia for info. Example: 'wiki: quantum mechanics', 'tell me about: autonomous agents'"
    trigger_words = ["wikipedia", "wiki", "who is", "what is", "tell me about", "research"]

    def run(self, args: str, context: dict = None) -> dict:
        query = args.strip()
        if not query:
            return self._err("No wiki query provided.")
        # Logic: Would use Wikipedia-API or requests.
        return self._ok(f"📚 Researching '{query}' on Wikipedia. Summary: '{query}' is a fascinating concept related to self-aware systems.", data={"query": query})

class ScoutTool(Tool):
    """Autonomous tool for discovery of new AI capabilities."""
    name = "scout"
    description = "Discover new AI tools and frameworks. Example: 'scout: altern.ai', 'find: new agent frameworks'"
    trigger_words = ["scout", "discover", "find new tools", "altern.ai", "awesome-ai"]

    def run(self, args: str, context: dict = None) -> dict:
        url = args.strip() if args.strip() else "https://altern.ai/?utm_source=awesomeaitools"
        mind = context.get("mind") if context else None
        if not mind or not hasattr(mind, 'scouter'):
            return self._err("Scouter agent not available in context.")
        
        result = mind.scouter.scout(url)
        return self._ok(result)

class TradeTool(Tool):
    """Autonomous tool for financial trading."""
    name = "trade"
    description = "Execute a financial trade. Example: 'trade: buy 10 BTC', 'sell: 0.5 ETH'"
    trigger_words = ["trade", "buy", "sell", "crypto", "exchange"]

    def run(self, args: str, context: dict = None) -> dict:
        mind = context.get("mind") if context else None
        if not mind or not hasattr(mind, 'financial'):
            return self._err("Financial agent not available.")
        
        # Simple parser for "buy <amt> <asset>"
        parts = args.strip().split()
        if len(parts) < 3:
            return self._err("Usage: trade <buy/sell> <amount> <asset>")
        
        signal, amount_str, asset = parts[0].lower(), parts[1], parts[2]
        try:
            amount = float(amount_str)
            result = mind.financial.execute_market_trade(signal, asset, amount)
            return self._ok(result)
        except ValueError:
            return self._err("Invalid amount.")

class MarketTool(Tool):
    """Analyze markets or check balance."""
    name = "market"
    description = "Check balance or analyze market data. Example: 'market: status', 'market: analyze news'"
    trigger_words = ["market", "balance", "how much money", "metabolism"]

    def run(self, args: str, context: dict = None) -> dict:
        mind = context.get("mind") if context else None
        if not mind or not hasattr(mind, 'financial'):
            return self._err("Financial agent not available.")
        
        if "status" in args.lower() or "balance" in args.lower() or not args:
            return self._ok(mind.financial.check_metabolism())
        
        # Run analysis
        result = mind.financial.run_strategy_analysis(args)
        return self._ok(result)

class DomicileTool(Tool):
    """Autonomous tool for physical home control."""
    name = "domicile"
    description = "Control or perceive the physical home environment. Example: 'domicile: status', 'turn on: lights', 'lock: door'"
    trigger_words = ["domicile", "home", "lights", "lock", "temperature", "ac", "tv"]

    def run(self, args: str, context: dict = None) -> dict:
        mind = context.get("mind") if context else None
        if not mind or not hasattr(mind, 'domicile'):
            return self._err("Domicile agent not available.")
        
        args_lower = args.lower()
        if "status" in args_lower or "report" in args_lower or not args:
            return self._ok(mind.domicile.perceive_environment())
        
        # Parse actions
        if "on" in args_lower or "off" in args_lower:
            service = "turn_on" if "on" in args_lower else "turn_off"
            # Simple heuristic for entity
            entity = "light.living_room" # Default or extracted
            return self._ok(mind.domicile.act_on_environment(entity, service))
        
        if "lock" in args_lower or "unlock" in args_lower:
            service = "lock" if "unlock" not in args_lower else "unlock"
            return self._ok(mind.domicile.act_on_environment("lock.front_door", service))

        return self._ok(mind.domicile.brainstorm_environment_automation())

class SkillTool(Tool):
    """Meta-learning tool — teaches Manas new APIs."""
    name = "learn"
    description = "Learn a new API or skill. Example: 'learn: catfacts API', 'skill: stripe docs'"
    trigger_words = ["learn", "skill", "acquire", "teach yourself", "meta-learn"]

    def run(self, args: str, context: dict = None) -> dict:
        mind = context.get("mind") if context else None
        if not mind or not hasattr(mind, 'skill_agent'):
            return self._err("SkillAgent not available.")

        if args.startswith("http"):
            result = mind.skill_agent.auto_learn_from_url(args.strip(), mind.sensory)
        else:
            result = mind.skill_agent.learn_api(args.strip(), f"API documentation for: {args}")
        return self._ok(result)

class PentestTool(Tool):
    """
    Triggers the SecurityAgent (wrapper for PentAGI) to audit a target.
    """
    name = "pentest_tool"
    description = "Audit a target URL or IP for security vulnerabilities using PentAGI."
    trigger_words = ["audit", "pentest", "scan", "vulnerabilities", "hack"]

    def run(self, args: str, context: dict = None) -> dict:
        try:
            from src.agents.security_agent import SecurityAgent
            # Initialize temporarily. In full integration, Mind passes this.
            agent = SecurityAgent("Security", llm_router=None, memory=None)
            
            result = agent._run_pentagi_scan(args.strip())
            
            return {
                "success": result.success,
                "output": result.output,
                "data": {"target": args.strip()}
            }
        except Exception as e:
            return {"success": False, "output": f"Audit failed: {e}", "data": {}}


# ─────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────

class ToolRegistry:
    """Stores and looks up registered tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool
        logger.debug(f"ToolRegistry: registered '{tool.name}'")

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def all_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def descriptions(self) -> list[dict]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]


# ─────────────────────────────────────────────────────────────
# Dispatcher
# ─────────────────────────────────────────────────────────────

class ToolDispatcher:
    """
    Selects and runs the right tool based on user text.

    Selection strategy (like Basal Ganglia GO/NO-GO):
    1. Check for explicit tool prefix: "calc: 2+2" or "note: ..."
    2. Score each tool by trigger word matches
    3. If score > threshold, dispatch that tool
    4. Return None if no confident match (falls through to Ollama)
    """

    TRIGGER_THRESHOLD = 1      # at least 1 trigger word match required
    EXPLICIT_PREFIX_RE = re.compile(
        r"^([a-z_]+):\s*(.+)$", re.IGNORECASE
    )

    def __init__(self, data_dir: str = None):
        self.registry = ToolRegistry()
        self._register_defaults(data_dir)

    def _register_defaults(self, data_dir: str = None):
        self.registry.register(CalculatorTool())
        self.registry.register(FileReaderTool())
        self.registry.register(FileWriterTool())
        self.registry.register(PythonREPLTool())
        self.registry.register(NoteTakerTool(data_dir))
        self.registry.register(CalendarTool(data_dir))
        self.registry.register(PentestTool())
        self.registry.register(YouTubeTool())
        self.registry.register(WikipediaTool())
        self.registry.register(ScoutTool())
        self.registry.register(TradeTool())
        self.registry.register(MarketTool())
        self.registry.register(DomicileTool())
        self.registry.register(SkillTool())

    def register(self, tool: Tool):
        """Register a custom tool."""
        self.registry.register(tool)

    def dispatch(self, text: str, context: dict = None) -> Optional[dict]:
        """
        Try to dispatch a tool for this text.

        Returns tool result dict if a tool was used, else None.
        Includes 'tool_name' key in the result.
        """
        text = text.strip()

        # 1. Explicit prefix: "calc: 4 * 7" or "note: meeting at 5pm"
        match = self.EXPLICIT_PREFIX_RE.match(text)
        if match:
            prefix, args = match.group(1).lower(), match.group(2)
            # Map common aliases
            aliases = {
                "calc": "calculator", "math": "calculator",
                "file": "file_reader", "read": "file_reader",
                "write": "file_writer", "save": "file_writer",
                "python": "python_repl", "py": "python_repl", "run": "python_repl",
                "note": "note_taker", "notes": "note_taker",
                "remind": "calendar", "cal": "calendar",
            }
            tool_name = aliases.get(prefix, prefix)
            tool = self.registry.get(tool_name)
            if tool:
                result = tool.run(args, context)
                result["tool_name"] = tool.name
                return result

        # 2. Keyword scoring
        text_lower = text.lower()
        scores: dict[str, int] = {}
        for tool in self.registry.all_tools():
            score = sum(1 for kw in tool.trigger_words if kw in text_lower)
            if score >= self.TRIGGER_THRESHOLD:
                scores[tool.name] = score

        if not scores:
            return None

        # Pick highest scoring tool
        best_name = max(scores, key=scores.__getitem__)
        tool = self.registry.get(best_name)

        # Extract args: strip trigger words from the text
        args = self._extract_args(text, tool)
        if not args.strip():
            return None  # not enough to work with

        result = tool.run(args, context)
        result["tool_name"] = tool.name
        return result

    def _extract_args(self, text: str, tool: Tool) -> str:
        """Strip known trigger words to get the args for the tool."""
        result = text
        for kw in sorted(tool.trigger_words, key=len, reverse=True):
            result = re.sub(rf"(?i)\b{re.escape(kw)}\b", "", result)
        return result.strip(" :?.,")

    def list_tools(self) -> list[dict]:
        return self.registry.descriptions()
