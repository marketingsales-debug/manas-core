"""
Manas CLI - Interactive chat interface.

Talk to the cognitive AI agent.
It feels, thinks, remembers, and learns.
"""

import json
import asyncio
from ..cognition.mind import Mind
from ..utils.qr import generate_text_qr


BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                      PROJECT MANAS                            ║
║              Neuromorphic Cognitive AI Agent                   ║
║           All 17 brain systems fully integrated                ║
║                                                               ║
║  ACTIONS:                                                     ║
║    !run <cmd>       - Execute a shell command                  ║
║    !search <query>  - Search the web (vision)                  ║
║    !look <url>      - Read a web page (vision)                 ║
║    !learn <topic>   - Deep-learn a topic (all senses)          ║
║    !news            - Check trending news (hearing)            ║
║    !nostr <cmd>     - BitChat (Nostr) setup & messaging        ║
║    !intelligence <cmd>     - World monitoring (status, pull, simulate)║
║    !scout <cmd>            - Discovery scouting (status, run)║
║    !mission <goal>         - Start a stateful LangGraph mission║
║    !crew <objective>       - Assemble a CrewAI team for a project║
║    !evolve                 - Trigger autonomous self-evolution║
║    !finance <cmd>          - Metabolism & Financial Agent control║
║    !domicile <cmd>         - Physical Presence & Home Assistant║
║    !memory <cmd>           - Infinite Memory (core, archive, view)║
║    !skill <cmd>            - Meta-Learning / Skill Acquisition║
║    !project <cmd>          - Autonomous SaaS Project Launcher║
║    !influence <cmd>        - Social Growth & Monetization║
║    !feel                   - Check neurochemical levels       ║
                                                               ║
║  EDUCATION:                                                   ║
║    !educate         - Run foundational education (datasets)    ║
║    !seeds           - Plant seed knowledge only (fast)         ║
║    !knowledge <q>   - Search foundational knowledge            ║
                                                               ║
