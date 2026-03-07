"""
Sleep System - Sleep cycles, memory consolidation, and dreaming.

In the real brain:
- Sleep is NOT passive — it's an active process critical for survival
- NREM (Non-REM) sleep: memory consolidation, synaptic pruning
  - Stage 1: Light sleep, theta waves
  - Stage 2: Sleep spindles, K-complexes
  - Stage 3: Deep sleep, delta waves (most restorative)
- REM sleep: dreaming, emotional processing, creative connections
  - Brain is highly active (paradoxical sleep)
  - Replays memories in novel combinations
  - Processes emotional experiences
  - Makes creative associations

Memory consolidation during sleep:
1. Hippocampus replays recent memories to neocortex
2. Important memories are strengthened
3. Weak/irrelevant memories are pruned
4. Emotional memories are reprocessed (therapy)
5. Patterns are extracted from specific memories (generalization)

Synaptic homeostasis hypothesis (Tononi):
- During wake: synapses strengthen (learning)
- During sleep: global synaptic downscaling
- This prevents saturation and enables next day's learning
- "Sleep to forget, sleep to remember"

For Manas:
- Periodic consolidation of memories
- Pruning of weak memories
- Dream-like creative combination of memories
- Synaptic downscaling (prevent network saturation)
- Emotional reprocessing
"""

import time
import numpy as np


class SleepStage:
    """A single sleep stage with specific properties."""

    def __init__(self, name: str, duration: float, depth: float):
        self.name = name
        self.duration = duration    # relative duration
        self.depth = depth          # how deep (0 = awake, 1 = deep sleep)
        self.function = ""          # what this stage does


class SleepCycle:
    """
    A complete sleep cycle (~90 minutes in humans).

    Stages: Wake -> NREM1 -> NREM2 -> NREM3 -> NREM2 -> REM
    Each cycle gets shorter deep sleep and longer REM.
    """

    STAGES = [
        SleepStage("nrem1", duration=0.05, depth=0.2),    # Light sleep
        SleepStage("nrem2", duration=0.25, depth=0.5),    # Sleep spindles
        SleepStage("nrem3", duration=0.25, depth=0.9),    # Deep sleep
        SleepStage("nrem2_return", duration=0.15, depth=0.5),
        SleepStage("rem", duration=0.30, depth=0.3),      # Dreaming
    ]

    def __init__(self):
        self.current_stage_idx: int = 0
        self.progress: float = 0.0  # 0 to 1 within current stage
        self.cycle_count: int = 0

    def advance(self, amount: float = 0.1) -> dict:
        """Advance through the sleep cycle."""
        stage = self.STAGES[self.current_stage_idx]
        self.progress += amount / stage.duration

        result = {
            "stage": stage.name,
            "depth": stage.depth,
            "progress": self.progress,
        }

        if self.progress >= 1.0:
            self.progress = 0.0
            self.current_stage_idx += 1
            if self.current_stage_idx >= len(self.STAGES):
                self.current_stage_idx = 0
                self.cycle_count += 1
                result["cycle_complete"] = True

        return result

    def get_current_stage(self) -> SleepStage:
        return self.STAGES[self.current_stage_idx]

    def reset(self):
        self.current_stage_idx = 0
        self.progress = 0.0


class MemoryReplay:
    """
    Hippocampal memory replay during sleep.

    The hippocampus replays recent memories during NREM sleep,
    transferring them to long-term storage in the neocortex.

    During REM: memories are replayed in novel combinations (dreams).
    """

    def __init__(self):
        self.replayed_memories: list[dict] = []
        self.dream_content: list[dict] = []

    def nrem_replay(self, memories: list[dict], importance_threshold: float = 0.3) -> dict:
        """
        NREM replay — consolidate important memories.

        1. Select memories above importance threshold
        2. Replay them (strengthen)
        3. Prune memories below threshold
        """
        strengthened = []
        pruned = []

        for memory in memories:
            importance = memory.get("importance", 0.5)
            emotional_intensity = memory.get("emotional_intensity", 0.0)

            # Emotional memories get priority (amygdala-hippocampus connection)
            effective_importance = importance + emotional_intensity * 0.2

            if effective_importance >= importance_threshold:
                # Strengthen this memory
                memory["importance"] = min(1.0, importance + 0.02)
                strengthened.append(memory)
                self.replayed_memories.append({
                    "content": memory.get("content", "")[:100],
                    "stage": "nrem",
                    "action": "strengthened",
                })
            else:
                # Mark for pruning (forgetting)
                memory["importance"] = max(0.0, importance - 0.05)
                if memory["importance"] < 0.05:
                    pruned.append(memory)

        return {
            "strengthened": len(strengthened),
            "pruned": len(pruned),
            "total_processed": len(memories),
        }

    def rem_dream(self, memories: list[dict], creativity: float = 0.5) -> dict:
        """
        REM dreaming — creative recombination of memories.

        Dreams mix memories in novel ways:
        - Random associations between unrelated memories
        - Emotional reprocessing
        - Creative problem-solving
        - Fear extinction (reprocessing scary memories safely)
        """
        if len(memories) < 2:
            return {"dream": "", "associations": []}

        # Select random memories to combine
        n_memories = min(5, len(memories))
        dream_memories = np.random.choice(memories, size=n_memories, replace=False).tolist()

        # Combine content creatively
        fragments = []
        associations = []
        for mem in dream_memories:
            content = mem.get("content", "")
            words = content.split()
            if words:
                # Take random fragments
                start = np.random.randint(0, max(1, len(words) - 3))
                fragment = " ".join(words[start:start + 5])
                fragments.append(fragment)

        # Create novel associations between memories
        for i in range(len(dream_memories) - 1):
            m1 = dream_memories[i]
            m2 = dream_memories[i + 1]
            if np.random.random() < creativity:
                associations.append({
                    "from": m1.get("content", "")[:50],
                    "to": m2.get("content", "")[:50],
                    "type": "dream_association",
                })

        dream_narrative = " ... ".join(fragments) if fragments else ""

        # Emotional reprocessing: reduce intensity of emotional memories
        for mem in dream_memories:
            if mem.get("emotional_intensity", 0) > 0.5:
                mem["emotional_intensity"] = max(0.1, mem["emotional_intensity"] - 0.05)

        dream_entry = {
            "dream": dream_narrative,
            "associations": associations,
            "memories_involved": len(dream_memories),
            "emotional_reprocessing": sum(
                1 for m in dream_memories if m.get("emotional_intensity", 0) > 0.3
            ),
        }
        self.dream_content.append(dream_entry)
        if len(self.dream_content) > 50:
            self.dream_content = self.dream_content[-30:]

        return dream_entry


