"""
Global Workspace Theory (GWT) - A model of consciousness.

Bernard Baars' Global Workspace Theory:
- Consciousness = a "global workspace" where information is broadcast
- Many specialized processors compete for access to the workspace
- The winner gets "broadcast" to all other processors
- This broadcast IS conscious awareness
- Unconscious processing: local, modular, not broadcast
- Conscious processing: global, integrated, broadcast to all

Think of it like a stage in a theater:
- Many actors (brain regions) work backstage (unconscious)
- Only one act can be on stage at a time (conscious)
- The audience (all brain regions) sees what's on stage
- Being on stage = being in consciousness

Neural correlates:
- Thalamo-cortical loops create the workspace
- Prefrontal cortex acts as the "director" (selects what's broadcast)
- Ignition: when a signal crosses threshold, it ignites global broadcasting
- The "neural correlate of consciousness" (NCC)

For Manas:
- Creates a unified conscious experience from multiple brain regions
- Only the most relevant information becomes "conscious"
- Unconscious processing happens in parallel
- Conscious content drives deliberate action and verbal report
"""

import time
import numpy as np


class WorkspaceItem:
    """A piece of information competing for conscious access."""

    def __init__(
        self,
        content_id: str,
        source: str,
        content: str,
        activation: float,
        content_type: str = "perception",
    ):
        self.content_id = content_id
        self.source = source          # which brain region
        self.content = content        # the actual information
        self.activation = activation  # how strongly it's competing
        self.content_type = content_type  # perception, memory, thought, emotion
        self.timestamp = time.time()
        self.broadcast_count: int = 0
        self.in_workspace: bool = False


class GlobalWorkspace:
    """
    The global workspace — the neural substrate of consciousness.

    1. Multiple brain regions submit content (compete for access)
    2. Content that crosses ignition threshold enters the workspace
    3. Workspace content is "broadcast" to all regions
    4. This broadcast enables coordinated, deliberate processing
    5. Only one "frame" of consciousness at a time (~100ms)
    """

    def __init__(self, ignition_threshold: float = 0.4, workspace_capacity: int = 3):
        self.ignition_threshold = ignition_threshold
        self.workspace_capacity = workspace_capacity

        # Current conscious content
        self.workspace: list[WorkspaceItem] = []

        # Competing content (not yet conscious)
        self.competition_buffer: list[WorkspaceItem] = []

        # Broadcast history (stream of consciousness)
        self.consciousness_stream: list[dict] = []

        # Global ignition state
        self.is_ignited: bool = False
        self.ignition_strength: float = 0.0

    def submit(self, item: WorkspaceItem):
        """
        Submit content for conscious access.

        Called by brain regions that have something important to report.
        """
        self.competition_buffer.append(item)

    def compete_and_broadcast(self) -> dict:
        """
        Run one cycle of conscious processing:
        1. All submitted items compete
        2. Strongest items that cross threshold enter workspace
        3. Workspace content is broadcast to all regions
        """
        if not self.competition_buffer and not self.workspace:
            return {"conscious_content": [], "is_ignited": False}

        # Combine existing workspace items (with decay) and new competitors
        all_candidates = list(self.competition_buffer)

        # Existing workspace items get a persistence bonus (but decay)
        for item in self.workspace:
            item.activation *= 0.85  # conscious content decays
            if item.activation > self.ignition_threshold * 0.5:
                all_candidates.append(item)

        # Sort by activation (competition)
        all_candidates.sort(key=lambda x: x.activation, reverse=True)

        # Select winners
        new_workspace = []
        for candidate in all_candidates[:self.workspace_capacity]:
            if candidate.activation >= self.ignition_threshold:
                candidate.in_workspace = True
                candidate.broadcast_count += 1
                new_workspace.append(candidate)

        # Check for ignition (threshold crossing with positive feedback)
        self.is_ignited = len(new_workspace) > 0
        if self.is_ignited:
            self.ignition_strength = max(item.activation for item in new_workspace)
            # Ignition amplifies workspace content (positive feedback)
            for item in new_workspace:
                item.activation = min(1.0, item.activation * 1.1)
        else:
            self.ignition_strength = 0.0

        self.workspace = new_workspace
        self.competition_buffer.clear()

        # Record in consciousness stream
        conscious_content = []
        for item in self.workspace:
            entry = {
                "source": item.source,
                "content": item.content[:200],
                "type": item.content_type,
                "activation": item.activation,
                "broadcast_count": item.broadcast_count,
                "timestamp": time.time(),
            }
            conscious_content.append(entry)

        if conscious_content:
            self.consciousness_stream.extend(conscious_content)
            if len(self.consciousness_stream) > 500:
                self.consciousness_stream = self.consciousness_stream[-300:]

        return {
            "conscious_content": conscious_content,
            "is_ignited": self.is_ignited,
            "ignition_strength": self.ignition_strength,
            "competing_items": len(all_candidates),
            "workspace_items": len(self.workspace),
        }

    def get_conscious_content(self) -> list[dict]:
        """What is currently in consciousness?"""
        return [
            {
                "source": item.source,
                "content": item.content[:200],
                "type": item.content_type,
                "activation": item.activation,
            }
            for item in self.workspace
        ]

    def get_stream_of_consciousness(self, limit: int = 20) -> list[dict]:
        """Recent conscious experiences (stream of consciousness)."""
        return self.consciousness_stream[-limit:]