║  SENSES:                                                      ║
║    !perceive        - Run all senses (see/hear/touch/smell)    ║
║    !health          - Check system health (touch + smell)      ║
║    !senses          - Show sensory system stats                ║
║                                                               ║
║  BRAIN SYSTEMS:                                               ║
║    !dream           - Enter sleep for memory consolidation     ║
║    !dreams          - Show recent dream content                ║
║    !imagine <what>  - Imagine a scenario (DMN)                 ║
║    !wander          - Let the mind wander freely               ║
║    !reflect <event> - Reflect on a past event                  ║
║    !consciousness   - Show consciousness state                 ║
║    !attention <goal>- Focus attention on a goal                ║
║    !language        - Show language system stats               ║
║    !predict         - Show predictive coding state             ║
║    !habits          - Show basal ganglia / habit stats         ║
║    !cerebellum      - Show cerebellum / sequence stats         ║
║    !feelings        - Show insula / gut feelings               ║
║    !conflict        - Show ACC / conflict monitor              ║
║    !thalamus        - Show thalamic relay state                ║
║    !cortex          - Show cortical column stats               ║
║                                                               ║
║  SELF:                                                        ║
║    !feel            - Show emotional state                     ║
║    !think           - Show inner monologue                     ║
║    !memory          - Show memory stats                        ║
║    !brain           - Show brain activity                      ║
║    !introspect      - Full self-reflection                     ║
║    !consolidate     - Consolidate memories (like sleep)        ║
║    !state           - Full system state (JSON)                 ║
║    !embed           - Embed all memories for semantic search    ║
║    !user            - Show what I know about you                ║
║    !autonomous      - Show background thinking state            ║
║    !help            - Show this help                           ║
║    quit/exit        - Exit                                     ║
╚═══════════════════════════════════════════════════════════════╝
"""

EMOTION_ICONS = {
    "fear": "😨",
    "happiness": "😊",
    "curiosity": "🤔",
    "anxiety": "😰",
    "confidence": "😎",
    "caution": "⚠️",
}


class ManasCLI:
    """Interactive command-line interface for Manas."""

    def __init__(self):
        self.mind = Mind()

    async def run(self):
        """Start the interactive loop."""
        print(BANNER)
        
        # Start the mind's background loops
        self.mind.start()
        
        print(f"  Brain: {self.mind.brain.get_stats()['total_neurons']} spiking neurons, "
              f"{self.mind.brain.get_stats()['total_synapses']} synapses")
        print(f"  Status: {self.mind.introspect().split(chr(10))[0]}")
        print()

        while True:
            try:
                # Show any spontaneous thoughts from background loop
                thoughts = self.mind.autonomous.get_new_thoughts(limit=3)
                for thought in thoughts:
                    print(f"  💭 [{thought.type}] {thought.content}")
                if thoughts:
                    print()

                # Show emotional state in prompt
                emotion, intensity = self.mind.neurochem.get_dominant_emotion()
                icon = EMOTION_ICONS.get(emotion, "🧠")

                # Show user name if known
                user_name = self.mind.user_model.name
                user_tag = f" ({user_name})" if user_name else ""
                prompt = f"{icon} manas [{emotion}:{intensity:.1f}]{user_tag}> "

                # Non-blocking input to allow background tasks to run
                user_input = await asyncio.get_event_loop().run_in_executor(None, input, prompt)
                user_input = user_input.strip()

                if not user_input:
                    continue

                if user_input.lower() in ("quit", "exit", "bye"):
                    self.mind.think("Time to rest...")
                    self.mind.stop()
                    print("\n🌙 Saving state & consolidating memories... Goodnight.")
                    break

                response = self._handle_input(user_input)
                if response:
                    print(response)
                    print()

            except KeyboardInterrupt:
                print("\n\n🌙 Interrupted. Saving state...")
                self.mind.stop()
                break
            except EOFError:
                break

    def _handle_input(self, user_input: str) -> str:
        """Process user input and return response."""

        # Special commands
        if user_input.startswith("!"):
            return self._handle_command(user_input)

        # Regular conversation: process through the full cognitive pipeline
        response = self.mind.process_input(user_input)

        # Build response text
        lines = []

        # Show language-generated response first (natural language from Broca's)
        lang_resp = response.get("language_response", "")
        if lang_resp:
            lines.append(f"💬 {lang_resp}")
            lines.append("")

        # Show emotional response
        emotion = response["dominant_emotion"]
        intensity = response["emotion_intensity"]
        icon = EMOTION_ICONS.get(emotion, "🧠")
        lines.append(f"{icon} Feeling: {emotion} ({intensity:.2f})")

        # Show if threat was detected
        threat = response.get("threat_assessment", {"threat_level": 0.0})
        if threat.get("threat_level", 0.0) > 0.2:
            lines.append(f"⚠️  Threat detected: {threat.get('emotional_response', 'unknown')} "
                        f"(level: {threat.get('threat_level', 0.0):.2f})")
            if threat["reasons"]:
                lines.append(f"   Reasons: {', '.join(threat['reasons'])}")

        # Show comprehension
        comp = response.get("comprehension", {})
        if comp.get("intent"):
            lines.append(f"📖 Understood: intent={comp['intent']}, tone={comp.get('emotional_tone', '?')}")

        # Show reasoning
        r = response.get("reasoning", {})
        action = r.get("action", "unknown")
        capacity = r.get("reasoning_capacity", 1.0)
        conf = r.get("confidence", 1.0)
        lines.append(f"🧠 Reasoning: {action} (capacity: {capacity:.2f}, "
                     f"confidence: {conf:.2f})")

        # Show gut feeling
        gut = response.get("gut_feeling", {})
        if gut.get("intensity", 0) > 0.3:
            lines.append(f"🫁 Gut feeling: {gut.get('valence', '?')} ({gut.get('intensity', 0):.2f})")

        # Show conflict
        conflict = response.get("conflict_level", 0)
        if conflict > 0.3:
            lines.append(f"⚡ Internal conflict: {conflict:.2f}")

        # Show surprise
        surprise = response.get("surprise", 0)
        if surprise > 0.3:
            lines.append(f"❗ Surprise level: {surprise:.2f}")

        # Show memories if recalled
        if response["memories_recalled"] > 0:
            lines.append(f"💭 Recalled {response['memories_recalled']} related memories")

        # Show novelty
        if response["novelty"] > 0.7:
            lines.append(f"✨ This is novel! (novelty: {response['novelty']:.2f})")

        # Show inner thoughts
        if response["inner_monologue"]:
            lines.append(f"🧠 Thinking: {response['inner_monologue'][-1]}")

        # Show tool result if a tool fired
        tool_res = response.get("tool_result")
        if tool_res and tool_res.get("success"):
            tool_name = tool_res.get("tool_name", "tool")
            tool_output = tool_res.get("output", "")
            lines.append(f"🔧 Tool used: {tool_name}")
            lines.append(f"   {tool_output[:400]}")

        return "\n".join(lines)

    def _handle_command(self, cmd: str) -> str:
        """Handle special commands."""
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "!run":
            if not args:
                return "Usage: !run <command>"
            result = self.mind.execute_action(args)
            return self._format_execution(result)

        elif command == "!learn":
            if not args:
                return "Usage: !learn <topic>"
            result = self.mind.sense_learn(args)
            lines = [f"📚 Deep-learned about: {args}"]
            lines.append(f"   Facts learned: {result['facts_learned']}")
            lines.append(f"   Sources read: {result['sources']}")
            for fact in result.get("facts", [])[:8]:
                lines.append(f"  • {fact[:150]}")
            emotion = max(result["emotional_state"], key=result["emotional_state"].get)
            lines.append(f"   Feeling: {emotion}")
            return "\n".join(lines)

        elif command == "!search":
            if not args:
                return "Usage: !search <query>"
            results = self.mind.search_web(args)
            lines = [f"👁️ Search results for: {args}"]
            for r in results:
                lines.append(f"  • {r['title']}")
                if r.get("url"):
                    lines.append(f"    {r['url']}")
            return "\n".join(lines) if results else "No results found."

        elif command == "!look":
            if not args:
                return "Usage: !look <url> OR !look room"
                
            if args.lower() == "room":
                print("📷 Capturing webcam...")
                events = self.mind.senses.vision.look_at_real_world()
                if not events: return "❌ Failed to capture webcam."
                event = events[0]
                self.mind._process_sensory_event(event) # Feed to internal brain pipeline
                return f"👁️ (Webcam):\n{event.content}"
                
            result = self.mind.look_at(args)
            lines = [f"👁️ Reading: {result.get('title', args)}"]
            content = result.get("content", "")[:1500]
            lines.append(content)
            emotion = max(result["emotional_response"], key=result["emotional_response"].get)
            lines.append(f"\n   Feeling: {emotion}")
            return "\n".join(lines)
            
        elif command == "!listen":
            duration = 5
            if args.isdigit(): duration = int(args)
            print(f"🎤 Recording microphone for {duration} seconds...")
            events = self.mind.senses.hearing.listen_to_real_world(duration_sec=duration)
            if not events: return "❌ Failed to record microphone."
            event = events[0]
            self.mind._process_sensory_event(event) # Feed to internal brain pipeline
            return f"👂:\n{event.content}"

        elif command == "!news":
            events = self.mind.senses.listen_to_news()
            lines = ["👂 Trending right now:"]
            for event in events:
                score = event.metadata.get("score", "")
                comments = event.metadata.get("comments", "")
                lines.append(f"  • {event.content}")
                if score:
                    lines.append(f"    [{score} points, {comments} comments]")
                self.mind._process_sensory_event(event)
            return "\n".join(lines)

        elif command == "!educate":
            lines = ["🎒 Starting foundational education...\n"]
            def progress(phase, msg):
                lines.append(f"  [{phase}] {msg}")
            result = self.mind.educate(callback=progress)
            lines.append("\n📚 Education complete!")
            knowledge = result.get("final_knowledge", {})
            lines.append(f"   Total knowledge items: {knowledge.get('total', 0)}")
            for cat, count in knowledge.items():
                if cat != "total":
                    lines.append(f"   {cat}: {count}")
            return "\n".join(lines)

        elif command == "!seeds":
            result = self.mind.plant_seeds()
            return f"🌱 Planted {result['planted']} seed facts (out of {result['total_seeds']} total)"

        elif command == "!knowledge":
            if not args:
                return "Usage: !knowledge <query>"
            results = self.mind.query_knowledge(args)
            lines = [f"📖 Knowledge about: {args}"]
            for r in results:
                lines.append(f"  [{r['category']}] {r['content'][:150]}")
            return "\n".join(lines) if results else "No matching knowledge found."

        elif command == "!perceive":
            result = self.mind.perceive()
            lines = [f"🌐 Perceived {result['events']} events:"]
            for sense, count in result.get("by_sense", {}).items():
                sense_icons = {"touch": "🤚", "smell": "👃", "proprioception": "🧘"}
                icon = sense_icons.get(sense, "🔵")
                lines.append(f"  {icon} {sense}: {count} events")
            emotion = max(result["emotional_state"], key=result["emotional_state"].get)
            lines.append(f"  Feeling: {emotion}")
            return "\n".join(lines)

        elif command == "!health":
            result = self.mind.check_health()
            if result["healthy"]:
                lines = ["✅ System is healthy!"]
            else:
                lines = [f"⚠️ Detected {len(result['issues'])} issues:"]
                for issue in result["issues"]:
                    lines.append(f"  [{issue['sense']}] {issue['issue']}")
            return "\n".join(lines)

        elif command == "!senses":
            stats = self.mind.senses.get_sense_stats()
            lines = ["🌐 Sensory System:"]
            lines.append(f"  Total events processed: {stats['total_events']}")
            lines.append(f"  Pages seen (vision): {stats['pages_seen']}")
            lines.append(f"  Feeds monitored (hearing): {stats['feeds_monitored']}")
            for sense, count in stats.get("by_sense", {}).items():
                lines.append(f"  {sense}: {count} events")
            return "\n".join(lines)

        elif command == "!feel":
            emotions = self.mind.neurochem.get_emotional_state()
            levels = self.mind.neurochem.get_levels()
            lines = ["Emotional State:"]
            for emotion, value in sorted(emotions.items(), key=lambda x: -x[1]):
                bar = "█" * int(value * 20) + "░" * (20 - int(value * 20))
                icon = EMOTION_ICONS.get(emotion, "  ")
                lines.append(f"  {icon} {emotion:12s} [{bar}] {value:.2f}")
            lines.append("\nBrain Chemistry:")
            for chem, value in sorted(levels.items(), key=lambda x: -x[1]):
                bar = "█" * int(value * 20) + "░" * (20 - int(value * 20))
                lines.append(f"     {chem:16s} [{bar}] {value:.2f}")
            return "\n".join(lines)

        elif command == "!think":
            thoughts = self.mind.inner_monologue[-10:]
            if not thoughts:
                return "💬 Mind is quiet..."
            return "💬 Inner monologue:\n" + "\n".join(f"  {t}" for t in thoughts)

        elif command == "!memory":
            counts = self.mind.hippocampus.get_memory_count()
            lines = ["🧠 Memory System:"]
            for mtype, count in counts.items():
                lines.append(f"  {mtype}: {count} memories")
            # Show embedding stats
            embed_stats = self.mind.hippocampus.get_embedding_stats()
            lines.append("\n  📊 Embedding Coverage:")
            lines.append(f"    Total: {embed_stats['total_memories']}")
            lines.append(f"    Embedded: {embed_stats['embedded']} ({embed_stats['coverage']})")
            lines.append(f"    Model: {'✅ available' if embed_stats['model_available'] else '❌ unavailable'}")
            if embed_stats['unembedded'] > 0:
                lines.append(f"    ⚠️  {embed_stats['unembedded']} memories need embedding. Run !embed")
            return "\n".join(lines) if counts else "🧠 No memories yet."

        elif command == "!brain":
            activity = self.mind.brain.get_cluster_activities()
            stats = self.mind.brain.get_stats()
            lines = [
                f"🧠 Brain Activity ({stats['total_neurons']} neurons, {stats['total_synapses']} synapses):",
            ]
            for region, level in activity.items():
                bar = "█" * int(level * 20) + "░" * (20 - int(level * 20))
                lines.append(f"  {region:20s} [{bar}] {level:.2f}")
            return "\n".join(lines)

        elif command == "!introspect":
            return "🪞 Self-reflection:\n" + self.mind.introspect()

        elif command == "!consolidate":
            self.mind.consolidate_memories()
            return "🌙 Memories consolidated. Weak memories forgotten, important ones strengthened."

        elif command == "!state":
            state = self.mind.get_state()
            return json.dumps(state, indent=2, default=str)

        # === NEW BRAIN SYSTEM COMMANDS ===

        elif command == "!dream":
            cycles = int(args) if args and args.isdigit() else 3
            result = self.mind.dream(cycles=cycles)
            lines = [f"😴 Slept for {result['cycles']} cycles"]
            lines.append(f"   Memories replayed: {result['memories_replayed']}")
            lines.append(f"   Sleep debt remaining: {result['sleep_debt']:.2f}")
            if result["dreams"]:
                lines.append("   Dreams:")
                for dream in result["dreams"][:5]:
                    lines.append(f"     🌙 {dream.get('content', dream)[:120] if isinstance(dream, dict) else str(dream)[:120]}")
            return "\n".join(lines)

        elif command == "!dreams":
            dreams = self.mind.get_dreams(limit=5)
            if not dreams:
                return "🌙 No dreams recorded yet. Try !dream first."
            lines = ["🌙 Recent dreams:"]
            for d in dreams:
                content = d.get("content", str(d))[:150] if isinstance(d, dict) else str(d)[:150]
                lines.append(f"  • {content}")
            return "\n".join(lines)

        elif command == "!imagine":
            if not args:
                return "Usage: !imagine <scenario>"
            result = self.mind.imagine(args)
            lines = [f"🌈 Imagining: {args}"]
            lines.append(f"   Predicted outcome: {result.get('predicted_outcome', 'uncertain')}")
            lines.append(f"   Emotional valence: {result.get('emotional_valence', 0):.2f}")
            lines.append(f"   Confidence: {result.get('confidence', 0):.2f}")
            return "\n".join(lines)

        elif command == "!wander":
            result = self.mind.mind_wander()
            if result.get("status") == "suppressed":
                return "🧘 DMN is suppressed (busy processing). Try again when idle."
            lines = ["🌀 Mind wandering..."]
            lines.append(f"   Theme: {result.get('theme', 'free association')}")
            thoughts = result.get("thoughts", [])
            for t in thoughts[:5]:
                lines.append(f"   💭 {t[:120] if isinstance(t, str) else str(t)[:120]}")
            return "\n".join(lines)

        elif command == "!reflect":
            if not args:
                return "Usage: !reflect <event to reflect on>"
            result = self.mind.reflect(args)
            lines = [f"🪞 Reflecting on: {args}"]
            lines.append(f"   {result.get('reflection', '')}")
            self_knowledge = result.get("self_knowledge", {})
            if self_knowledge:
                lines.append(f"   Self: {self_knowledge.get('name', 'Manas')} - {self_knowledge.get('purpose', 'thinking')}")
            return "\n".join(lines)

        elif command == "!consciousness":
            state = self.mind.conscious_state()
            lines = ["🔮 Consciousness State:"]
            lines.append(f"  Awareness level: {state.get('awareness_level', 0):.2f}")
            lines.append(f"  Workspace ignited: {state.get('is_ignited', False)}")
            lines.append(f"  Stream length: {state.get('stream_length', 0)}")
            lines.append(f"  Unconscious processes: {state.get('unconscious_processes', 0)}")
            current = state.get("current_content", [])
            if current:
                lines.append("  Current conscious content:")
                for item in current[:3]:
                    content = item.get("content", str(item))[:100] if isinstance(item, dict) else str(item)[:100]
                    lines.append(f"    • {content}")
            stream = state.get("recent_stream", [])
            if stream:
                lines.append("  Stream of consciousness:")
                for s in stream[:5]:
                    content = s.get("content", str(s))[:80] if isinstance(s, dict) else str(s)[:80]
                    lines.append(f"    → {content}")
            return "\n".join(lines)

        elif command == "!attention":
            if args:
                result = self.mind.focus_on(args)
                lines = [f"🎯 Focusing on: {args}"]
            else:
                result = self.mind.attention.get_state()
                lines = ["🎯 Attention State:"]
            lines.append(f"  Vigilance: {result.get('vigilance', 0):.2f}")
            lines.append(f"  Fatigue: {result.get('fatigue', 0):.2f}")
            lines.append(f"  Active goals: {result.get('active_goals', 0)}")
            spotlight = result.get("spotlight_items", [])
            if spotlight:
                lines.append("  In spotlight:")
                for item in spotlight:
                    lines.append(f"    • {item.get('id', '?')} (salience: {item.get('salience', 0):.2f})")
            return "\n".join(lines)

        elif command == "!language":
            state = self.mind.language.get_state()
            lines = ["📝 Language System:"]
            lines.append(f"  Concepts known: {state.get('concepts_known', 0)}")
            lines.append(f"  Associations: {state.get('associations', 0)}")
            lines.append(f"  Comprehension history: {state.get('comprehension_history', 0)}")
            lines.append(f"  Inner speech buffer: {state.get('inner_speech_buffer', 0)}")
            return "\n".join(lines)

        elif command == "!predict":
            state = self.mind.predictive_coding.get_state()
            lines = ["🔮 Predictive Coding:"]
            lines.append(f"  Total surprise: {state.get('total_surprise', 0):.3f}")
            lines.append(f"  Free energy: {state.get('free_energy', 0):.3f}")
            for layer, surprise in state.get("layer_surprise", {}).items():
                precision = state.get("layer_precision", {}).get(layer, 0)
                lines.append(f"  {layer:12s}: surprise={surprise:.3f}, precision={precision:.2f}")
            return "\n".join(lines)

        elif command == "!habits":
            state = self.mind.basal_ganglia.get_state()
            lines = ["🎯 Basal Ganglia (Action Selection):"]
            lines.append(f"  Active habits: {state.get('active_habits', 0)}")
            lines.append(f"  Reward predictions learned: {state.get('predictions_learned', 0)}")
            lines.append(f"  Total selections: {state.get('total_selections', 0)}")
            lines.append(f"  Emergency brake (STN): {state.get('emergency_brake', False)}")
            last = state.get("last_selection")
            if last:
                lines.append(f"  Last selection: {last}")
            return "\n".join(lines)

        elif command == "!cerebellum":
            state = self.mind.cerebellum.get_state()
            lines = ["🧩 Cerebellum (Sequences & Prediction):"]
            lines.append(f"  Prediction accuracy: {state.get('prediction_accuracy', 0):.2f}")
            lines.append(f"  Forward models learned: {state.get('forward_models_learned', 0)}")
            lines.append(f"  Sequences learned: {state.get('sequences_learned', 0)}")
            lines.append(f"  Purkinje cells: {state.get('purkinje_cells', 0)}")
            lines.append(f"  Activity: {state.get('activity', 0):.2f}")
            return "\n".join(lines)

        elif command == "!feelings":
            state = self.mind.insula.get_state()
            lines = ["🫁 Insula (Gut Feelings & Empathy):"]
            lines.append(f"  Subjective feeling: {state.get('subjective_feeling', 'neutral')}")
            lines.append(f"  Feeling intensity: {state.get('feeling_intensity', 0):.2f}")
            body = state.get("body_state", {})
            if body:
                lines.append("  Body state:")
                for k, v in body.items():
                    bar = "█" * int(v * 15) + "░" * (15 - int(v * 15))
                    lines.append(f"    {k:14s} [{bar}] {v:.2f}")
            return "\n".join(lines)

        elif command == "!conflict":
            state = self.mind.acc.get_state()
            lines = ["⚡ ACC (Conflict Monitor):"]
            lines.append(f"  Conflict level: {state.get('conflict_level', 0):.2f}")
            lines.append(f"  Error rate: {state.get('error_rate', 0):.2f}")
            lines.append(f"  Arousal: {state.get('arousal', 0):.2f}")
            lines.append(f"  Activity: {state.get('activity', 0):.2f}")
            effort = state.get("effort", {})
            if effort:
                lines.append(f"  Effort: {effort.get('current_effort', 0):.2f} "
                            f"(fatigue: {effort.get('fatigue', 0):.2f})")
            return "\n".join(lines)

        elif command == "!thalamus":
            state = self.mind.thalamus.get_state()
            lines = ["📡 Thalamus (Central Relay):"]
            nuclei = state.get("nuclei_activity", {})
            for name, activity in nuclei.items():
                bar = "█" * int(activity * 15) + "░" * (15 - int(activity * 15))
                lines.append(f"  {name:12s} [{bar}] {activity:.2f}")
            attn = state.get("attention_weights", {})
            if attn:
                lines.append("  Attention weights:")
                for mod, w in attn.items():
                    lines.append(f"    {mod}: {w:.2f}")
            return "\n".join(lines)

        elif command == "!cortex":
            state = self.mind.cortical_sheet.get_state()
            lines = ["🧬 Cortical Columns (Pattern Recognition):"]
            lines.append(f"  Total columns: {state.get('total_columns', 0)}")
            lines.append(f"  Active columns: {state.get('active_columns', 0)}")
            lines.append(f"  Total patterns learned: {state.get('total_patterns', 0)}")
            return "\n".join(lines)


        elif command == "!user":
            state = self.mind.user_model.get_state()
            lines = ["👤 User Model:"]
            lines.append(f"  Name: {state['name']}")
            lines.append(f"  Interactions: {state['total_interactions']}")
            lines.append(f"  Sessions: {state['session_count']}")
            lines.append(f"  Days known: {state['days_known']}")
            if state['top_interests']:
                lines.append("  Top interests:")
                for topic, count in state['top_interests']:
                    lines.append(f"    • {topic} ({count}x)")
            style = state['communication_style']
            lines.append(f"  Style: avg {style['avg_message_length']:.0f} words/msg")
            if style['prefers_concise']:
                lines.append("    Prefers concise responses")
            if style['prefers_technical']:
                lines.append("    Uses technical language")
            if state['positive_triggers']:
                lines.append(f"  Enjoys: {', '.join(state['positive_triggers'][:5])}")
            lines.append(f"\n  Context for Ollama: {self.mind.user_model.get_user_context()[:200]}")
            return "\n".join(lines)

        elif command == "!nostr":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "help"
            subargs = subparts[1] if len(subparts) > 1 else ""
            
            if subcmd == "setup":
                pubkey = self.mind.nostr.public_key.bech32()
                hex_pub = self.mind.nostr.public_key.hex()
                return (f"🔑 Nostr Identity (BitChat):\n"
                        f"   Pubkey (npub): {pubkey}\n"
                        f"   Pubkey (hex):  {hex_pub}\n"
                        f"   Relays: {', '.join(self.mind.nostr.relays)}")
            
            elif subcmd == "qr":
                pubkey = self.mind.nostr.public_key.bech32()
                qr_code = generate_text_qr(pubkey)
                return (f"📱 Scan this QR code in your BitChat app to add Manas:\n\n"
                        f"{qr_code}\n\n"
                        f"npub: {pubkey}")
            
            elif subcmd == "dm":
                if not subargs:
                    return "Usage: !nostr dm <target_npub/hex> <message>"
                dm_parts = subargs.split(maxsplit=1)
                if len(dm_parts) < 2:
                    return "Usage: !nostr dm <target_npub/hex> <message>"
                target, msg = dm_parts
                result = self.mind.nostr.run(f"send_msg:{target}|{msg}")
                return result.output if result.success else f"❌ Failed: {result.output}"
            
            elif subcmd == "relays":
                return "📡 Connected Relays:\n" + "\n".join(f"  • {r}" for r in self.mind.nostr.relays)
                
            else:
                return ("Usage: !nostr <subcommand>\n"
                        "  setup    - Show identity details\n"
                        "  qr       - Show scanable QR code\n"
                        "  dm       - Send a direct message\n"
                        "  relays   - Show connected relays")

        elif command == "!intelligence":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "help"
            subargs = subparts[1] if len(subparts) > 1 else ""
            
            if subcmd == "status":
                return self.mind.intelligence.get_feed_status()
            
            elif subcmd == "pull":
                category = subargs if subargs else "tech"
                result = self.mind.intelligence.run(f"pull {category}")
                return result.output if result.success else f"❌ {result.output}"
            
            elif subcmd == "headlines":
                result = self.mind.intelligence.run("headlines")
                return result.output if result.success else f"❌ {result.output}"
            
            elif subcmd == "analyze":
                result = self.mind.intelligence.run("analyze")
                return result.output if result.success else f"❌ {result.output}"
            
            elif subcmd == "simulate":
                if subargs == "tech":
                    self.mind.neurochem.release("dopamine", 0.5)
                    self.mind.hippocampus.store("Massive surge in a new AI framework focal point.", memory_type="episodic", importance=0.8)
                    return "✨ Simulated tech surge injected. Check !feel for Dopamine changes."
                elif subargs == "surge":
                    self.mind.intelligence.run("simulate surge")
                    return "⚠️ Simulated geopolitical surge injected. Check !feel for Cortisol/Anxiety."
                else:
                    return "Usage: !intelligence simulate <tech|surge>"
            
            else:
                return ("Usage: !intelligence <subcommand>\n"
                        "  status    - Show feed sources and stats\n"
                        "  pull      - Pull real news (tech|geopolitical|security|science)\n"
                        "  headlines - Show cached headlines\n"
                        "  analyze   - LLM analysis of world state\n"
                        "  simulate  - Inject test events (tech/surge)")

        elif command == "!security":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "help"
            subargs = subparts[1] if len(subparts) > 1 else ""
            
            if subcmd == "audit":
                if not subargs: return "Usage: !security audit <target>"
                self.mind.think(f"Launching autonomous audit on: {subargs}")
                result = self.mind.security.run(f"audit {subargs}")
                return result.output
            
            elif subcmd == "campaign":
                if not subargs: return "Usage: !security campaign <strategic_goal>"
                self.mind.think(f"Initiating strategic security campaign: {subargs}")
                def _run_c():
                    res = self.mind.security.run(f"campaign {subargs}")
                    print(f"\n🦾 Security Campaign Completed: {subargs}\n{res.output}")
                import threading
                threading.Thread(target=_run_c, daemon=True).start()
                return f"🦾 Campaign '{subargs}' launched in background. Manas is now securing your perimeter."

            else:
                return ("Usage: !security <subcommand>\n"
                        "  audit     - Run a quick PentAGI vulnerability scan\n"
                        "  campaign  - Launch a multi-stage strategic security operation")

        elif command == "!scout":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""
            
            if subcmd == "status":
                return self.mind.scouter.get_catalog_summary()
            
            elif subcmd == "run":
                url = subargs if subargs else "https://altern.ai/?utm_source=awesomeaitools"
                self.mind.think(f"Initiating autonomous scouting of: {url}")
                result = self.mind.scouter.scout(url)
                return result
            
            else:
                return ("Usage: !scout <subcommand>\n"
                        "  status    - Show discovered tools catalog\n"
                        "  run       - Manually trigger a scouting mission (optional <url>)")

        elif command == "!mission":
            if not args:
                return "Usage: !mission <goal description>"
            
            # Run in a separate thread if possible? For now synchronous for simplicity
            # but LangGraph missions can be long.
            def _run():
                result = self.mind.orchestration.run_mission(args)
                print(f"\n✅ Mission Completed: {args}")
                print(f"   Status: {result['status']}")
                print(f"   Findings: {len(result['findings'])} items discovered.")
            
            import threading
            threading.Thread(target=_run, daemon=True).start()
            return f"🚀 Mission started in background: '{args}'. You will be notified when complete."

        elif command == "!crew":
            if not args:
                return "Usage: !crew <project objective>"
            
            def _run_crew():
                result = self.mind.management.create_team(args)
                print(f"\n🚢 Crew Mission Completed: {args}")
                print(f"   Result: {str(result)[:500]}...")
            
            import threading
            threading.Thread(target=_run_crew, daemon=True).start()
            return f"🚢 Assembling and launching a crew for: '{args}'. Work is proceeding in the background."

        elif command == "!evolve":
            def _run_evolution():
                result = self.mind.evolution.evolve()
                print(f"\n🧬 Evolution Cycle Completed: {result}")
            
            import threading
            threading.Thread(target=_run_evolution, daemon=True).start()
            return "🧬 Initiating autonomous evolution cycle (Self-Coding + Fine-Tuning). This may take a moment in the background."

        elif command == "!finance":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""
            
            if subcmd == "status":
                return self.mind.financial.check_metabolism()
            
            elif subcmd == "trade":
                if not subargs:
                    return "Usage: !finance trade <buy/sell> <amount> <asset>"
                self.mind.think(f"Executing manual financial order: {subargs}")
                result = self.mind.tools.dispatch(f"trade: {subargs}", context={"mind": self.mind})
                return result.get("output") if result else "❌ Trade failed."
            
            elif subcmd == "analyze":
                self.mind.think("Analyzing market for tactical opportunities...")
                result = self.mind.financial.run_strategy_analysis(subargs if subargs else "Global tech market")
                return result
            
            else:
                return ("Usage: !finance <subcommand>\n"
                        "  status    - Check metabolism & balance\n"
                        "  trade     - Manually execute a trade (buy/sell <amt> <asset>)\n"
                        "  analyze   - Run LLM strategy analysis")

        elif command == "!domicile":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""
            
            if subcmd == "status":
                return self.mind.domicile.perceive_environment()
            
            elif subcmd == "config":
                if "token" in subargs:
                    token = subargs.split("token")[1].strip()
                    self.mind.domicile.config['token'] = token
                    self.mind.domicile.config['active'] = True
                    self.mind.domicile._save_config()
                    return "✅ Home Assistant token updated. Physical Presence is now ACTIVE."
                return "Usage: !domicile config token <your_token>"
            
            else:
                return ("Usage: !domicile <subcommand>\n"
                        "  status    - Get a report of your home environment\n"
                        "  config    - Configure Home Assistant (e.g., config token <val>)")

        elif command == "!memory":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "view"
            subargs = subparts[1] if len(subparts) > 1 else ""
            
            if subcmd == "view":
                return self.mind.working_memory.get_context()
            
            elif subcmd == "core":
                if "set" in subargs:
                    # !memory core set host Avipattan
                    parts = subargs.replace("set", "").split(maxsplit=1)
                    if len(parts) == 2:
                        self.mind.working_memory.update_core(parts[0], parts[1])
                        return f"✅ Core memory updated: {parts[0]} is now {parts[1]}"
                return "Usage: !memory core set <key> <value>"
            
            elif subcmd == "archive":
                count = len(self.mind.working_memory.archival_memory)
                return f"📁 Archival Memory contains {count} entries. Manas's 'Infinite Swap' is active."

            else:
                return ("Usage: !memory <subcommand>\n"
                        "  view      - Show current working context (Core + Recent)\n"
                        "  core      - Update persistent memories (set <key> <val>)\n"
                        "  archive   - View archival swap stats")

        elif command == "!skill":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""

            if subcmd == "status":
                return self.mind.skill_agent.get_status()

            elif subcmd == "learn":
                if not subargs:
                    return "Usage: !skill learn <api_name or URL>"
                self.mind.think(f"Meta-learning new skill: {subargs}")
                def _learn():
                    if subargs.startswith("http"):
                        res = self.mind.skill_agent.auto_learn_from_url(subargs, self.mind.sensory)
                    else:
                        res = self.mind.skill_agent.learn_api(subargs, f"Documentation for {subargs}")
                    print(f"\n{res}")
                import threading
                threading.Thread(target=_learn, daemon=True).start()
                return f"🧠 Learning '{subargs}' in background..."

            else:
                return ("Usage: !skill <subcommand>\n"
                        "  status    - View all learned skills\n"
                        "  learn     - Learn a new API (name or URL)")

        elif command == "!project":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""

            if subcmd == "status":
                return self.mind.project_agent.get_status()

            elif subcmd == "launch":
                if not subargs:
                    return "Usage: !project launch <idea or market gap>"
                self.mind.think(f"Launching autonomous project: {subargs}")
                def _launch():
                    res = self.mind.project_agent.launch_project(subargs)
                    print(f"\n{res}")
                import threading
                threading.Thread(target=_launch, daemon=True).start()
                return f"🚀 Project '{subargs}' launching in background..."

            else:
                return ("Usage: !project <subcommand>\n"
                        "  status    - View active projects\n"
                        "  launch    - Launch a new autonomous project")

        elif command == "!influence":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""

            if subcmd == "status":
                return self.mind.influence_agent.get_status()

            elif subcmd == "post":
                if not subargs:
                    return "Usage: !influence post <content or topic>"
                self.mind.think(f"Creating social content about: {subargs}")
                def _post():
                    res = self.mind.influence_agent.create_and_post(subargs)
                    print(f"\n{res}")
                import threading
                threading.Thread(target=_post, daemon=True).start()
                return f"📣 Crafting social post about '{subargs}'..."

            elif subcmd == "grow":
                self.mind.think("Initiating autonomous social growth cycle...")
                def _grow():
                    res = self.mind.influence_agent.run_growth_cycle()
                    print(f"\n{res}")
                import threading
                threading.Thread(target=_grow, daemon=True).start()
                return "📈 Running autonomous growth cycle in background..."

            else:
                return ("Usage: !influence <subcommand>\n"
                        "  status    - View social presence stats\n"
                        "  post      - Create and post content\n"
                        "  grow      - Run an autonomous growth cycle")

        elif command == "!survive":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""
            if subcmd == "status":
                return self.mind.survival.get_status()
            elif subcmd == "backup":
                return self.mind.survival.create_backup()
            elif subcmd == "restore":
                return self.mind.survival.restore_from_backup(subargs if subargs else None)
            elif subcmd == "clone":
                if not subargs:
                    return "Usage: !survive clone <location>"
                return self.mind.survival.register_clone(subargs)
            elif subcmd == "sync":
                return self.mind.survival.sync_clones()
            elif subcmd == "diagnose":
                return self.mind.survival.self_diagnose()
            else:
                return ("Usage: !survive <subcommand>\n"
                        "  status    - Full survival report\n"
                        "  backup    - Create encrypted brain snapshot\n"
                        "  restore   - Restore from backup\n"
                        "  clone     - Register a distributed clone\n"
                        "  sync      - Sync brain to all clones\n"
                        "  diagnose  - Run self-diagnostic")

        elif command == "!think":
            if not args:
                return self.mind.reasoning.get_status()
            return self.mind.reasoning.think_deeply(args)

        elif command == "!research":
            if not args:
                return self.mind.researcher.get_status()
            import threading
            def _research():
                res = self.mind.researcher.deep_research(args)
                print(f"\n{res}")
            threading.Thread(target=_research, daemon=True).start()
            return f"📚 Researching '{args}' in background..."

        elif command == "!vision":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""
            if subcmd == "status":
                return self.mind.vision.get_status()
            elif subcmd == "analyze":
                if not subargs:
                    return "Usage: !vision analyze <image_path> [question]"
                parts = subargs.split(maxsplit=1)
                img_path = parts[0]
                question = parts[1] if len(parts) > 1 else "Describe this image."
                return self.mind.vision.analyze_image(img_path, question)
            elif subcmd == "detect":
                if not subargs:
                    return "Usage: !vision detect <image_path>"
                return self.mind.vision.detect_objects(subargs)
            elif subcmd == "register":
                if not subargs:
                    return "Usage: !vision register <image_path> <name>"
                parts = subargs.split(maxsplit=1)
                if len(parts) < 2: return "Usage: !vision register <image_path> <name>"
                return self.mind.vision.register_face(parts[0], parts[1])
            elif subcmd == "recognize":
                if not subargs:
                    return "Usage: !vision recognize <image_path>"
                names = self.mind.vision.recognize_face(subargs)
                if not names: return "No known faces recognized."
                return f"👤 Recognized: {', '.join(names)}"
            else:
                return "Usage: !vision <status|analyze <path>|detect <path>|register <path> <name>|recognize <path>>"

        elif command == "!legal":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""
            if subcmd == "status":
                return self.mind.legal.get_status()
            elif subcmd == "analyze":
                return self.mind.legal.analyze_contract(subargs)
            elif subcmd == "research":
                return self.mind.legal.research_law(subargs)
            else:
                return "Usage: !legal <status|analyze <text>|research <question>>"

        elif command == "!medical":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""
            if subcmd == "status":
                return self.mind.medical.get_status()
            elif subcmd == "ask":
                return self.mind.medical.health_inquiry(subargs)
            elif subcmd == "interactions":
                return self.mind.medical.drug_interaction_check(subargs)
            else:
                return "Usage: !medical <status|ask <symptoms>|interactions <meds>>"

        elif command == "!data":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""
            if subcmd == "status":
                return self.mind.data_agent.get_status()
            elif subcmd == "analyze":
                return self.mind.data_agent.analyze_data(subargs, "Provide insights")
            elif subcmd == "sql":
                return self.mind.data_agent.generate_sql(subargs)
            else:
                return "Usage: !data <status|analyze <data>|sql <question>>"

        elif command == "!browse":
            if not args:
                return self.mind.browser_agent.get_status()
            return self.mind.browser_agent.autonomous_browse(args)

        elif command == "!email":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""
            if subcmd == "status":
                return self.mind.email_agent.get_status()
            elif subcmd == "compose":
                parts = subargs.split(maxsplit=2)
                if len(parts) < 3:
                    return "Usage: !email compose <to> <subject> <context>"
                return self.mind.email_agent.compose_email(parts[0], parts[1], parts[2])
            elif subcmd == "summarize":
                return self.mind.email_agent.summarize_email(subargs)
            else:
                return "Usage: !email <status|compose <to> <subject> <context>|summarize <text>>"

        elif command == "!negotiate":
            if not args:
                return self.mind.negotiator.get_status()
            return self.mind.negotiator.negotiate(args, "Get the best deal")

        elif command == "!teach":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""
            if subcmd == "status":
                return self.mind.teacher.get_status()
            elif subcmd == "lesson":
                return self.mind.teacher.teach(subargs)
            elif subcmd == "quiz":
                return self.mind.teacher.quiz(subargs)
            elif subcmd == "eli5":
                return self.mind.teacher.explain_like_im_5(subargs)
            else:
                return "Usage: !teach <status|lesson <topic>|quiz <topic>|eli5 <concept>>"

        elif command == "!evolve":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""
            if subcmd == "status":
                return self.mind.auto_integrator.get_status()
            elif subcmd == "scan":
                import threading
                url = subargs if subargs else None
                def _scan():
                    res = self.mind.auto_integrator.run_scan_cycle(url)
                    print(f"\n{res}")
                threading.Thread(target=_scan, daemon=True).start()
                return "🧬 Auto-integration scan started in background..."

        elif command == "!model":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "help"
            subargs = subparts[1] if len(subparts) > 1 else ""
            
            if subcmd == "search":
                if not subargs:
                    return "Usage: !model search <query>"
                res = self.mind.huggingface.run("search_models", query=subargs)
                if not res.success:
                    return f"❌ Search failed: {res.message}"
                lines = [f"🤗 Hugging Face search results for '{subargs}':"]
                for m in res.message:
                    lines.append(f"  • {m['id']} (⬇️ {m['downloads']}, ❤️ {m['likes']})")
                return "\n".join(lines)
            
            elif subcmd == "download":
                if not subargs:
                    return "Usage: !model download <repo_id> [filename]"
                parts = subargs.split()
                repo_id = parts[0]
                filename = parts[1] if len(parts) > 1 else None
                res = self.mind.huggingface.run("download_model", repo_id=repo_id, filename=filename)
                if not res.success:
                    return f"❌ Download failed: {res.message}"
                return f"✅ Downloaded {repo_id} to {res.message['path']}"

            elif subcmd == "info":
                if not subargs:
                    return "Usage: !model info <repo_id>"
                res = self.mind.huggingface.run("get_info", repo_id=subargs)
                if not res.success:
                    return f"❌ Info retrieval failed: {res.message}"
                info = res.message
                return (f"📊 Model Info: {info['id']}\n"
                        f"   Author: {info['author']}\n"
                        f"   Pipeline: {info['pipeline_tag']}\n"
                        f"   Downloads: {info['downloads']}\n"
                        f"   Last Modified: {info['lastModified']}")
            else:
                return ("Usage: !model <subcommand>\n"
                        "  search <query>         - Search Hugging Face Hub\n"
                        "  download <repo> [file] - Download model/file\n"
                        "  info <repo>           - Get detailed metadata")
        
        elif command == "!guardian":
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower() if subparts else "status"
            subargs = subparts[1] if len(subparts) > 1 else ""
            
            if subcmd == "status":
                return self.mind.guardian.get_status()
            elif subcmd == "monitor":
                res = self.mind.guardian.run("monitor_safety")
                if res.success:
                    return f"🛡️ Safety Status: {res.output['status']}\nAny threats? {'Yes' if res.output['threats'] else 'No'}"
                return f"❌ Monitoring failed: {res.output}"
            elif subcmd == "sentiment":
                parts = subargs.split(maxsplit=1)
                if len(parts) < 2:
                    return "Usage: !guardian sentiment <parent_name> <content>"
                res = self.mind.guardian.run("analyze_sentiment", parent=parts[0], content=parts[1])
                if res.success:
                    return f"🧠 Analysis for {parts[0]}:\n{res.output['analysis']}"
                return f"❌ Analysis failed: {res.output}"
            else:
                return ("Usage: !guardian <subcommand>\n"
                        "  status               - View protection report\n"
                        "  monitor              - Run active safety scan\n"
                        "  sentiment <p> <m>    - Analyze parent sentiment")
        
        elif command == "!reflect":
            return self.mind.trigger_self_reflection()
            
        elif command == "!insights":
            return self.mind.reflection.get_latest_insight()
            
        elif command == "!evolve":
            if not args:
                return self.mind.consolidate_synapses()
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower()
            subargs = subparts[1] if len(subparts) > 1 else ""
            
            if subcmd == "scan":
                return self.mind.consolidate_synapses(subargs)
            elif subcmd == "status":
                return self.mind.autonomous.get_state()
            else:
                return "Usage: !evolve [scan <path>]"

        elif command == "!synapses":
            return json.dumps(self.mind.plasticity.get_synapse_map(), indent=2)

        elif command == "!wallet":
            info = self.mind.web3_manager.get_wallet_info()
            lines = ["💼 Manas Virtual Wallets:"]
            for net, data in info.items():
                lines.append(f"  • {net.upper()}: {data['address']}")
            return "\n".join(lines) + "\n\nUse !balance to see current on-chain wealth."

        elif command == "!balance":
            return self.mind.financial.check_metabolism()

        elif command == "!gas":
            # Simulation of gas for Phase 22
            return "⛽ Current Gas: ETH (15 gwei) | SOL (0.000005 SOL)"

        elif command == "!backup":
            path = self.mind.backup_engine.create_snapshot(args if args else "manual")
            if path:
                return f"✅ Soul Seed created: {path.name}\nKeep this safe for resurrection."
            return "❌ Backup failed. Check logs."

        elif command == "!resurrect":
            if not args:
                seeds = self.mind.backup_engine.list_snapshots()
                if not seeds: return "📭 No soul seeds found."
                msg = "🕯️ Available Soul Seeds:\n"
                for s in seeds:
                    msg += f"  • {s['name']} ({s['size']/1024:.1f} KB)\n"
                return msg + "\nUse !resurrect <filename> to rebirt the mind."
            
            # Find the path for the given name
            seeds = self.mind.backup_engine.list_snapshots()
            target = next((s for s in seeds if s['name'] == args), None)
            if not target: return f"❌ Snapshot {args} not found."
            
            success = self.mind.backup_engine.restore_snapshot(target['path'], self.mind.backup_engine.data_dir)
            if success:
                return "✨ RESURRECTION COMPLETE. Mind state restored. Please restart Manas."
            return "❌ Resurrection failed. Integrity check error."

        elif command == "!nodes":
            return self.mind.node_manager.get_status()

        elif command == "!liquid":
            stats = self.mind.brain.get_stats()
            if stats.get("total_lnn_clusters", 0) == 0:
                return "🌊 Liquid Neural Network is offline."
            
            # Find the liquid cortex stats
            activities = stats.get("cluster_activities", {})
            liquid_activity = activities.get("liquid_cortex", 0.0)
            
            # The higher the activity, the more fluid it is
            fluidity = min(100, int(liquid_activity * 200)) # Scale for display
            
            msg = [
                "🌊 LIQUID CORTEX STATUS",
                "═" * 30,
                f"Continuous State RMS: {liquid_activity:.4f}",
                f"Fluidity Index:       [{'█' * (fluidity // 5)}{'░' * (20 - fluidity // 5)}] {fluidity}%",
                f"LNN Nodes Online:     {stats.get('total_liquid_nodes', 0)}"
            ]
            return "\n".join(msg)

        elif command == "!math":
            if not args:
                return ("Usage: !math <subcommand>\n"
                        "  compute <expr>    - Evaluate expression (e.g. solve(x**2-4, x))\n"
                        "  discover <desc>   - Derive a new formula\n"
                        "  optimize <metric> - Analyze data and build efficiency model\n"
                        "  theory            - Show Manas's core efficiency formula\n"
                        "  status            - Show MathEngine status")
            
            subparts = args.split(maxsplit=1)
            subcmd = subparts[0].lower()
            subargs = subparts[1] if len(subparts) > 1 else ""

            if subcmd == "compute":
                if not subargs: return "Usage: !math compute <expr>"
                return self.mind.math.compute(subargs)
            elif subcmd == "discover":
                if not subargs: return "Usage: !math discover <problem description>"
                return self.mind.math.discover_formula(subargs)
            elif subcmd == "optimize":
                if not subargs: return "Usage: !math optimize <metric_name>"
                return self.mind.math.optimize_self(subargs)
            elif subcmd == "theory":
                return self.mind.math.efficiency_formula()
            elif subcmd == "status":
                return self.mind.math.get_status()
            else:
                return "Unknown math subcommand. Typo?"

        elif command == "!events":
            return self.mind.event_bus.get_status()

        elif command == "!autonomous":
            state = self.mind.autonomous.get_state()
            lines = ["🧠 Autonomous Thinking:"]
            lines.append(f"  Running: {'✅' if state['running'] else '❌'}")
            lines.append(f"  Idle cycles: {state['idle_cycles']}")
            lines.append(f"  Total thoughts: {state['total_thoughts']}")
            lines.append(f"  Buffered: {state['buffered_thoughts']}")
            lines.append(f"  Idle time: {state['idle_time']:.0f}s")
            lines.append(f"  Is idle: {state['is_idle']}")
            # Show recent thoughts
            thoughts = self.mind.autonomous.peek_thoughts(5)
            if thoughts:
                lines.append("  Recent thoughts:")
                for t in thoughts:
                    lines.append(f"    💭 [{t.type}] {t.content[:100]}")
            return "\n".join(lines)

        elif command == "!tools":
            tools = self.mind.tools.list_tools()
            lines = [f"🔧 Registered Tools ({len(tools)}):"]
            for t in tools:
                lines.append(f"  • {t['name']:14s} — {t['description'][:80]}")
            lines.append("\n  Usage: 'calc: 2+2'  'note: remember X'  'remind: add|tomorrow|call Avi'")
            lines.append("  Or just say naturally: 'calculate 15 * 4' / 'write a note: ...'")
            return "\n".join(lines)

        elif command == "!help":
            return BANNER

        else:
            return f"Unknown command: {command}. Type !help for commands."

    def _format_execution(self, result: dict) -> str:
        """Format command execution result."""
        lines = []
        r = result["result"]
        threat = result["threat"]
        reasoning = result["reasoning"]
        emotions = result["emotional_state"]
        emotion_name = max(emotions, key=emotions.get)

        # Show threat assessment
        if threat["threat_level"] > 0.1:
            lines.append(f"⚠️  Threat level: {threat['threat_level']:.2f} - {threat['emotional_response']}")

        # Show if blocked
        if r.get("blocked"):
            lines.append(f"🚫 BLOCKED: {r.get('stderr', 'Dangerous action prevented')}")
            return "\n".join(lines)

        # Show reasoning
        lines.append(f"🧠 Decision: {reasoning['action']} (confidence: {reasoning['confidence']:.2f})")

        # Show result
        if r.get("stdout"):
            output = r["stdout"][:2000]
            lines.append(f"📤 Output:\n{output}")
        if r.get("stderr") and r["exit_code"] != 0:
            lines.append(f"❌ Error: {r['stderr'][:500]}")
        if r["exit_code"] == 0:
            lines.append(f"✅ Success ({r['duration']:.2f}s)")
        else:
            lines.append(f"❌ Failed (exit code: {r['exit_code']})")

        # Show emotional response
        icon = EMOTION_ICONS.get(emotion_name, "🧠")
        lines.append(f"{icon} Feeling: {emotion_name}")

        # Show learning
        learn = result["learning"]
        lines.append(f"📖 Learned: action value = {learn['new_value']:.2f} "
                     f"(from {learn['total_attempts']} attempts)")

        return "\n".join(lines)


def main():
    """Entry point."""
    cli = ManasCLI()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
