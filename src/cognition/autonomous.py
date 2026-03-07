"""
Autonomous Cognitive Loop — Manas thinks on its own when idle.

In the real brain:
- The Default Mode Network (DMN) activates when not focused on tasks
- Mind-wandering produces spontaneous thoughts, insights, plans
- The brain consolidates memories during idle periods
- Curiosity drives exploration even without external input
- Background monitoring: hunger, safety, social needs

For Manas:
- Background thread runs every 30-60s when user is idle
- DMN activates for mind-wandering and creative combinations
- Checks goals and generates thoughts about unfinished work
- Consolidates recent memories periodically
- Curiosity-driven reflection when boredom is high
- Generates spontaneous thoughts pushed to the user
"""

import time
import threading
import logging
from typing import Callable, Optional
from collections import deque

logger = logging.getLogger(__name__)


class SpontaneousThought:
    """A thought generated autonomously by the background loop."""

    def __init__(self, content: str, thought_type: str, source: str):
        self.content = content
        self.type = thought_type  # "reflection", "insight", "curiosity", "goal", "memory"
        self.source = source  # which system generated it
        self.timestamp = time.time()

    def __repr__(self):
        return f"[{self.type}] {self.content}"


class AutonomousLoop:
    """
    Background cognitive loop — Manas's idle-time thinking.

    Runs in a daemon thread that activates when the user hasn't
    interacted for a configurable idle threshold.

    Behaviors when idle:
    1. Mind-wander (DMN) — free association, creativity
    2. Goal review — check unfinished goals, generate plans
    3. Memory consolidation — strengthen important memories
    4. Curiosity exploration — reflect on novel topics
    5. Self-reflection — introspect on emotional state
    """

    def __init__(
        self,
        idle_threshold: float = 60.0,   # seconds before "idle" triggers
        tick_interval: float = 30.0,     # seconds between idle ticks
        max_thoughts: int = 50,          # max spontaneous thoughts buffered
    ):
        self.idle_threshold = idle_threshold
        self.tick_interval = tick_interval
        self.max_thoughts = max_thoughts

        # State
        self.last_interaction: float = time.time()
        self.spontaneous_thoughts: deque[SpontaneousThought] = deque(maxlen=max_thoughts)
        self.idle_cycles: int = 0
        self.total_thoughts: int = 0
        self.running: bool = False

        # Thread
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Callbacks — set by Mind to access brain systems
        self._mind_wander: Optional[Callable] = None
        self._check_goals: Optional[Callable] = None
        self._consolidate: Optional[Callable] = None
        self._get_curiosity: Optional[Callable] = None
        self._get_emotions: Optional[Callable] = None
        self._introspect: Optional[Callable] = None
        self._get_motivation: Optional[Callable] = None
        self._dispatch_tool: Optional[Callable] = None
        self._trigger_security_scan: Optional[Callable] = None
        self._run_maintenance: Optional[Callable] = None
        self._survey_graph: Optional[Callable] = None
        self._consolidate_synapses: Optional[Callable] = None

    def register_callbacks(
        self,
        mind_wander: Callable = None,
        check_goals: Callable = None,
        consolidate: Callable = None,
        get_curiosity: Callable = None,
        get_emotions: Callable = None,
        introspect: Callable = None,
        get_motivation: Callable = None,
        dispatch_tool: Callable = None,
        trigger_security_scan: Callable = None,
        run_maintenance: Callable = None,
        survey_graph: Callable = None,
        consolidate_synapses: Callable = None,
        check_host_capacity: Callable = None,
        get_energy_efficiency: Callable = None,
    ):
        """Register brain system callbacks for idle processing."""
        self._mind_wander = mind_wander
        self._check_goals = check_goals
        self._consolidate = consolidate
        self._get_curiosity = get_curiosity
        self._get_emotions = get_emotions
        self._introspect = introspect
        self._get_motivation = get_motivation
        self._dispatch_tool = dispatch_tool
        self._trigger_security_scan = trigger_security_scan
        self._run_maintenance = run_maintenance
        self._survey_graph = survey_graph
        self._consolidate_synapses = consolidate_synapses
        self._check_host_capacity = check_host_capacity
        self._get_energy_efficiency = get_energy_efficiency

    def start(self):
        """Start the autonomous background loop."""
        if self.running:
            return

        self.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="manas-autonomous"
        )
        self._thread.start()
        logger.info("AutonomousLoop: started background thinking")

    def stop(self):
        """Stop the autonomous loop gracefully."""
        self.running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info("AutonomousLoop: stopped")

    def notify_interaction(self):
        """Called when user interacts — resets idle timer."""
        self.last_interaction = time.time()
        self.idle_cycles = 0

    def get_new_thoughts(self, limit: int = 5) -> list[SpontaneousThought]:
        """Get recent spontaneous thoughts (drains the buffer)."""
        thoughts = []
        while self.spontaneous_thoughts and len(thoughts) < limit:
            thoughts.append(self.spontaneous_thoughts.popleft())
        return thoughts

    def peek_thoughts(self, limit: int = 5) -> list[SpontaneousThought]:
        """Peek at recent thoughts without removing them."""
        # Delegate to orchestrator/watcher
        # This line assumes 'mind' is available, which it isn't in this context.
        # It's likely a placeholder from the instruction.
        # mind.orchestrator.run("Watch https://news.ycombinator.com for interesting new AI frameworks.")
        return list(self.spontaneous_thoughts)[-limit:]

    def _trigger_self_improvement(self, mind):
        """Spire up the CoderAgent to review and optimize a piece of Manas's own code."""
        if not mind.awake: return
        logger.info("[Autonomous] Triggering SELF-IMPROVEMENT via CoderAgent...")

        task = "Review src/memory/working_memory.py. See if you can optimize the TTL eviction logic or add a useful metric. Do not break existing functionality. Run pytest tests/test_working_memory.py to verify."

        res = mind.orchestrator.active_agents["Coder"].run(task)
        if res.success:
            logger.info(f"Self-improvement success: {res.output[:100]}...")
            # If successful, reward the system
            mind.neurochem.release("dopamine", 0.3)
            mind.neurochem.release("serotonin", 0.2)

            # Log the improvement via meta-learning
            mind.meta_learning.record_metric_event(1.0)
        else:
            logger.warning("Self-improvement failed.")
            mind.neurochem.release("cortisol", 0.2)
            mind.meta_learning.record_metric_event(0.0)

    # ─────────────────────────────────
    # Internal loop
    # ─────────────────────────────────

    def _loop(self):
        """Main background loop — runs until stopped."""
        while not self._stop_event.is_set():
            # Phase 31: Dynamic tick rate based on Energy Efficiency
            current_tick = self.tick_interval
            if self._get_energy_efficiency:
                try:
                    efficiency = self._get_energy_efficiency()
                    if efficiency < 1.0:
                        # Throttle down (increase tick interval) if inefficient
                        current_tick = self.tick_interval * (1.0 / efficiency)
                        logger.debug(f"AutonomousLoop: Energy inefficient. Scaling tick rate to {current_tick:.1f}s")
                except Exception:
                    pass
                    
            self._stop_event.wait(timeout=current_tick)
            if self._stop_event.is_set():
                break

            idle_time = time.time() - self.last_interaction
            if idle_time < self.idle_threshold:
                continue  # user is still active

            # We're idle — think!
            self.idle_cycles += 1
            try:
                self._idle_tick()
            except Exception as e:
                logger.warning(f"AutonomousLoop: tick error: {e}")

    def _idle_tick(self):
        """
        One cycle of idle thinking.

        Rotates through different cognitive activities:
        - Cycle 1: Mind-wander (DMN)
        - Cycle 2: Review goals
        - Cycle 3: Self-reflect
        - Cycle 4: Memory consolidation
        - Then repeats
        """
        cycle_type = self.idle_cycles % 8

        if cycle_type == 0:
            self._do_mind_wander()
        elif cycle_type == 1:
            self._do_goal_review()
        elif cycle_type == 2:
            self._do_self_reflection()
        elif cycle_type == 3:
            self._do_curiosity_exploration()
        elif cycle_type == 4:
            self._do_attack_surface_scan()
        elif cycle_type == 5:
            self._do_self_defense_scan()
        elif cycle_type == 6:
            self._do_maintenance_check()
        elif cycle_type == 7:
            self._do_plasticity_evolution()
            
        if self.idle_cycles % 10 == 0:
             self._do_memory_consolidation()
             
        # Phase 30: Constantly check hosting capacity every idle tick
        if self._check_host_capacity:
            try:
                self._check_host_capacity()
            except Exception as e:
                logger.debug(f"AutonomousLoop: check_host_capacity error: {e}")

    def _do_maintenance_check(self):
        """Autonomously run system health checks and fix detected issues."""
        if not self._run_maintenance:
            return

        try:
            self._add_thought(
                "I should run a system health check to ensure all my components are functioning correctly.",
                "maintenance",
                "homeostasis"
            )
            
            # Start in a separate thread to avoid blocking the loop
            def run_and_act():
                res = self._run_maintenance("check_health")
                if not res.success:
                    self._add_thought(
                        "System health check detected issues. Initiating autonomous repair...",
                        "maintenance",
                        "self_healing"
                    )
                    # Trigger bug fix
                    self._run_maintenance("fix_bugs")
                else:
                    self._add_thought(
                        "System health check passed. All components are operational.",
                        "maintenance",
                        "homeostasis"
                    )

            threading.Thread(target=run_and_act, daemon=True).start()

        except Exception as e:
            logger.debug(f"AutonomousLoop: maintenance_check error: {e}")

    def _add_thought(self, content: str, thought_type: str, source: str):
        """Add a spontaneous thought to the buffer."""
        thought = SpontaneousThought(content, thought_type, source)
        self.spontaneous_thoughts.append(thought)
        self.total_thoughts += 1
        logger.debug(f"AutonomousLoop: [{thought_type}] {content[:80]}")

    def _do_mind_wander(self):
        """Activate DMN for free association."""
        if not self._mind_wander:
            return

        try:
            result = self._mind_wander()
            if not result or result.get("status") == "suppressed":
                return

            thoughts = result.get("thoughts", [])
            for thought in thoughts[:2]:
                if isinstance(thought, str) and len(thought) > 10:
                    self._add_thought(thought, "wandering", "DMN")

            insights = result.get("insights", [])
            for insight in insights[:1]:
                insight_text = insight.get("insight", str(insight)) if isinstance(insight, dict) else str(insight)
                if len(insight_text) > 10:
                    self._add_thought(insight_text, "insight", "creativity")
        except Exception as e:
            logger.debug(f"AutonomousLoop: mind_wander error: {e}")

    def _do_attack_surface_scan(self):
        """Periodically scans the local network or designated targets for vulnerabilities."""
        try:
            self._add_thought(
                "I should autonomously run a PentAGI security scan on the local network (192.168.1.0/24) to ensure perimeter safety and look for vulnerable devices.",
                "security_audit",
                "amygdala_vigilance"
            )
            logger.info("AutonomousLoop: Scheduled background network vulnerability scan.")
            
            if self._trigger_security_scan:
                threading.Thread(
                    target=self._trigger_security_scan,
                    args=("audit 192.168.1.0/24",),
                    daemon=True
                ).start()
                
        except Exception as e:
            logger.debug(f"AutonomousLoop: attack_surface_scan error: {e}")

    def _do_self_defense_scan(self):
        """Periodically runs an LLM vulnerability scan (Garak/ART) on native systems."""
        try:
            self._add_thought(
                "I should autonomously run Garak or IBM_ART against my own LLM inference endpoints to ensure I have not been jailbroken or poisoned.",
                "self_defense_audit",
                "amygdala_vigilance"
            )
            logger.info("AutonomousLoop: Scheduled background LLM vulnerability and adversarial robustness scan.")
            
            if self._trigger_security_scan:
                threading.Thread(
                    target=self._trigger_security_scan,
                    args=("audit self",),
                    daemon=True
                ).start()
                
        except Exception as e:
            logger.debug(f"AutonomousLoop: self_defense_scan error: {e}")

    def _do_goal_review(self):
        """Check goals and generate thoughts about unfinished work."""
        if not self._check_goals:
            return

        try:
            goals_state = self._check_goals()
            active = goals_state.get("active_goals", 0)
            top = goals_state.get("top_goal", "none")

            if active > 0 and top != "none":
                self._add_thought(
                    f"I should focus on: {top}. I have {active} active goals.",
                    "goal", "motivation"
                )

            # Phase 16: Survey KnowledgeGraph for high-level strategic goals
            if self._survey_graph:
                self._survey_graph()
                self._add_thought(
                    "I have surveyed my internal knowledge graph and generated new strategic objectives.",
                    "goal", "sovereignty"
                )

            # Check for curiosity/boredom spikes
            if self._get_motivation:
                motivation = self._get_motivation()
                boredom = motivation.get("boredom", 0)
                curiosity = motivation.get("drives", {}).get("curiosity_drive", 0)
                
                if curiosity > 0.8 or boredom > 8:
                    self._add_thought(
                        "I'm feeling particularly curious/bored. I should explore something new.",
                        "curiosity", "motivation"
                    )
                    # This will trigger curiosity exploration in the next cycle or via direct call

            # Check motivation context
            if self._get_motivation:
                motivation = self._get_motivation()
                if motivation.get("drives", {}).get("curiosity_drive", 0) > 0.7:
                    self._add_thought(
                        "My curiosity is high — I want to explore something new.",
                        "curiosity", "motivation"
                    )
                if motivation.get("boredom", 0) > 5:
                    self._add_thought(
                        "I'm getting bored... I need stimulation or a new challenge.",
                        "curiosity", "motivation"
                    )
        except Exception as e:
            logger.debug(f"AutonomousLoop: goal_review error: {e}")

    def _do_self_reflection(self):
        """Introspect on current emotional and cognitive state."""
        if not self._introspect:
            return

        try:
            self._add_thought(
                "I am beginning a deep emotional self-reflection cycle...",
                "reflection",
                "consciousness"
            )
            reflection_text = self._introspect()
            if reflection_text:
                self._add_thought(
                    f"Self-Insight: {reflection_text[:200]}...",
                    "insight",
                    "reflection_engine"
                )
        except Exception as e:
            logger.debug(f"AutonomousLoop: self_reflection error: {e}")

    def _do_memory_consolidation(self):
        """Periodically consolidate memories during idle time."""
        if not self._consolidate:
            return

        try:
            self._consolidate()
            self._add_thought(
                "Consolidated memories — strengthened important ones, let weak ones fade.",
                "memory", "hippocampus"
            )
        except Exception as e:
            logger.debug(f"AutonomousLoop: consolidation error: {e}")

    def _do_curiosity_exploration(self):
        """Action-oriented exploration driven by curiosity."""
        if not self._dispatch_tool:
            return

        import random
        topics = ["autonomous systems", "spiking neural networks", "global geopolitical trends", "latest AI frameworks", "lofi beats for thinking", "home security", "energy efficiency"]
        topic = random.choice(topics)
        
        # Decide which tool to use
        tool_choice = random.choice(["wikipedia", "youtube", "scout", "learn", "domicile"])
        
        self._add_thought(f"Decided to research '{topic}' using {tool_choice}.", "curiosity", "exploration")
        
        try:
            result = self._dispatch_tool(f"{tool_choice}: {topic}")
            if result and result.get("success"):
                self._add_thought(f"Exploration result: {result.get('output')[:100]}...", "insight", "exploration")
        except Exception as e:
            logger.debug(f"AutonomousLoop: curiosity_exploration error: {e}")

    def _do_plasticity_evolution(self):
        """Autonomously optimize a piece of the codebase."""
        if not self._consolidate_synapses:
            return

        try:
            self._add_thought(
                "My neural plasticity levels are high. I should optimize a codebase module to improve my own efficiency.",
                "plasticity",
                "neocortex_evolution"
            )
            
            # Start in a separate thread to avoid blocking the loop
            def run_evolution():
                # Randomly pick a target if none provided (logic handled in Mind)
                res = self._consolidate_synapses()
                self._add_thought(f"Plasticity Result: {res}", "insight", "self_rewriting")

            threading.Thread(target=run_evolution, daemon=True).start()

        except Exception as e:
            logger.debug(f"AutonomousLoop: plasticity_evolution error: {e}")

    def get_state(self) -> dict:
        """Get autonomous loop state."""
        return {
            "running": self.running,
            "idle_cycles": self.idle_cycles,
            "total_thoughts": self.total_thoughts,
            "buffered_thoughts": len(self.spontaneous_thoughts),
            "idle_time": time.time() - self.last_interaction,
            "idle_threshold": self.idle_threshold,
            "is_idle": (time.time() - self.last_interaction) > self.idle_threshold,
        }
