"""
Manas Web Server — FastAPI backend with WebSocket for live brain state.

Serves the web dashboard and exposes a REST + WebSocket API:
  GET  /          → Dashboard HTML
  GET  /state     → Full brain state JSON
  POST /chat      → Send a message, get full cognitive response
  GET  /memories  → Recent memories (searchable)
  GET  /emotions  → Emotional state + neurochemistry
  GET  /goals     → Goal system state
  WS   /ws        → Real-time push: emotions, thoughts, brain activity
"""

import asyncio
import logging
import time
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str

class MemorySearchRequest(BaseModel):
    query: str = ""
    limit: int = 10

# ─────────────────────────────────────────────────────────────
# WebSocket connection manager
# ─────────────────────────────────────────────────────────────

class ConnectionManager:
    """Manages active WebSocket connections and broadcasts."""

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


# ─────────────────────────────────────────────────────────────
# App factory
# ─────────────────────────────────────────────────────────────

def create_app(mind) -> FastAPI:
    """
    Create and configure the FastAPI application.

    `mind` is a shared Mind instance — the same one used for everything.
    """
    app = FastAPI(title="Manas Brain Dashboard", version="3.0")
    manager = ConnectionManager()

    # Serve static files (dashboard)
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)

    if (static_dir / "style.css").exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # ─────────────────────────────────────────────────────────
    # REST endpoints
    # ─────────────────────────────────────────────────────────

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Serve the main dashboard."""
        index_path = static_dir / "index.html"
        if index_path.exists():
            return HTMLResponse(index_path.read_text())
        return HTMLResponse("<h1>Dashboard not found</h1>")

    @app.get("/state")
    async def get_state():
        """Full brain state snapshot."""
        emotions = mind.neurochem.get_emotional_state()
        levels = mind.neurochem.get_levels()
        dominant, intensity = mind.neurochem.get_dominant_emotion()
        memory_counts = mind.hippocampus.get_memory_count()
        tiers = memory_counts.pop("_tiers", {})
        goals = mind.goal_system.get_state()
        consciousness = mind.consciousness.get_state() if hasattr(mind.consciousness, "get_state") else {}
        brain_activity = mind.brain.get_cluster_activities()
        thoughts = mind.autonomous.peek_thoughts(5)

        return {
            "emotions": emotions,
            "neurochemistry": levels,
            "dominant_emotion": dominant,
            "emotion_intensity": intensity,
            "brain_activity": brain_activity,
            "memory": {"by_type": memory_counts, "by_tier": tiers},
            "goals": goals,
            "consciousness": consciousness,
            "sleep_debt": mind.sleep_system.sleep_debt,
            "cycle": mind.cycle_count,
            "awake": mind.awake,
            "working_memory": mind.working_memory.get_state(),
            "autonomous": mind.autonomous.get_state(),
            "thoughts": [{"type": t.type, "content": t.content} for t in thoughts],
            "inner_monologue": list(mind.inner_monologue[-5:]),
            "timestamp": time.time(),
        }

    @app.post("/chat")
    async def chat(req: ChatRequest):
        """Process a message through the full cognitive pipeline."""
        try:
            response = mind.process_input(req.message)
            # Push update to all WS clients
            state_update = _build_ws_update(mind, response)
            await manager.broadcast({"type": "chat_response", **state_update})
            return {
                "response": response.get("language_response", ""),
                "emotion": response.get("dominant_emotion", "neutral"),
                "emotion_intensity": response.get("emotion_intensity", 0.5),
                "tool_result": response.get("tool_result"),
                "inner_thought": response.get("inner_thought", ""),
                "memories_recalled": response.get("memories_recalled", 0),
                "novelty": response.get("novelty", 0),
                "source": response.get("language_source", "template"),
            }
        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            return {"error": str(e), "response": "Something went wrong in my brain..."}

    @app.get("/memories")
    async def get_memories(query: str = "", limit: int = 10):
        """Search and return memories."""
        try:
            memories = mind.hippocampus.recall(query or "experience", limit=limit)
            return {
                "memories": [
                    {
                        "content": m.content[:200],
                        "type": m.memory_type,
                        "importance": round(m.importance, 3),
                        "emotional_intensity": round(m.emotional_intensity, 3),
                        "context": m.context[:100],
                        "access_count": m.access_count,
                    }
                    for m in memories
                ],
                "total": len(memories),
            }
        except Exception as e:
            return {"error": str(e), "memories": []}

    @app.get("/emotions")
    async def get_emotions():
        """Current emotional state and neurochemistry."""
        return {
            "emotions": mind.neurochem.get_emotional_state(),
            "neurochemistry": mind.neurochem.get_levels(),
            "dominant": mind.neurochem.get_dominant_emotion(),
        }

    @app.get("/goals")
    async def get_goals():
        """Goal system state."""
        goals = mind.goal_system.get_active_goals()
        return {
            "goals": [
                {
                    "id": g.id,
                    "name": g.name,
                    "category": g.category,
                    "priority": round(g.priority, 3),
                    "progress": round(g.progress, 3),
                    "active": g.active,
                }
                for g in goals
            ],
            "total_active": len(goals),
        }

    @app.get("/tools")
    async def get_tools():
        """List available tools."""
        return {"tools": mind.tools.list_tools()}

    # ─────────────────────────────────────────────────────────
    # WebSocket — live updates every 2 seconds
    # ─────────────────────────────────────────────────────────

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await manager.connect(ws)
        try:
            while True:
                # Push live brain state every 2s
                update = _build_ws_update(mind)
                await manager.broadcast({"type": "brain_state", **update})
                await asyncio.sleep(2.0)
        except WebSocketDisconnect:
            manager.disconnect(ws)
        except Exception as e:
            logger.debug(f"WS error: {e}")
            manager.disconnect(ws)

    # ─────────────────────────────────────────────────────────
    # Background heartbeat task
    # ─────────────────────────────────────────────────────────

    @app.on_event("startup")
    async def start_heartbeat():
        mind.start()
        asyncio.create_task(_heartbeat(mind, manager))

    return app


def _build_ws_update(mind, response: dict = None) -> dict:
    """Build a compact WebSocket update payload."""
    emotions = mind.neurochem.get_emotional_state()
    dominant, intensity = mind.neurochem.get_dominant_emotion()
    thoughts = mind.autonomous.peek_thoughts(10)
    return {
        "emotions": emotions,
        "dominant_emotion": dominant,
        "emotion_intensity": round(intensity, 3),
        "brain_activity": mind.brain.get_cluster_activities(),
        "inner_monologue": list(mind.inner_monologue[-3:]),
        "thoughts": [{"type": t.type, "content": t.content[:200]} for t in thoughts],
        "cycle": mind.cycle_count,
        "sleep_debt": round(mind.sleep_system.sleep_debt, 3),
        "chat": {
            "response": response.get("language_response", "") if response else "",
            "inner_thought": response.get("inner_thought", "") if response else "",
            "tool": response.get("tool_result") if response else None,
        } if response else None,
        "timestamp": time.time(),
    }


async def _heartbeat(mind, manager: ConnectionManager):
    """Periodic background broadcasts (even without user interaction)."""
    while True:
        await asyncio.sleep(2.0)
        if manager.active:
            try:
                update = _build_ws_update(mind)
                await manager.broadcast({"type": "brain_state", **update})
            except Exception as e:
                logger.debug(f"Heartbeat error: {e}")
