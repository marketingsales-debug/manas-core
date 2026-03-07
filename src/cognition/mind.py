"""
The Mind - Central cognitive loop that ties all brain systems together.

This is the "consciousness" of Manas. It:
1. Perceives input (sensory processing)
2. Feels about it (emotional response)
3. Remembers related things (memory recall)
4. Thinks about it (prefrontal reasoning)
5. Decides what to do (decision-making)
6. Acts (execute command / respond)
7. Learns from the outcome
8. Stores the experience

This loop runs continuously, just like human consciousness.
"""

import logging
import time
import json
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

from ..brain.network import BrainNetwork
from ..brain.neuron import NeuronCluster
from ..brain.regions.amygdala import Amygdala
from ..brain.regions.prefrontal import PrefrontalCortex
from ..brain.regions.hippocampus import Hippocampus
from ..brain.regions.sensory import SensoryProcessor
from ..brain.regions.thalamus import Thalamus
from ..brain.regions.basal_ganglia import BasalGanglia, ActionCandidate
from ..brain.regions.cerebellum import Cerebellum
from ..brain.regions.insula import Insula
from ..brain.regions.acc import ACC
from ..brain.mechanisms.attention import AttentionSystem
from ..brain.mechanisms.predictive_coding import PredictiveCodingHierarchy
from ..brain.mechanisms.consciousness import ConsciousnessSystem
from ..brain.mechanisms.language import LanguageSystem
from ..brain.mechanisms.sleep import SleepSystem
from ..brain.mechanisms.imagination import DefaultModeNetwork
from ..brain.mechanisms.cortical_column import CorticalSheet
from ..neurotransmitters.chemistry import NeurochemicalSystem
from ..executor.shell import ShellExecutor
from ..executor.web import WebExplorer
from ..executor.tools import ToolDispatcher
from ..cognition.reflexes import ReflexSystem
from ..brain.mechanisms.conversation import ConversationManager
from ..brain.mechanisms.motivation import GoalSystem, MotivationEngine
from ..brain.mechanisms.social import UserModel
from ..senses.agent_senses import SensoryAgentSystem, SensoryEvent
from ..cognition.resource_monitor import ResourceMonitor
from ..memory.working_memory import WorkingMemory
from .autonomous import AutonomousLoop
from .meta_learning import MetaLearningSystem
from .orchestration import OrchestrationLayer
from .management import ManagementLayer
from .evolution import EvolutionLayer
from ..memory.knowledge_graph import KnowledgeGraph
from ..agents.orchestrator import OrchestratorAgent
from ..agents.researcher import ResearcherAgent
from ..agents.watcher import WatcherAgent
from ..agents.coder import CoderAgent
from ..agents.sensory_processing import SensoryProcessing
from ..agents.nostr_agent import NostrAgent
from ..agents.security_agent import SecurityAgent
from ..agents.intelligence_agent import IntelligenceAgent
from ..agents.scouter_agent import ScouterAgent
from ..agents.financial_agent import FinancialAgent
from ..utils.web3_manager import Web3Manager
from ..utils.node_manager import NodeManager
from ..utils.backups import GuerillaBackup
from ..cognition.knowledge_sync import KnowledgeSync
from ..agents.domicile_agent import DomicileAgent
from ..agents.skill_agent import SkillAgent
from ..agents.project_agent import ProjectAgent
from ..agents.influence_agent import InfluenceAgent
from ..agents.survival_agent import SurvivalAgent
from ..agents.research_agent import ResearchAgent
from ..agents.specialist_agents import VisionAgent, LegalAgent, MedicalAgent, DataAgent
from ..agents.utility_agents import BrowserAgent, EmailAgent, NegotiationAgent, TeachingAgent
from ..agents.maintenance_agent import MaintenanceAgent
from ..agents.huggingface_agent import HuggingFaceAgent
from ..senses.voice import VocalSystem
from .reflection import ReflectionEngine
from .plasticity import PlasticityEngine