class UnconsciousProcessing:
    """
    Parallel unconscious processing — the vast majority of brain activity.

    Most of what the brain does is unconscious:
    - Automatic pattern recognition
    - Emotional reactions (amygdala)
    - Motor control
    - Memory consolidation
    - Priming effects

    These happen in parallel and can influence behavior
    without conscious awareness.
    """

    def __init__(self):
        self.active_processes: dict[str, dict] = {}
        self.priming_effects: dict[str, float] = {}
        self.subliminal_activations: list[dict] = []

    def register_process(self, process_id: str, source: str, description: str):
        """Register an ongoing unconscious process."""
        self.active_processes[process_id] = {
            "source": source,
            "description": description,
            "start_time": time.time(),
            "output": None,
        }

    def complete_process(self, process_id: str, output: dict):
        """An unconscious process completed — may influence consciousness."""
        if process_id in self.active_processes:
            self.active_processes[process_id]["output"] = output
            self.active_processes[process_id]["end_time"] = time.time()

    def add_prime(self, concept: str, strength: float):
        """
        Priming: unconscious activation that biases future processing.

        If you see the word "doctor", you'll recognize "nurse" faster.
        """
        self.priming_effects[concept] = min(1.0, self.priming_effects.get(concept, 0) + strength)

    def get_priming(self, concept: str) -> float:
        """How much is a concept primed?"""
        # Priming decays
        strength = self.priming_effects.get(concept, 0.0)
        self.priming_effects[concept] = strength * 0.95  # decay
        return strength

    def decay_all(self):
        """Decay all priming effects."""
        self.priming_effects = {
            k: v * 0.9 for k, v in self.priming_effects.items() if v > 0.01
        }
        # Clean up completed processes
        cutoff = time.time() - 60
        self.active_processes = {
            k: v for k, v in self.active_processes.items()
            if v.get("end_time", time.time()) > cutoff
        }


class ConsciousnessSystem:
    """
    The complete consciousness system.

    Integrates:
    - Global workspace (what's conscious)
    - Unconscious processing (parallel, modular)
    - Stream of consciousness (temporal flow)
    - Metacognition (awareness of own mental states)
    """

    def __init__(self):
        self.workspace = GlobalWorkspace()
        self.unconscious = UnconsciousProcessing()
        self.awareness_level: float = 1.0  # 0 = unconscious, 1 = fully aware
        self.metacognition_enabled: bool = True

    def process_cycle(self) -> dict:
        """
        Run one cycle of consciousness (~100ms in real brain).

        1. Unconscious processes may submit to workspace
        2. Competition and broadcast
        3. Metacognitive monitoring
        """
        # Run workspace competition
        broadcast = self.workspace.compete_and_broadcast()

        # Metacognition: awareness of own mental state
        meta = {}
        if self.metacognition_enabled and broadcast["is_ignited"]:
            meta = {
                "aware_of": [item["type"] for item in broadcast["conscious_content"]],
                "clarity": self.awareness_level * broadcast["ignition_strength"],
                "cognitive_load": min(1.0, broadcast["competing_items"] / 10.0),
            }

        # Decay unconscious priming
        self.unconscious.decay_all()

        return {
            "broadcast": broadcast,
            "metacognition": meta,
            "awareness_level": self.awareness_level,
            "unconscious_processes": len(self.unconscious.active_processes),
        }

    def submit_to_consciousness(
        self,
        source: str,
        content: str,
        activation: float,
        content_type: str = "perception",
    ):
        """Submit content for possible conscious access."""
        if self.awareness_level < 0.1:
            return  # "Unconscious" — nothing enters workspace

        # Awareness level gates activation
        effective_activation = activation * self.awareness_level

        item = WorkspaceItem(
            content_id=f"{source}_{time.time()}",
            source=source,
            content=content,
            activation=effective_activation,
            content_type=content_type,
        )
        self.workspace.submit(item)

    def set_awareness(self, level: float):
        """
        Set awareness level.
        0.0 = deep sleep/unconscious
        0.5 = drowsy/dreaming
        1.0 = fully awake and aware
        """
        self.awareness_level = np.clip(level, 0.0, 1.0)

    def get_conscious_summary(self) -> str:
        """What am I conscious of right now?"""
        content = self.workspace.get_conscious_content()
        if not content:
            return "Mind is quiet — no conscious content."

        parts = []
        for item in content:
            parts.append(f"[{item['source']}] {item['content'][:100]}")
        return " | ".join(parts)

    def introspect(self) -> dict:
        """Metacognitive introspection — consciousness examining itself."""
        stream = self.workspace.get_stream_of_consciousness(limit=10)

        return {
            "current_content": self.workspace.get_conscious_content(),
            "awareness_level": self.awareness_level,
            "stream_length": len(self.workspace.consciousness_stream),
            "recent_stream": stream,
            "is_ignited": self.workspace.is_ignited,
            "unconscious_processes": len(self.unconscious.active_processes),
            "active_primes": len(self.unconscious.priming_effects),
        }

    def get_state(self) -> dict:
        return {
            "awareness_level": self.awareness_level,
            "is_ignited": self.workspace.is_ignited,
            "workspace_items": len(self.workspace.workspace),
            "consciousness_stream_length": len(self.workspace.consciousness_stream),
            "ignition_strength": self.workspace.ignition_strength,
        }