class SynapticHomeostasis:
    """
    Synaptic homeostasis — global downscaling during sleep.

    During waking, learning strengthens many synapses.
    If unchecked, this leads to saturation (can't learn more).

    During deep sleep (NREM3):
    - All synapses are proportionally weakened
    - Strong synapses stay strong (relative difference preserved)
    - Weak synapses may be eliminated (pruning)
    - This makes room for new learning tomorrow

    "Sleep is the price we pay for learning" — Giulio Tononi
    """

    def __init__(self, downscale_factor: float = 0.95):
        self.downscale_factor = downscale_factor

    def downscale(self, synapses: list, threshold: float = 0.05) -> dict:
        """
        Apply synaptic downscaling.

        1. Multiply all weights by downscale_factor
        2. Prune synapses below threshold
        """
        pruned = 0
        total = len(synapses)

        for synapse in synapses:
            synapse.state.weight *= self.downscale_factor
            if synapse.state.weight < threshold:
                synapse.state.weight = 0.0
                pruned += 1

        return {
            "total_synapses": total,
            "downscaled": total - pruned,
            "pruned": pruned,
            "downscale_factor": self.downscale_factor,
        }


class SleepSystem:
    """
    The complete sleep system.

    Manages:
    - Sleep cycle progression
    - NREM memory consolidation
    - REM dreaming and emotional processing
    - Synaptic homeostasis
    - Wake/sleep transitions
    """

    def __init__(self):
        self.cycle = SleepCycle()
        self.replay = MemoryReplay()
        self.homeostasis = SynapticHomeostasis()

        self.is_sleeping: bool = False
        self.sleep_debt: float = 0.0     # accumulated need for sleep
        self.last_sleep_time: float = 0.0
        self.total_sleep_time: float = 0.0

    def accumulate_debt(self, amount: float = 0.01):
        """Accumulate sleep debt (increases while awake)."""
        self.sleep_debt = min(1.0, self.sleep_debt + amount)

    def needs_sleep(self) -> bool:
        """Should we sleep soon?"""
        return self.sleep_debt > 0.7

    def start_sleep(self):
        """Begin sleep."""
        self.is_sleeping = True
        self.cycle.reset()
        self.last_sleep_time = time.time()

    def sleep_step(
        self,
        memories: list[dict] = None,
        synapses: list = None,
        liquid_cluster = None
    ) -> dict:
        """
        Process one step of sleep.

        Different things happen at different stages.
        """
        if not self.is_sleeping:
            return {"status": "awake"}

        stage_info = self.cycle.advance(amount=0.1)
        stage = self.cycle.get_current_stage()

        result = {
            "stage": stage.name,
            "depth": stage.depth,
            "cycle": self.cycle.cycle_count,
        }

        # NREM3 (deep sleep): memory consolidation + synaptic homeostasis + LNN Optimization
        if stage.name == "nrem3":
            if memories:
                consolidation = self.replay.nrem_replay(memories)
                result["consolidation"] = consolidation
            if synapses:
                homeostasis = self.homeostasis.downscale(synapses)
                result["homeostasis"] = homeostasis
            if liquid_cluster:
                lnn_optimization = liquid_cluster.optimize()
                result["lnn_optimization"] = lnn_optimization

        # NREM2: lighter consolidation
        elif stage.name in ("nrem2", "nrem2_return"):
            if memories:
                consolidation = self.replay.nrem_replay(memories, importance_threshold=0.5)
                result["consolidation"] = consolidation

        # REM: dreaming
        elif stage.name == "rem":
            if memories:
                dream = self.replay.rem_dream(memories, creativity=0.5)
                result["dream"] = dream

        # Reduce sleep debt
        self.sleep_debt = max(0.0, self.sleep_debt - 0.05)
        self.total_sleep_time += 0.1

        # Check if sleep is done (3 complete cycles)
        if self.cycle.cycle_count >= 3:
            result["sleep_complete"] = True

        return result

    def wake_up(self) -> dict:
        """Wake up from sleep."""
        self.is_sleeping = False

        return {
            "slept_cycles": self.cycle.cycle_count,
            "sleep_debt": self.sleep_debt,
            "dreams": len(self.replay.dream_content),
            "memories_replayed": len(self.replay.replayed_memories),
        }

    def get_recent_dreams(self, limit: int = 5) -> list[dict]:
        """Get recent dream content."""
        return self.replay.dream_content[-limit:]

    def get_state(self) -> dict:
        return {
            "is_sleeping": self.is_sleeping,
            "sleep_debt": self.sleep_debt,
            "current_stage": self.cycle.get_current_stage().name if self.is_sleeping else "awake",
            "cycle_count": self.cycle.cycle_count,
            "total_sleep_time": self.total_sleep_time,
            "dreams_total": len(self.replay.dream_content),
        }