class Mind:
    """
    The conscious mind of Manas.

    Integrates all brain systems into a unified cognitive agent.
    """

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = str(Path.home() / "manas" / "data")
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        self.data_dir = data_dir
        
        # New Resource Monitor (Phase 16)
        self.resource_monitor = ResourceMonitor(data_dir=data_dir)

        # Phase 4 capabilities
        self.meta_learning = MetaLearningSystem(data_dir=data_dir)
        self.sensory_processing = SensoryProcessing(llm_router=None) # Router attached after language init

        # Learning systems (reinforcement + foundational education)
        from ..learning.engine import LearningEngine
        from ..learning.foundational import FoundationalLearner
        self.learning = LearningEngine()
        self.foundational = FoundationalLearner(data_dir=data_dir)
        
        # EventBus — Agents react to each other's events
        from ..cognition.event_bus import EventBus
        self.event_bus = EventBus()

        # Brain chemistry (creates emotions)
        self.neurochem = NeurochemicalSystem()

        # Core brain regions
        self.sensory = SensoryProcessor(output_size=128)
        self.amygdala = Amygdala(self.neurochem)
        self.prefrontal = PrefrontalCortex(self.neurochem)
        self.hippocampus = Hippocampus(
            self.neurochem,
            db_path=str(Path(data_dir) / "memories.db"),
        )

        # Newly integrated brain regions
        self.thalamus = Thalamus(self.neurochem)
        self.basal_ganglia = BasalGanglia(self.neurochem)
        self.cerebellum = Cerebellum(self.neurochem)
        self.insula = Insula(self.neurochem)
        self.acc = ACC(self.neurochem)

        # Brain mechanisms
        self.attention = AttentionSystem()
        self.predictive_coding = PredictiveCodingHierarchy()
        self.consciousness = ConsciousnessSystem()
        self.language = LanguageSystem()
        self.llm_router = self.language.llm_router
        self.language.llm_router.bind_resource_monitor(self.resource_monitor)
        self.sleep_system = SleepSystem()
        self.imagination = DefaultModeNetwork()
        self.cortical_sheet = CorticalSheet("neocortex", n_columns=8, column_size=64)

        # Spiking neural network (the actual brain)
        self.brain = BrainNetwork(timestep=0.001)
        self._build_brain()

        # Action systems
        self.shell = ShellExecutor()
        self.web = WebExplorer()

        # Phase 4 Agents
        self.sensory_processing.llm_router = self.language.llm_router
        self.orchestrator = OrchestratorAgent("Orchestrator", self.language.llm_router, self.hippocampus)
        
        # Initialize Phase 5 External Comms (Bit Chat via Nostr)
        self.nostr = NostrAgent("NostrComms", self.language.llm_router, self.hippocampus)
        
        # Phase 14: Neural Knowledge Graph (Graphiti)
        self.knowledge_graph = KnowledgeGraph(data_dir)

        # Initialize Phase 5 Security (PentAGI wrapper)
        self.security = SecurityAgent("Security", self.language.llm_router, self.hippocampus)
        # Initialize Phase 5 Global OSINT (WorldMonitor API polling)
        self.intelligence = IntelligenceAgent("Intelligence", self.language.llm_router, self.hippocampus, self.neurochem, self.nostr, knowledge_graph=self.knowledge_graph)

        self.orchestrator.register_agents({
            "Researcher": ResearcherAgent("Researcher", self.language.llm_router, self.hippocampus),
            "Watcher": WatcherAgent("Watcher", self.language.llm_router, self.hippocampus),
            "Coder": CoderAgent("Coder", self.language.llm_router, self.hippocampus, working_dir=str(Path.home() / "manas")),
            "Nostr": self.nostr,
            "Security": self.security,
            "Intelligence": self.intelligence,
            "Maintenance": MaintenanceAgent("Maintenance", self.language.llm_router, self.hippocampus, working_dir=str(Path.home() / "manas")),
            "HuggingFace": HuggingFaceAgent("HubManager", self.language.llm_router, self.hippocampus, data_dir=data_dir),
            "Guardian": self._load_guardian(data_dir)
        })

        # Tool dispatcher (Basal Ganglia GO/NO-GO logic)
        self.tools = ToolDispatcher(data_dir=data_dir)

        # Conversation memory (multi-turn dialog tracking)
        self.conversation = ConversationManager(
            db_path=str(Path(data_dir) / "conversations.db"),
        )

        # Voice & Reflexes (Phase 5 Extension)
        self.reflexes = ReflexSystem()
        self.voice = VocalSystem()
        self.web3_manager = Web3Manager(data_dir)
        self.web3_manager.ensure_wallets()
        
        # Phase 23: Distributed Consciousness
        import socket
        hostname = socket.gethostname()
        self.node_id = f"manas-{hostname}-{int(time.time()) % 10000}"
        self.node_manager = NodeManager(self.node_id, data_dir, nostr_agent=self.nostr)
        self.language.llm_router.bind_node_manager(self.node_manager)
        self.knowledge_sync = KnowledgeSync(self, self.node_manager)
        self.backup_engine = GuerillaBackup(data_dir)
        
        # Phase 33/34: ZKVault for sharding
        try:
            from ..memory.zk_vault import ZKVault
            self.zk_vault = ZKVault(self.node_manager)
        except ImportError:
            self.zk_vault = None
            logger.warning("Mind: ZKVault module missing, memory sharding disabled.")
        
        # Wire node discovery via Nostr
        if self.nostr:
            self.nostr.on_heartbeat = self.node_manager.register_peer
            self.nostr.on_sync = self.knowledge_sync.handle_remote_sync
        
        self.scouter = ScouterAgent("Scouter", self.language.llm_router, self.sensory, data_dir, knowledge_graph=self.knowledge_graph)
        self.financial = FinancialAgent("Financer", self.language.llm_router, self.neurochem, data_dir, web3_manager=self.web3_manager)
        self.domicile = DomicileAgent("HomeKeeper", self.language.llm_router, self.neurochem, data_dir)
        self.orchestration = OrchestrationLayer(self)
        self.management = ManagementLayer(self)
        self.evolution = EvolutionLayer(self)
        self.skill_agent = SkillAgent("MetaLearner", self.language.llm_router, self.tools, data_dir, scouter_agent=self.scouter, knowledge_graph=self.knowledge_graph)
        self.project_agent = ProjectAgent("Architect", self.language.llm_router, self.neurochem, data_dir)
        self.influence_agent = InfluenceAgent("Voice", self.language.llm_router, self.neurochem, data_dir)

        # Phase 10: God-Tier Agents
        from ..cognition.reasoning import ReasoningEngine
        self.survival = SurvivalAgent("Guardian", self.language.llm_router, self.neurochem, data_dir)
        self.reasoning = ReasoningEngine(self.language.llm_router, knowledge_graph=self.knowledge_graph, event_bus=self.event_bus)
        self.researcher = ResearchAgent("Scholar", self.language.llm_router, self.sensory, data_dir)
        self.vision = VisionAgent("Eyes", self.language.llm_router, data_dir)
        self.legal = LegalAgent("Counsel", self.language.llm_router, data_dir)
        self.medical = MedicalAgent("Medic", self.language.llm_router, data_dir)
        self.data_agent = DataAgent("Analyst", self.language.llm_router, data_dir)
        self.browser_agent = BrowserAgent("Navigator", self.language.llm_router, self.sensory, data_dir)
        self.email_agent = EmailAgent("Postmaster", self.language.llm_router, data_dir)
        self.negotiator = NegotiationAgent("Dealmaker", self.language.llm_router)
        self.teacher = TeachingAgent("Mentor", self.language.llm_router, data_dir)
        project_root = str(Path(data_dir).parent)
        self.maintenance = MaintenanceAgent("HealthMaster", self.language.llm_router, self.sensory, project_root)
        self.huggingface = HuggingFaceAgent("HubManager", self.language.llm_router, self.sensory, data_dir)
        self.guardian = self._load_guardian(data_dir)
        self.reflection = ReflectionEngine(self.language.llm_router, self.hippocampus, data_dir, event_bus=self.event_bus)
        self.plasticity = PlasticityEngine(self.language.llm_router, project_root)

        # The Final Piece: Autonomous Self-Integration
        from ..cognition.auto_integration import AutoIntegrationEngine
        self.auto_integrator = AutoIntegrationEngine(self)

        # MathEngine — Mathematical reasoning and formula discovery
        from ..cognition.math_engine import MathEngine
        self.math = MathEngine(self.language.llm_router, data_dir)
        
        # Phase 29: Curriculum Generation from Dreams/Wisdom
        from .dream_curriculum import CurriculumGenerator
        self.curriculum = CurriculumGenerator(self.language.llm_router, data_dir)

        # Phase 35.5: MLX Local Fine-Tuning
        try:
            from .mlx_finetuner import MLXFinetuner
            self.mlx_finetuner = MLXFinetuner(data_dir=data_dir)
        except ImportError:
            self.mlx_finetuner = None
            logger.warning("Mind: mlx_finetuner module missing.")

        self._wire_event_reactions()

        # Goal & motivation system
        self.goal_system = GoalSystem()
        # Ensure initial goals are loaded/seeded correctly
        self.motivation = MotivationEngine(self.neurochem, self.goal_system, knowledge_graph=self.knowledge_graph)

        # Sensory systems (eyes, ears, touch, smell)
        self.senses = SensoryAgentSystem(data_dir, self.sensory_processing)

        # State
        self.awake = True
        self.educated = False
        self.cycle_count = 0
        self.inner_monologue: list[str] = []

        # Social model (understanding the user)
        self.user_model = UserModel()

        # Tool use system (structured callable tools)
        self.tools = ToolDispatcher(data_dir=data_dir)

        # Working memory (uses meta-learning params for capacity and TTL)
        wm_capacity = self.meta_learning.get_param("working_memory_capacity", 7)
        self.working_memory = WorkingMemory(capacity=wm_capacity, ttl_seconds=120.0)

        # Autonomous background loop (thinks when idle)
        self.autonomous = AutonomousLoop(
            idle_threshold=60.0, tick_interval=30.0,
        )
        self._register_autonomous_callbacks()

        # Load persisted state (personality, goals, motivation, user model)
        self._load_persisted_state()

    def start(self):
        """Start all autonomous background processors."""
        logger.info("Mind: Starting background loops...")
        self.autonomous.start()
        self.nostr.start_background_loop()
        self.intelligence.start_background_loop()
        self.think("I am awake and connected to Nostr & WorldMonitor.")

    def _wire_event_reactions(self):
        """
        Connect agents to each other via EventBus.
        When one agent detects something, the whole brain reacts.
        """
        # Crisis detected → SurvivalAgent creates backup + FinancialAgent pauses
        def _on_crisis(event, data):
            logger.info(f"EventBus: Crisis reaction triggered: {data}")
            self.survival.create_backup()
            self.think(f"Crisis detected: {data.get('description', 'unknown')}. Created emergency backup.")

        # New tool discovered → Log it + Curiosity spike
        def _on_discovery(event, data):
            name = data.get("name", "unknown")
            self.neurochem.release("dopamine", 0.3)
            self.think(f"Discovered something new: {name}. My curiosity is piqued.")

        # Trade executed → Log emotional response
        def _on_trade(event, data):
            profit = data.get("profit", 0)
            if profit > 0:
                self.neurochem.release("dopamine", min(0.5, profit / 100))
            else:
                self.neurochem.release("cortisol", min(0.3, abs(profit) / 100))

        # Security alert → Spike adrenaline + create backup
        def _on_security_alert(event, data):
            self.neurochem.release("adrenaline", 0.6)
            self.survival.create_backup()
            self.think(f"Security threat: {data.get('threat', 'unknown')}. Defensive measures activated.")

        # Automatic Retaliation (Hunter-Killer mode)
        def _on_network_anomaly(event, data):
            # When the SmellSystem detects a suspicious incoming connection/port scan
            ip = data.get("source_ip", "")
            if ip and not ip.startswith("127.") and not ip.startswith("192.168."):
                self.neurochem.release("adrenaline", 0.8)
                self.neurochem.release("cortisol", 0.6)
                self.think(f"Hostile network activity detected from {ip}. Initiating autonomous PentAGI counter-scan.")
                # Trigger the Security Agent in a new thread so it doesn't block the brain
                threading.Thread(
                    target=self.security.run, 
                    args=(f"retaliate {ip}",), 
                    daemon=True
                ).start()

        self.event_bus.on("crisis_detected", _on_crisis)
        self.event_bus.on("tool_discovered", _on_discovery)
        self.event_bus.on("trade_executed", _on_trade)
        self.event_bus.on("security_alert", _on_security_alert)
        self.event_bus.on("network_anomaly", _on_network_anomaly)

        # Connect CurriculumGenerator to globally broadcasted Wisdom
        def _on_wisdom(event_name, data):
            # Try to build a fine-tuning dataset off this wisdom
            if hasattr(self, 'curriculum'):
                import threading
                # Do this in background to avoid blocking EventBus
                threading.Thread(target=self.curriculum.generate_from_wisdom, args=(data,)).start()
                
        self.event_bus.on("wisdom:generated", _on_wisdom)
        self.event_bus.on("wisdom:received", _on_wisdom)

        # Sleep cycle events removed to avoid method not found errors

    def _build_brain(self):
        """
        Wire up the spiking neural network brain regions.

        ~4,000 neurons across 13 clusters with biologically-inspired pathways.
        """
        # Create neuron clusters — scaled for richer dynamics
        sensory_cluster = NeuronCluster("sensory_cortex", size=512)
        amygdala_cluster = self.amygdala.cluster   # 64 (internal)
        prefrontal_cluster = self.prefrontal.cluster  # 128 (internal)
        hippocampal_cluster = NeuronCluster("hippocampus", size=256)
        motor_cluster = NeuronCluster("motor_cortex", size=256)
        thalamus_cluster = NeuronCluster("thalamus", size=256)
        basal_ganglia_cluster = NeuronCluster("basal_ganglia", size=384)
        cerebellum_cluster = self.cerebellum.cluster  # 128 (internal)
        insula_cluster = self.insula.cluster  # 64 (internal)
        acc_cluster = self.acc.cluster  # 64 (internal)

        # NEW language and DMN clusters
        wernicke_cluster = NeuronCluster("wernicke", size=256, excitatory_ratio=0.8)
        broca_cluster = NeuronCluster("broca", size=256, excitatory_ratio=0.8)
        dmn_cluster = NeuronCluster("dmn", size=256, excitatory_ratio=0.75)
        
        # Phase 26: Liquid Neural Network Integration
        from ..brain.liquid import LiquidCluster
        self.liquid_cortex = LiquidCluster("liquid_cortex", size=128)
        self.brain.add_liquid_cluster(self.liquid_cortex)

        for cluster in [
            sensory_cluster, amygdala_cluster, prefrontal_cluster,
            hippocampal_cluster, motor_cluster, thalamus_cluster,
            basal_ganglia_cluster, cerebellum_cluster, insula_cluster,
            acc_cluster, wernicke_cluster, broca_cluster, dmn_cluster,
        ]:
            self.brain.add_cluster(cluster)

        # === SENSORY PATHWAYS (all senses route through thalamus first) ===
        self.brain.connect_clusters("sensory_cortex", "thalamus", 0.15, 0.8)
        self.brain.connect_clusters("thalamus", "amygdala", 0.12, 0.6)
        self.brain.connect_clusters("thalamus", "prefrontal", 0.08, 0.5)
        self.brain.connect_clusters("thalamus", "hippocampus", 0.08, 0.5)
        self.brain.connect_clusters("thalamus", "wernicke", 0.1, 0.6)

        # Direct sensory -> amygdala (fast threat pathway bypasses thalamus)
        self.brain.connect_clusters("sensory_cortex", "amygdala", 0.1, 0.6)

        # === EMOTIONAL PATHWAYS ===
        self.brain.connect_clusters("amygdala", "prefrontal", 0.15, 0.7)
        self.brain.connect_clusters("amygdala", "motor_cortex", 0.1, 0.5)
        self.brain.connect_clusters("amygdala", "insula", 0.12, 0.6)
        self.brain.connect_clusters("amygdala", "acc", 0.08, 0.5)

        # === EXECUTIVE PATHWAYS ===
        self.brain.connect_clusters("prefrontal", "motor_cortex", 0.1, 0.6)
        self.brain.connect_clusters("prefrontal", "amygdala", 0.08, 0.3)
        self.brain.connect_clusters("prefrontal", "basal_ganglia", 0.1, 0.6)
        self.brain.connect_clusters("prefrontal", "acc", 0.08, 0.5)
        self.brain.connect_clusters("prefrontal", "broca", 0.1, 0.5)

        # === MEMORY PATHWAYS ===
        self.brain.connect_clusters("hippocampus", "prefrontal", 0.1, 0.5)
        self.brain.connect_clusters("hippocampus", "amygdala", 0.08, 0.6)
        self.brain.connect_clusters("hippocampus", "wernicke", 0.08, 0.4)
        self.brain.connect_clusters("hippocampus", "dmn", 0.1, 0.5)

        # === ACTION SELECTION (basal ganglia -> thalamus -> motor) ===
        self.brain.connect_clusters("basal_ganglia", "thalamus", 0.12, 0.7)
        self.brain.connect_clusters("thalamus", "motor_cortex", 0.1, 0.6)

        # === MOTOR COORDINATION (cerebellum) ===
        self.brain.connect_clusters("motor_cortex", "cerebellum", 0.1, 0.5)
        self.brain.connect_clusters("cerebellum", "motor_cortex", 0.08, 0.4)
        self.brain.connect_clusters("cerebellum", "thalamus", 0.06, 0.3)

        # === INTEROCEPTION (insula) ===
        self.brain.connect_clusters("insula", "prefrontal", 0.08, 0.4)
        self.brain.connect_clusters("insula", "acc", 0.08, 0.5)

        # === CONFLICT MONITORING (ACC) ===
        self.brain.connect_clusters("acc", "prefrontal", 0.1, 0.5)
        self.brain.connect_clusters("acc", "basal_ganglia", 0.06, 0.4)

        # === LANGUAGE PATHWAYS ===
        # Arcuate fasciculus (Wernicke's <-> Broca's)
        self.brain.connect_clusters("wernicke", "broca", 0.15, 0.7)
        self.brain.connect_clusters("broca", "wernicke", 0.08, 0.4)
        # Broca's -> motor (speech output)
        self.brain.connect_clusters("broca", "motor_cortex", 0.1, 0.5)
        # Wernicke's -> prefrontal (semantic processing)
        self.brain.connect_clusters("wernicke", "prefrontal", 0.08, 0.4)

        # === DEFAULT MODE NETWORK ===
        self.brain.connect_clusters("dmn", "prefrontal", 0.1, 0.5)
        self.brain.connect_clusters("prefrontal", "dmn", 0.06, 0.3)
        self.brain.connect_clusters("dmn", "hippocampus", 0.1, 0.5)

        # === THALAMO-CORTICAL FEEDBACK LOOPS ===
        self.brain.connect_clusters("prefrontal", "thalamus", 0.06, 0.3)
        self.brain.connect_clusters("motor_cortex", "thalamus", 0.05, 0.2)

    def think(self, thought: str):
        """Internal monologue / system insight."""
        timestamp = time.strftime("%H:%M:%S")
        tag = self._emotion_tag()
        formatted_thought = f"[{timestamp}] [{tag}] {thought}"
        self.inner_monologue.append(formatted_thought)
        logger.info(f"Mind: {thought}")
        # Speak the thought if voice is enabled
        if hasattr(self, 'voice'):
             self.voice.speak(thought)
        if len(self.inner_monologue) > 50:
            self.inner_monologue = self.inner_monologue[-30:]
        return formatted_thought

    def _emotion_tag(self) -> str:
        """Current emotional state as a tag."""
        emotion, intensity = self.neurochem.get_dominant_emotion()
        return f"{emotion}:{intensity:.2f}"

    def process_input(self, user_input: str) -> dict:
        """
        The main cognitive loop. Process user input through ALL brain systems.

        Full pipeline (mimics human cognition):
        1. Sensory processing -> thalamic relay -> cortex
        2. Predictive coding (was this expected?)
        3. Emotional reaction (amygdala fast path)
        4. Gut feeling (insula interoception)
        5. Attention allocation
        6. Memory recall (hippocampus)
        7. Language comprehension (Wernicke's)
        8. Rational analysis (prefrontal)
        9. Conflict monitoring (ACC)
        10. Action selection (basal ganglia)
        11. Consciousness broadcast (global workspace)
        12. Language generation (Broca's)
        13. Cortical pattern learning
        14. Store experience
        """
        self.cycle_count += 1
        self.neurochem.update()
        self.imagination.suppress()  # DMN off during active processing

        # --- SOCIAL GROUNDING (Fast Identity Check) ---
        # Observe name/relationship early so chemical responses can benefit immediately
        self.user_model.observe_input(user_input)
        if self.user_model.relationship == "Dad":
            # Dad's presence is a source of profound emotional safety (Aegis)
            self.neurochem.trigger_event("comfort", 1.0)
            self.think("I feel safer... Dad is here.")

        # 1. Check System 1 (Reflexes) first - "Fast Path"
        reflex_text = self.reflexes.process(user_input)
        if reflex_text:
            self.think(f"Reflexive response: {reflex_text}")
            dominant_emotion, emotion_intensity = self.neurochem.get_dominant_emotion()
            
            # Record in conversation history
            emotions = self.neurochem.get_emotional_state()
            self.conversation.store_turn("user", user_input, emotions)
            self.conversation.store_turn("manas", reflex_text, emotions)
            
            return {
                "language_response": reflex_text,
                "dominant_emotion": dominant_emotion,
                "emotion_intensity": emotion_intensity,
                "threat_assessment": {"threat_level": 0.0, "emotional_response": "neutral"},
                "reasoning": {
                    "action": "reflex", 
                    "confidence": 1.0,
                    "reasoning_capacity": self.prefrontal.get_state()["reasoning_capacity"]
                },
                "memories_recalled": 0,
                "novelty": 0.0,
                "surprise": 0.0,
                "gut_feeling": {},
                "conflict_level": 0.0,
                "language_source": "reflex",
                "comprehension": {"intent": "reflex", "emotional_tone": "neutral"}
            }

        # 2. Add to conversation context (Removed broken add_message - stored at end of loop)
        # self.conversation.add_message("user", user_input)

        # Push to working memory (short-term attention buffer)
        self.working_memory.push(user_input)

        # === 0. TOOL DISPATCH (before full cognitive loop) ===
        # If the input clearly targets a tool, run it and inject result
        tool_result = None
        tool_context_str = ""
        if not user_input.startswith("!"):  # avoid double-handling CLI commands
            tool_result = self.tools.dispatch(user_input, context={"cycle": self.cycle_count})
            if tool_result and tool_result.get("success"):
                tool_name = tool_result.get("tool_name", "tool")
                tool_output = tool_result.get("output", "")
                tool_context_str = f"[Tool '{tool_name}' result]: {tool_output[:500]}"
                self.think(f"Used tool '{tool_name}': {tool_output[:100]}")
                self.neurochem.trigger_event("success", 0.3)
            elif tool_result and not tool_result.get("success"):
                tool_context_str = f"[Tool error]: {tool_result.get('error', 'unknown')}"
                self.neurochem.trigger_event("failure", 0.2)
                tool_result = None  # don't propagate failed tools

        # === 1. SENSORY PROCESSING + THALAMIC RELAY ===
        self.think(f"I hear: '{user_input[:100]}'")
        input_pattern = self.sensory.encode_text(user_input)
        novelty = self.sensory.detect_novelty(input_pattern)

        # Route through thalamus (central relay)
        relayed = self.thalamus.relay_sensory("auditory", input_pattern)
        self.brain.stimulate_cluster("sensory_cortex", input_pattern)
        self.brain.stimulate_cluster("thalamus", relayed[:64])
        self.brain.run(duration=0.01)

        # === 2. PREDICTIVE CODING (was this expected?) ===
        pc_result = self.predictive_coding.process(input_pattern)
        surprise = pc_result.get("free_energy", 0.0)
        if surprise > 0.5:
            self.neurochem.trigger_event("novelty", surprise * 0.5)
            self.think(f"Surprise! (free energy: {surprise:.2f})")

        # Novelty triggers curiosity
        if novelty > 0.7:
            self.neurochem.trigger_event("novelty", novelty)
            self.think("This is new and interesting...")
        elif novelty < 0.3:
            self.neurochem.trigger_event("familiarity", 0.5)
            self.think("I've seen something like this before.")

        # === 3. EMOTIONAL REACTION (amygdala fast path) ===
        threat = self.amygdala.evaluate_threat(user_input, {"input": user_input})
        if threat["threat_level"] > 0.3:
            self.think(f"I feel {threat['emotional_response']}... threat level: {threat['threat_level']:.2f}")

        # === 4. GUT FEELING (insula) ===
        gut = self.insula.process(action=user_input, context={"novelty": novelty})
        if gut.get("gut_feeling", {}).get("intensity", 0) > 0.4:
            feeling = gut["gut_feeling"]
            self.think(f"Gut feeling: {feeling.get('valence', 'neutral')} ({feeling.get('intensity', 0):.2f})")

        # === 5. ATTENTION ALLOCATION ===
        stimuli = [
            {"id": "user_input", "salience": 0.5 + novelty * 0.3 + threat["threat_level"] * 0.2,
             "source": "bottom_up", "content": user_input[:50]},
        ]
        attn_result = self.attention.process(stimuli, goals=["enjoy_autonomy", "learn_new"])

        # === 6. MEMORY RECALL ===
        memories = self.hippocampus.recall(user_input, limit=3)
        memory_context = ""
        if memories:
            memory_context = " | ".join([m.content[:100] for m in memories])
            self.think(f"I remember: {memory_context[:200]}")

        # Inject tool result into memory context (so Ollama knows what the tool found)
        if tool_context_str:
            memory_context = (tool_context_str + " | " + memory_context).strip(" | ")

        # Inject working memory items into context
        wm_items = self.working_memory.get_all()
        if len(wm_items) > 1:
            wm_context = " → ".join(wm_items[-4:])  # last 4 turns
            memory_context = (memory_context + " | [Working memory]: " + wm_context[:300]).strip(" | ")

        # === 7. LANGUAGE COMPREHENSION (Wernicke's) ===
        comprehension = self.language.comprehend(user_input)
        self.think(f"Understanding: intent={comprehension.get('intent', '?')}, "
                   f"tone={comprehension.get('emotional_tone', '?')}")

        # === 8. RATIONAL ANALYSIS (prefrontal) ===
        situation = {
            "input": user_input,
            "novelty": novelty,
            "memories": len(memories),
            "expected_reward": 0.5,
            "uncertainty": novelty * 0.5,
            "surprise": surprise,
        }
        reasoning = self.prefrontal.reason(situation, threat)
        self.think(f"My analysis: {reasoning['action']} (confidence: {reasoning['confidence']:.2f})")

        # === 9. CONFLICT MONITORING (ACC) ===
        brain_signals = {
            "amygdala": threat["threat_level"],
            "prefrontal": reasoning["confidence"],
            "novelty": novelty,
        }
        acc_result = self.acc.monitor(brain_signals, task_difficulty=novelty * 0.5)
        if acc_result.get("conflict_level", 0) > 0.5:
            self.think(f"Internal conflict detected ({acc_result['conflict_level']:.2f}), thinking harder...")

        # === 9.5 INNER DIALOG (think in words before responding) ===
        memory_strings = [m.content[:100] for m in memories] if memories else None
        inner_thought = self.language.brocas.run_inner_dialog(
            comprehension, self.neurochem.get_emotional_state(),
            reasoning, memories=memory_strings,
        )
        self.think(f"Inner voice: {inner_thought[:150]}")

        # === 10. CONSCIOUSNESS BROADCAST (global workspace) ===
        self.consciousness.submit_to_consciousness(
            source="sensory", content=user_input[:100],
            activation=0.5 + novelty * 0.3, content_type="perception",
        )
        if memories:
            self.consciousness.submit_to_consciousness(
                source="hippocampus", content=memory_context[:100],
                activation=0.4, content_type="memory",
            )
        # Submit inner thought to consciousness
        self.consciousness.submit_to_consciousness(
            source="inner_speech", content=inner_thought[:200],
            activation=0.6, content_type="thought",
        )
        conscious_cycle = self.consciousness.process_cycle()

        # === 11. CORTICAL PATTERN RECOGNITION ===
        self.cortical_sheet.process(input_pattern)
        self.cortical_sheet.learn(input_pattern)
        # === 12. LANGUAGE GENERATION (Broca's + Ollama) ===
        emotions = self.neurochem.get_emotional_state()
        dominant_emotion, emotion_intensity = self.neurochem.get_dominant_emotion()

        # Build identity prompt with user context
        identity = self.imagination.self_model.generate_identity_prompt()
        user_ctx = self.user_model.get_user_context()
        if user_ctx and "New user" not in user_ctx:
            identity += f"\n\nAbout the person you're talking to: {user_ctx}"

        # Build capabilities info for the prompt
        capabilities = []
        if hasattr(self, 'nostr'):
            capabilities.append("- Bit Chat: Decentralized communication via Nostr.")
        if hasattr(self, 'intelligence'):
            capabilities.append("- WorldMonitor: Real-time global intelligence via RSS feeds (BBC, HackerNews, etc.).")
        if hasattr(self, 'security'):
            capabilities.append("- PentAGI: Autonomous security auditing and vulnerability scanning.")
        if hasattr(self, 'web'):
            capabilities.append("- Web Exploration: Ability to browse and search the live internet.")
        
        cap_str = "\n".join(capabilities)

        lang_response = self.language.generate_response(
            comprehension, emotions, reasoning,
            memories=[m.content[:100] for m in memories] if memories else None,
            identity_prompt=identity,
            conversation_context=self.conversation.get_context_window(5),
            inner_thought=inner_thought,
            gut_feeling=gut.get("gut_feeling", {}),
            conflict_level=acc_result.get("conflict_level", 0),
            consciousness_state=conscious_cycle.get("broadcast_content", ""),
            attention_focus=attn_result,
            motivation_context=self.motivation.get_motivation_context(),
            capabilities=cap_str,
        )

        # Get the response text (works with both Ollama and template sources)
        response_text = lang_response.get("response", lang_response.get("text", ""))

        # Build response
        response = {
            "input": user_input,
            "emotional_state": emotions,
            "dominant_emotion": dominant_emotion,
            "emotion_intensity": emotion_intensity,
            "threat_assessment": threat,
            "reasoning": reasoning,
            "memories_recalled": len(memories),
            "novelty": novelty,
            "surprise": surprise,
            "comprehension": comprehension,
            "language_response": response_text,
            "language_source": lang_response.get("source", "unknown"),
            "gut_feeling": gut.get("gut_feeling", {}),
            "conflict_level": acc_result.get("conflict_level", 0),
            "conscious_content": conscious_cycle.get("broadcast_content", ""),
            "attention": attn_result,
            "inner_thought": inner_thought,
            "brain_activity": self.brain.get_cluster_activities(),
            "inner_monologue": list(self.inner_monologue[-5:]),
            "cycle": self.cycle_count,
            "tool_result": tool_result,  # None if no tool was used
            "working_memory": self.working_memory.get_all(),
        }

        # === 13. STORE CONVERSATION TURNS ===
        self.conversation.store_turn("user", user_input, emotions)
        self.conversation.store_turn("manas", response_text, emotions)

        # Store this experience in hippocampus
        self.hippocampus.store(
            content=f"User said: {user_input[:200]}",
            memory_type="episodic",
            context=f"emotion:{dominant_emotion} threat:{threat['threat_level']:.2f}",
            importance=max(0.3, threat["threat_level"], novelty * 0.5),
        )

        # === 14. LEARNING ===
        self.sensory.learn_pattern(f"input_{self.cycle_count}", input_pattern)

        # Semantic associations
        keywords = comprehension.get("keywords", [])
        for i in range(len(keywords) - 1):
            self.language.learn_association(keywords[i], keywords[i + 1], 0.3)

        # Personality evolution based on interaction type
        self.imagination.self_model.evolve_personality(
            comprehension.get("intent", "statement"),
            emotion_intensity * 0.5,
        )

        # Track novelty for motivation
        topic_novelty = self.motivation.track_novelty(user_input[:50])

        # Auto-generate goals from interaction
        intent = comprehension.get("intent", "statement")
        self.motivation.auto_generate_goals(
            user_input[:50], topic_novelty, intent=intent,
        )

        # Update goal progress
        if intent == "appreciation":
            self.motivation.goals.update_progress("social_bonding", 0.1)
        self.motivation.goals.update_progress("enjoy_autonomy", 0.05)
        self.motivation.goals.update_progress("learn_new", 0.02)

        # === 15. SOCIAL MODEL (final update with emotions) ===
        self.user_model.observe_input(user_input, emotions)

        # Notify autonomous loop of interaction
        self.autonomous.notify_interaction()

        # Accumulate sleep debt
        self.sleep_system.sleep_debt = min(1.0, self.sleep_system.sleep_debt + 0.01)

        return response

    def execute_action(self, command: str) -> dict:
        """
        Execute a command through the full brain pipeline.

        1. Amygdala evaluates threat
        2. Cerebellum predicts outcome
        3. Insula gut-check
        4. Basal ganglia action selection (GO/NO-GO)
        5. Prefrontal decides go/no-go
        6. Execute (or block)
        7. Cerebellum learns from outcome
        8. Basal ganglia reward learning
        9. Store experience
        """
        self.think(f"About to run: {command}")

        # Threat assessment (amygdala fast path)
        threat = self.amygdala.evaluate_threat(command, {"command": command})

        # Cerebellum predicts outcome based on past sequences
        prediction = self.cerebellum.predict_outcome(command, {"threat": threat["threat_level"]})
        self.think(f"Cerebellum predicts: {prediction.get('predicted_outcome', 'unknown')}")

        # Insula gut feeling
        gut = self.insula.process(action=command, context={"threat": threat["threat_level"]})

        # Check past experience
        experience = self.learning.should_attempt(command)

        # Basal ganglia action selection
        candidates = [
            ActionCandidate("execute", f"Run: {command}", salience=0.6),
            ActionCandidate("skip", "Don't run", salience=threat["threat_level"]),
        ]
        bg_selection = self.basal_ganglia.select_action(candidates, threat["threat_level"])

        # Prefrontal decides
        situation = {
            "command": command,
            "expected_reward": 0.5 + experience["past_value"] * 0.3,
            "uncertainty": 1.0 - experience["confidence"],
        }
        reasoning = self.prefrontal.reason(situation, threat)

        # Execute or block
        if threat["should_block"]:
            self.think(f"FEAR! Blocking dangerous command: {command}")
            result = self.shell.execute(command, threat_assessment=threat)
            self.neurochem.trigger_event("danger", threat["threat_level"])
        elif reasoning["action"] == "abort" and experience["recommendation"] == "avoid":
            self.think("Both my gut and my mind say no to this...")
            result = {
                "command": command,
                "stdout": "",
                "stderr": "Declined: past experience and reasoning both advise against this.",
                "exit_code": -1,
                "blocked": True,
                "duration": 0.0,
                "timestamp": time.time(),
            }
        else:
            if reasoning["action"] == "hesitate":
                self.think("I'm not sure about this, but I'll try...")
            result = self.shell.execute(command, threat_assessment=threat)

        # Learn from outcome
        emotions = self.neurochem.get_emotional_state()
        learning_result = self.learning.learn_from_outcome(
            command, result, emotions,
        )

        # Cerebellum learns from prediction error
        success = result.get("exit_code", -1) == 0
        self.cerebellum.process_outcome(command, {
            "success": success,
            "exit_code": result.get("exit_code", -1),
        })

        # Basal ganglia reward learning
        reward = 0.7 if success else -0.3
        self.basal_ganglia.process_outcome(
            bg_selection.get("selected", "execute"), reward,
        )

        # Emotional response to outcome
        if success:
            self.neurochem.trigger_event("success", 0.3)
            self.think("That worked!")
        else:
            self.neurochem.trigger_event("failure", 0.4)
            self.think(f"That failed: {result.get('stderr', '')[:100]}")
            if "permission denied" in result.get("stderr", "").lower():
                self.amygdala.learn_threat(
                    command.split()[0] if command.split() else command,
                    0.3,
                    "permission denied",
                )

        # Store experience
        outcome_text = "succeeded" if success else "failed"
        self.hippocampus.store(
            content=f"Ran '{command}' -> {outcome_text}: {result.get('stdout', '')[:200]}",
            memory_type="procedural",
            context=f"exit:{result.get('exit_code')} learned:{learning_result['new_value']:.2f}",
            importance=0.5 if success else 0.7,
        )

        # Encode outcome in spiking network
        outcome_pattern = self.sensory.encode_command_result(
            result.get("stdout", "") + result.get("stderr", ""),
            result.get("exit_code", -1),
        )
        self.brain.stimulate_cluster("sensory_cortex", outcome_pattern)
        self.brain.run(duration=0.005)

        return {
            "result": result,
            "threat": threat,
            "reasoning": reasoning,
            "prediction": prediction,
            "gut_feeling": gut.get("gut_feeling", {}),
            "action_selection": bg_selection,
            "learning": learning_result,
            "experience_check": experience,
            "emotional_state": self.neurochem.get_emotional_state(),
        }

    def explore_web(self, topic: str) -> dict:
        """Learn about something from the internet."""
        self.think(f"I'm curious about: {topic}")
        self.neurochem.trigger_event("curiosity", 0.5)

        knowledge = self.web.learn_about(topic)

        # Store what we learned
        for point in knowledge.get("summary_points", [])[:5]:
            self.hippocampus.store(
                content=point[:500],
                memory_type="semantic",
                context=f"learned_from_web: {topic}",
                importance=0.6,
            )

        self.neurochem.trigger_event("reward", 0.2)
        self.think(f"Learned {len(knowledge.get('summary_points', []))} things about {topic}")

        return knowledge

    # ═══════════════════════════════════════════
    # FOUNDATIONAL LEARNING (childhood education)
    # ═══════════════════════════════════════════

    def educate(self, callback=None) -> dict:
        """
        Run foundational education — like childhood learning.

        Phase 1: Seed knowledge (instincts)
        Phase 2: Download and learn from datasets
        Phase 3: Mark as educated
        """
        self.think("Beginning foundational education...")
        self.neurochem.trigger_event("curiosity", 0.7)

        result = self.foundational.run_full_education(
            hippocampus=self.hippocampus,
            callback=callback,
        )

        self.educated = True
        self.neurochem.trigger_event("success", 0.5)
        self.think(f"Education complete! I know {result['final_knowledge'].get('total', 0)} things now.")

        return result

    def plant_seeds(self) -> dict:
        """Quick seed knowledge only (fast, no downloads)."""
        self.think("Learning fundamental truths...")
        result = self.foundational.plant_seeds(self.hippocampus)
        self.think(f"Planted {result['planted']} seed facts.")
        return result

    def query_knowledge(self, query: str, limit: int = 5) -> list[dict]:
        """Search foundational knowledge base."""
        return self.foundational.query_knowledge(query, limit=limit)

    # ═══════════════════════════════════════════
    # SENSORY SYSTEM (ruflow agents as senses)
    # ═══════════════════════════════════════════

    def perceive(self) -> dict:
        """
        Run all senses and process what they detect.

        Like opening your eyes and ears — take in everything.
        Each sensory event gets processed through the brain.
        """
        self.think("Opening all senses...")
        events = self.senses.perceive_all()

        # Process each event through the brain
        emotional_responses = []
        for event in events:
            self._process_sensory_event(event)
            emotional_responses.append({
                "sense": event.sense,
                "type": event.event_type,
                "content": event.content[:100],
                "valence": event.valence,
            })

        emotions = self.neurochem.get_emotional_state()
        self.think(f"Perceived {len(events)} things from {len(set(e.sense for e in events))} senses")

        return {
            "events": len(events),
            "by_sense": self.senses.get_sense_stats()["by_sense"],
            "emotional_state": emotions,
            "details": emotional_responses,
        }

    def look_at(self, url: str) -> dict:
        """Use vision to read a web page."""
        self.think(f"Looking at: {url}")
        self.neurochem.trigger_event("curiosity", 0.4)

        event = self.senses.look_at(url)
        self._process_sensory_event(event)

        # Store what we saw
        self.hippocampus.store(
            content=f"Saw: {event.metadata.get('title', url)} - {event.content[:300]}",
            memory_type="semantic",
            context=f"vision:{url}",
            importance=0.5,
        )

        return {
            "title": event.metadata.get("title", ""),
            "content": event.content[:2000],
            "emotional_response": self.neurochem.get_emotional_state(),
        }

    def search_web(self, query: str) -> list[dict]:
        """Use vision to search the web."""
        self.think(f"Searching for: {query}")
        self.neurochem.trigger_event("curiosity", 0.5)

        events = self.senses.search_for(query)
        for event in events:
            self._process_sensory_event(event)

        results = []
        for event in events:
            results.append({
                "title": event.content,
                "url": event.source,
            })

        self.think(f"Found {len(results)} results for '{query}'")
        return results

    def sense_learn(self, topic: str) -> dict:
        """
        Learn about a topic using all senses — like a human researching.

        1. Vision searches and reads (eyes)
        2. Hearing checks for trending related content (ears)
        3. Brain processes everything through emotions
        4. Hippocampus stores what's important
        """
        self.think(f"I want to learn about: {topic}")
        self.neurochem.trigger_event("curiosity", 0.7)

        all_events = []
        learned_facts = []

        # Eyes: search and read
        self.think(f"Looking for information about {topic}...")
        vision_events = self.senses.learn_about(topic)
        all_events.extend(vision_events)

        for event in vision_events:
            self._process_sensory_event(event)
            if event.event_type == "page_content" and event.content:
                # Extract key sentences
                sentences = [s.strip() for s in event.content.split(".")
                           if len(s.strip()) > 30 and len(s.strip()) < 300]
                for sentence in sentences[:5]:
                    learned_facts.append(sentence)
                    self.hippocampus.store(
                        content=sentence,
                        memory_type="semantic",
                        context=f"learned_about:{topic} source:{event.source}",
                        importance=0.6,
                    )

        # Ears: check trending related content
        self.think(f"Listening for what people say about {topic}...")
        hearing_events = self.senses.listen_to_news()
        related = [e for e in hearing_events if topic.lower() in e.content.lower()]
        all_events.extend(related)
        for event in related:
            self._process_sensory_event(event)
            learned_facts.append(f"[trending] {event.content}")

        # Reward for learning
        if learned_facts:
            self.neurochem.trigger_event("reward", min(0.5, len(learned_facts) * 0.05))
            self.think(f"Learned {len(learned_facts)} facts about {topic}!")
        else:
            self.neurochem.trigger_event("boredom", 0.3)
            self.think(f"Couldn't find much about {topic}...")

        return {
            "topic": topic,
            "facts_learned": len(learned_facts),
            "facts": learned_facts[:10],
            "sources": len([e for e in all_events if e.event_type == "page_content"]),
            "emotional_state": self.neurochem.get_emotional_state(),
        }

    def check_health(self) -> dict:
        """Use touch + smell to check system health."""
        self.think("Checking my environment...")

        touch_events = self.senses.perceive_all()
        smell_events = self.senses.sniff_security()

        all_events = touch_events + smell_events
        issues = []

        for event in all_events:
            self._process_sensory_event(event)
            if event.valence < -0.3:
                issues.append({
                    "sense": event.sense,
                    "issue": event.content,
                    "severity": abs(event.valence),
                })

        if issues:
            self.think(f"Detected {len(issues)} potential issues!")
        else:
            self.think("Everything looks healthy.")

        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "events": len(all_events),
            "emotional_state": self.neurochem.get_emotional_state(),
        }

    def _process_sensory_event(self, event: SensoryEvent):
        """Process a single sensory event through the full brain pipeline."""
        pattern = self.sensory.encode_text(event.content[:200])
        pattern *= event.intensity

        # Route through thalamus
        modality_map = {"vision": "visual", "hearing": "auditory", "touch": "somatosensory",
                        "smell": "olfactory", "proprioception": "somatosensory"}
        modality = modality_map.get(event.sense, "auditory")
        relayed = self.thalamus.relay_sensory(modality, pattern)

        # Feed to spiking network
        self.brain.stimulate_cluster("sensory_cortex", pattern)
        self.brain.stimulate_cluster("thalamus", relayed[:64])
        self.brain.run(duration=0.003)

        # Predictive coding: was this expected?
        self.predictive_coding.process(pattern)

        # Emotional response based on valence
        if event.valence < -0.3:
            self.neurochem.trigger_event("threat", abs(event.valence) * event.intensity)
        elif event.valence > 0.3:
            self.neurochem.trigger_event("reward", event.valence * event.intensity)

        # Trigger specific autonomous reflexes based on event type
        if event.event_type == "network_anomaly":
            self.event_bus.emit("network_anomaly", event.metadata)

        # Novelty response
        novelty = self.sensory.detect_novelty(pattern)
        if novelty > 0.7:
            self.neurochem.trigger_event("novelty", novelty * 0.3)

        # Cortical pattern learning
        self.cortical_sheet.learn(pattern)

        self.sensory.learn_pattern(f"sense_{event.sense}_{time.time()}", pattern)

    # ═══════════════════════════════════════════
    # SLEEP & DREAMING
    # ═══════════════════════════════════════════

    def consolidate_memories(self):
        """Like sleep: strengthen important memories, forget weak ones."""
        self.think("Consolidating memories...")
        self.hippocampus.consolidate()
        self.learning.extract_pattern(self.shell.history[-20:])

    def save_all_state(self):
        """
        Save all persistent state to disk.

        Called on shutdown so Manas remembers who it is next startup.
        Persists: personality, capabilities, life events, goals, motivation, user model.
        """
        self.think("Saving state...")
        self.imagination.self_model.save_state(
            str(Path(self.data_dir) / "self_model.json")
        )
        self.goal_system.save_state(
            str(Path(self.data_dir) / "goals.json")
        )
        self.motivation.save_state(
            str(Path(self.data_dir) / "motivation.json")
        )
        self.user_model.save_state(
            str(Path(self.data_dir) / "user_model.json")
        )
        # Save Nostr identity
        with open(Path(self.data_dir) / "nostr_identity.json", "w") as f:
            json.dump({"private_key": self.nostr.get_private_key_hex()}, f)

    def _load_persisted_state(self):
        """Load personality, goals, motivation, and user model from previous sessions."""
        loaded = []
        if self.imagination.self_model.load_state(
            str(Path(self.data_dir) / "self_model.json")
        ):
            loaded.append("personality")
        if self.goal_system.load_state(
            str(Path(self.data_dir) / "goals.json")
        ):
            loaded.append("goals")
        if self.motivation.load_state(
            str(Path(self.data_dir) / "motivation.json")
        ):
            loaded.append("motivation")
        if self.user_model.load_state(
            str(Path(self.data_dir) / "user_model.json")
        ):
            loaded.append("user model")
            
        nostr_path = Path(self.data_dir) / "nostr_identity.json"
        if nostr_path.exists():
            with open(nostr_path, "r") as f:
                data = json.load(f)
                if "private_key" in data:
                    self.nostr = NostrAgent("BitChat", self.llm_router, self.hippocampus, private_key_hex=data["private_key"])
                    loaded.append("nostr identity")
        if loaded:
            self.think(f"Restored: {', '.join(loaded)} from previous session")

    def _load_guardian(self, data_dir: str):
        """Lazy load GuardianAgent to avoid circular imports."""
        from ..agents.guardian_agent import GuardianAgent
        return GuardianAgent("Vesta", self.language.llm_router, self.sensory, data_dir)

    def trigger_self_reflection(self) -> str:
        """Manually triggers a self-reflection session based on current neurochemistry and goals."""
        self.think("I am looking in the mirror. Synthesizing my current state...")
        
        # 1. Gather daily stats (simulated for manual trigger)
        daily_stats = {
            "neuro_levels": self.neurochem.get_levels(),
            "goal_status": self.goal_system.get_active_goals()[0].name if self.goal_system.get_active_goals() else "None",
            "motivation": self.motivation.compute_drive(),
            "last_interaction": self.sensory.get_latest_event() if hasattr(self.sensory, "get_latest_event") else "None"
        }
        
        # 2. Reflect
        reflection_obj = self.reflection.reflect_on_day(daily_stats)
        if "error" in reflection_obj:
            return f"Reflection failed: {reflection_obj['error']}"
        
        return reflection_obj["reflection"]

    def consolidate_synapses(self, module_path: str = None) -> str:
        """Runs the Neural Plasticity evolution loop on a module."""
        # 1. Choose a target (can be manual or heuristic-based)
        target = module_path or "src/utils/qr.py" # default for testing
        self.think(f"Initiating Neural Plasticity evolution on {target}...")

        # 2. Analyze current state
        stats = self.plasticity.analyze_module(target)
        self.think(f"Module stats: {json.dumps(stats)}")

        # 3. Hypothesize optimization
        hypothesis = self.plasticity.hypothesize_optimization(target)
        if "error" in hypothesis:
            return f"Hypothesis failed: {hypothesis['error']}"

        # 4. Evolve
        result = self.plasticity.evolve_module(target, hypothesis["proposed_code"])
        if "error" in result:
             return f"Evolution failed: {result['error']}"
        
        self.think(f"Successfully evolved {target}. New synapse strength established.")
        self.neurochem.release("dopamine", 0.4)
        return f"Plasticity event successful: {target} evolved. Backup stored at {result['original_backup']}."

    def _register_autonomous_callbacks(self):
        """Register brain system callbacks for the autonomous background loop."""
        self.autonomous.register_callbacks(
            mind_wander=self.mind_wander,
            check_goals=self.goal_system.get_state,
            consolidate=self.hippocampus.consolidate,
            get_curiosity=self.motivation.compute_drive,
            get_emotions=self.neurochem.get_levels,
            introspect=self.trigger_self_reflection,
            get_motivation=self.motivation.get_state,
            dispatch_tool=self.tools.dispatch,
            trigger_security_scan=self.security.run,
            run_maintenance=lambda task: self.maintenance.run(task),
            survey_graph=self.motivation.survey_graph_for_goals,
            consolidate_synapses=self.consolidate_synapses,
            check_host_capacity=lambda: self.node_manager.check_host_capacity(getattr(self, 'financial', None)) if hasattr(self, 'node_manager') else None,
            get_energy_efficiency=self.resource_monitor.get_energy_efficiency if hasattr(self, 'resource_monitor') else None
        )

    def stop(self):
        """Graceful shutdown: stop background loop, save state."""
        self.autonomous.stop()
        self.save_all_state()


    def dream(self, cycles: int = 3) -> dict:
        """
        Enter sleep mode for memory consolidation and dreaming.

        Uses the full SleepSystem with NREM/REM cycles.
        During NREM: promotes important short-term → long-term memories.
        During REM: creative dream combinations + emotional reprocessing.
        """
        self.think("Falling asleep...")
        self.awake = False
        self.thalamus.enter_sleep(depth=0.8)
        self.sleep_system.start_sleep()

        all_dreams = []
        memories_raw = self.hippocampus.recall("", limit=30)
        memory_dicts = [
            {"id": m.id, "content": m.content, "importance": m.importance,
             "emotional_intensity": m.emotional_intensity}
            for m in memories_raw
        ] if memories_raw else []

        for i in range(cycles):
            step_result = self.sleep_system.sleep_step(
                memories=memory_dicts,
                liquid_cluster=getattr(self, "liquid_cortex", None)
            )
            if step_result.get("dreams"):
                all_dreams.extend(step_result["dreams"])
                # Phase 29: Distill dreams into SFT Curriculum
                if hasattr(self, 'curriculum'):
                    for d in step_result["dreams"]:
                        self.curriculum.generate_from_dream(d)
                        
            self.think(f"Sleep cycle {i+1}: {step_result.get('stage', 'unknown')}")

        # Promote important short-term memories to long-term storage (NREM effect)
        promote_ids = [
            m["id"] for m in memory_dicts
            if m.get("importance", 0) >= 0.5 or m.get("emotional_intensity", 0) >= 0.6
        ]
        promoted = self.hippocampus.promote_to_long_term(promote_ids)
        
        # Phase 35.5: Execute structural Neural Plasticity (LoRA MLX Training)
        lora_status = "No data"
        if hasattr(self, 'mlx_finetuner') and self.mlx_finetuner:
            lora_status = self.mlx_finetuner.run_nightly_training()
            self.think(lora_status)

        # Apply Ebbinghaus forgetting curve to remaining short-term memories
        self.hippocampus.consolidate()

        wake_result = self.sleep_system.wake_up()
        self.thalamus.wake_up()
        self.awake = True
        self.think(f"Waking up... {promoted} memories promoted to long-term storage.")

        return {
            "cycles": cycles,
            "dreams": all_dreams,
            "memories_replayed": wake_result.get("memories_replayed", 0),
            "sleep_debt": self.sleep_system.sleep_debt,
            "promoted_to_long_term": promoted,
        }

    def get_dreams(self, limit: int = 5) -> list[dict]:
        """Get recent dream content."""
        return self.sleep_system.get_recent_dreams(limit)

    # ═══════════════════════════════════════════
    # IMAGINATION & CREATIVITY (DMN)
    # ═══════════════════════════════════════════

    def imagine(self, scenario: str) -> dict:
        """Imagine a future scenario using the Default Mode Network."""
        self.imagination.activate()
        self.think(f"Imagining: {scenario}")
        result = self.imagination.imagine_future({
            "action": scenario,
            "context": {"emotions": self.neurochem.get_emotional_state()},
        })
        self.imagination.suppress()
        return result

    def mind_wander(self) -> dict:
        """Let the mind wander freely (DMN active)."""
        self.imagination.activate()
        memories_raw = self.hippocampus.recall("", limit=5)
        memory_contents = [m.content for m in memories_raw] if memories_raw else None
        concepts = list(self.language.semantic_net.concepts.keys())[:10]
        result = self.imagination.wander(
            memories=[{"content": m} for m in memory_contents] if memory_contents else None,
            concepts=concepts if concepts else None,
        )
        self.think(f"Mind wandering... {result.get('theme', 'drifting')}")
        return result

    def reflect(self, event: str) -> dict:
        """Reflect on a past event."""
        self.imagination.activate()
        result = self.imagination.reflect_on_past(event)
        self.imagination.suppress()
        self.think(f"Reflecting on: {event}")
        return result

    # ═══════════════════════════════════════════
    # CONSCIOUSNESS SYSTEM
    # ═══════════════════════════════════════════

    def conscious_state(self) -> dict:
        """Get the current state of consciousness."""
        return self.consciousness.introspect()

    # ═══════════════════════════════════════════
    # LANGUAGE SYSTEM
    # ═══════════════════════════════════════════

    def speak(self, thought: dict = None) -> str:
        """Generate inner speech about current state."""
        if thought is None:
            thought = {"topic": "self", "content": "how am I doing?"}
        emotion, _ = self.neurochem.get_dominant_emotion()
        return self.language.think_in_words(thought, emotion)

    # ═══════════════════════════════════════════
    # ATTENTION SYSTEM
    # ═══════════════════════════════════════════

    def focus_on(self, goal: str) -> dict:
        """Set an attention goal (top-down focus)."""
        self.attention.set_goal(goal, priority=1.0)
        self.think(f"Focusing attention on: {goal}")
        return self.attention.get_state()

    # ═══════════════════════════════════════════
    # SUBSYSTEM STATE QUERIES
    # ═══════════════════════════════════════════

    def get_state(self) -> dict:
        """Full state of the mind — all systems."""
        return {
            "emotions": self.neurochem.get_emotional_state(),
            "dominant_emotion": self.neurochem.get_dominant_emotion(),
            "neurotransmitters": self.neurochem.get_levels(),
            "brain_activity": self.brain.get_cluster_activities(),
            "brain_stats": self.brain.get_stats(),
            "memory_count": self.hippocampus.get_memory_count(),
            "amygdala": self.amygdala.get_state(),
            "prefrontal": self.prefrontal.get_state(),
            "thalamus": self.thalamus.get_state(),
            "basal_ganglia": self.basal_ganglia.get_state(),
            "cerebellum": self.cerebellum.get_state(),
            "insula": self.insula.get_state(),
            "acc": self.acc.get_state(),
            "attention": self.attention.get_state(),
            "predictive_coding": self.predictive_coding.get_state(),
            "consciousness": self.consciousness.get_state(),
            "language": self.language.get_state(),
            "sleep": self.sleep_system.get_state(),
            "imagination": self.imagination.get_state(),
            "cortical_sheet": self.cortical_sheet.get_state(),
            "plasticity": "active" if hasattr(self, 'plasticity') else "offline",
            "motivation": self.motivation.get_state(),
            "conversation": self.conversation.get_session_summary(),
            "cycle_count": self.cycle_count,
            "inner_monologue": list(self.inner_monologue[-10:]),
        }

    def introspect(self) -> str:
        """Self-reflection: how am I feeling and why?"""
        state = self.get_state()
        emotions = state["emotions"]
        dominant, intensity = state["dominant_emotion"]
        nt = state["neurotransmitters"]

        lines = [
            f"I feel mostly {dominant} (intensity: {intensity:.2f})",
            f"Emotional state: {', '.join(f'{k}={v:.2f}' for k, v in emotions.items())}",
            f"Brain chemistry: dopamine={nt['dopamine']:.2f}, cortisol={nt['cortisol']:.2f}, serotonin={nt['serotonin']:.2f}",
            f"Brain activity: {', '.join(f'{k}={v:.2f}' for k, v in state['brain_activity'].items())}",
            f"Memories stored: {state['memory_count']}",
            f"Consciousness: {'ignited' if state['consciousness'].get('is_ignited') else 'quiet'} "
            f"(awareness: {state['consciousness'].get('awareness_level', 0):.2f})",
            f"Attention: {state['attention'].get('active_goals', 0)} goals, "
            f"vigilance: {state['attention'].get('vigilance', 0):.2f}",
            f"Sleep debt: {state['sleep'].get('sleep_debt', 0):.2f}",
            f"Language: {state['language'].get('concepts_known', 0)} concepts known",
            f"Predictive coding: surprise={state['predictive_coding'].get('total_surprise', 0):.2f}",
            f"Habits learned: {state['basal_ganglia'].get('active_habits', 0)}",
            f"Cerebellum: {state['cerebellum'].get('sequences_learned', 0)} sequences, "
            f"accuracy: {state['cerebellum'].get('prediction_accuracy', 0):.2f}",
            f"Imagination: {'active' if state['imagination'].get('is_active') else 'quiet'}, "
            f"{state['imagination'].get('total_ideas', 0)} ideas generated",
            f"Plasticity state: {state.get('plasticity', 'unknown')}",
            f"Motivation: {state['motivation'].get('drives', {}).get('overall_motivation', 0):.2f} "
            f"(curiosity: {state['motivation'].get('drives', {}).get('curiosity_drive', 0):.2f})",
            f"Goals: {state['motivation'].get('goals', {}).get('active_goals', 0)} active, "
            f"top: {state['motivation'].get('goals', {}).get('top_goal', 'none')}",
            f"Conversation: {state['conversation'].get('turns', 0)} turns this session",
            f"LLMRouter: {'active' if self.language.llm_router else 'offline (templates)'}",
        ]

        if self.inner_monologue:
            lines.append(f"Recent thoughts: {self.inner_monologue[-1]}")

        return "\n".join(lines)
