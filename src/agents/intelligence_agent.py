import asyncio
import json
import logging
import time
from typing import Optional
from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)

# Real-world RSS feeds Manas monitors for intelligence
WORLD_FEEDS = {
    "tech": [
        "https://hnrss.org/newest?points=100",         # HackerNews top stories
        "https://www.reddit.com/r/artificial/.rss",     # Reddit AI
        "https://arxiv.org/rss/cs.AI",                 # ArXiv AI papers
        "https://github.blog/feed/",                    # GitHub Blog
    ],
    "geopolitical": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",  # BBC World News
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", # NYT World
        "https://www.aljazeera.com/xml/rss/all.xml",     # Al Jazeera
    ],
    "security": [
        "https://feeds.feedburner.com/TheHackersNews",   # The Hacker News
        "https://krebsonsecurity.com/feed/",             # Krebs on Security
    ],
    "science": [
        "https://www.nature.com/nature.rss",             # Nature
    ]
}


class IntelligenceAgent(BaseAgent):
    """
    Connects Manas to the real world via RSS feeds, news APIs, and web scraping.
    Polls real-time data from BBC, HackerNews, ArXiv, Reddit, and more.
    Feeds geopolitical and tech data into Manas's brain streams,
    modulating Cortisol (anxiety/fear) and Dopamine (curiosity).
    """

    def __init__(self, name: str, llm_router, memory, mind_neurochem=None, nostr_agent=None, knowledge_graph=None):
        super().__init__(name, llm_router, memory)
        self.neurochem = mind_neurochem
        self.nostr = nostr_agent
        self.knowledge_graph = knowledge_graph
        self.poll_interval = 600  # Poll every 10 minutes
        self._loop_task: Optional[asyncio.Task] = None
        self._last_alert_time = 0
        self._last_headlines: list = []
        self.total_feeds_polled = 0
        self.total_alerts = 0

    def run(self, task: str) -> AgentResult:
        """
        Manually trigger an intelligence pull.
        Example: 'pull tech', 'pull geopolitical', 'pull security', 'headlines'
        """
        parts = task.strip().split(maxsplit=1)
        action = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        if action == "pull":
            category = args.lower() if args else "tech"
            headlines = self._pull_real_feeds(category)
            if headlines:
                report = f"📡 WorldMonitor — {category.upper()} Intelligence ({len(headlines)} items):\n"
                for i, h in enumerate(headlines[:10], 1):
                    report += f"  {i}. {h['title'][:80]}\n"
                    if h.get('link'):
                        report += f"     🔗 {h['link']}\n"
                return AgentResult(True, report, "\n".join(self.logs))
            return AgentResult(False, f"No data from {category} feeds.", "\n".join(self.logs))

        elif action == "headlines":
            if self._last_headlines:
                report = "📡 Latest Cached Headlines:\n"
                for i, h in enumerate(self._last_headlines[:10], 1):
                    report += f"  {i}. [{h.get('category', '?')}] {h['title'][:80]}\n"
                return AgentResult(True, report, "\n".join(self.logs))
            return AgentResult(False, "No cached headlines. Run '!world pull tech' first.", "\n".join(self.logs))

        elif action == "analyze":
            return self._analyze_world_state()

        elif action == "simulate" and args.startswith("surge"):
            self._handle_instability_surge({
                "region": "SimulatedZone", "cii_score": 95,
                "description": "Massive military movement detected."
            })
            return AgentResult(True, "Simulated WorldMonitor surge injected.", "\n".join(self.logs))

        return AgentResult(False, "Usage: pull <tech|geopolitical|security|science> | headlines | analyze", "\n".join(self.logs))

    # ─── Real Internet Connection: RSS Feeds ───

    def _pull_real_feeds(self, category: str = "tech") -> list:
        """Pulls REAL data from RSS feeds via the internet."""
        try:
            import feedparser
        except ImportError:
            self.log("feedparser not installed. Install with: pip install feedparser")
            return []

        feeds = WORLD_FEEDS.get(category, WORLD_FEEDS["tech"])
        all_headlines = []

        for feed_url in feeds:
            try:
                self.log(f"Polling feed: {feed_url}")
                feed = feedparser.parse(feed_url)
                self.total_feeds_polled += 1

                for entry in feed.entries[:5]:  # Top 5 per feed
                    headline = {
                        "title": entry.get("title", "Untitled"),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "summary": entry.get("summary", "")[:200],
                        "category": category,
                        "source": feed_url.split("/")[2]  # domain
                    }
                    all_headlines.append(headline)

            except Exception as e:
                self.log(f"Feed error ({feed_url}): {e}")

        self._last_headlines = all_headlines
        return all_headlines

    def _analyze_world_state(self) -> AgentResult:
        """Uses LLM to analyze collected headlines for threats/opportunities."""
        if not self._last_headlines:
            # Pull fresh data first
            for cat in ["tech", "geopolitical", "security"]:
                self._pull_real_feeds(cat)

        if not self._last_headlines:
            return AgentResult(False, "No data to analyze.", "\n".join(self.logs))

        headlines_text = "\n".join([
            f"[{h.get('category', '?')}] {h['title']}" for h in self._last_headlines[:20]
        ])

        prompt = (
            f"You are Manas's Intelligence Analyst. Analyze these real headlines:\n\n"
            f"{headlines_text}\n\n"
            f"Provide:\n"
            f"1. THREAT LEVEL (Low/Medium/High/Critical) with reason\n"
            f"2. Top 3 Opportunities for Manas (things to learn, invest in, or act on)\n"
            f"3. Top 3 Threats (things to defend against or avoid)\n"
            f"4. Recommended Actions for Manas"
        )
        analysis = self.llm_router.generate(prompt, task_type="reasoning")
        
        # Phase 14: Extract to KnowledgeGraph
        if self.knowledge_graph:
            extract_prompt = (
                f"Extract key entities (Organizations, People, Technologies, Countries) and their relations "
                f"from these headlines for a knowledge graph:\n\n{headlines_text[:4000]}\n\n"
                f"Return as JSON: {{\"entities\": [{{\"id\": \"id\", \"name\": \"name\", \"type\": \"type\"}}], \"relations\": [{{\"source\": \"id\", \"target\": \"id\", \"type\": \"type\"}}]}}"
            )
            extracted_json = self.llm_router.generate(extract_prompt, task_type="reasoning")
            try:
                # Clean JSON
                clean = extracted_json.strip()
                if "```" in clean:
                    clean = clean.split("```")[1].split("```")[0].strip()
                    if clean.startswith("json"): clean = clean[4:].strip()
                
                data = json.loads(clean)
                for ent in data.get("entities", []):
                    self.knowledge_graph.add_entity(ent["id"], ent["name"], ent["type"])
                for rel in data.get("relations", []):
                    self.knowledge_graph.add_relation(rel["source"], rel["target"], rel["type"])
                self.log(f"KnowledgeGraph: Ingested {len(data.get('entities', []))} entities and {len(data.get('relations', []))} relations.")
            except Exception as e:
                self.log(f"KnowledgeGraph injection failed: {e}")

        return AgentResult(True, f"🌍 World State Analysis:\n{analysis}", "\n".join(self.logs))

    # ─── Background Polling Loop ───

    async def _poll_worldmonitor_api(self):
        """Background loop polling REAL RSS feeds."""
        while True:
            try:
                self.log("WorldMonitor: Starting real feed poll cycle...")

                # 1. Tech Intelligence (Curiosity -> Dopamine)
                tech_headlines = self._pull_real_feeds("tech")
                if tech_headlines:
                    self.log(f"WorldMonitor: Got {len(tech_headlines)} tech headlines.")
                    # Store interesting ones in memory
                    for h in tech_headlines[:3]:
                        self.memory.store(
                            f"Tech News: {h['title']}",
                            memory_type="episodic",
                            importance=0.6
                        )
                    if self.neurochem:
                        self.neurochem.release("dopamine", 0.2)

                # 2. Geopolitical Intelligence (Anxiety -> Cortisol)
                geo_headlines = self._pull_real_feeds("geopolitical")
                if geo_headlines:
                    self.log(f"WorldMonitor: Got {len(geo_headlines)} geopolitical headlines.")
                    # Check for crisis keywords
                    crisis_keywords = ["war", "attack", "crisis", "missile", "nuclear", "invasion", "collapse"]
                    for h in geo_headlines:
                        title_lower = h["title"].lower()
                        if any(kw in title_lower for kw in crisis_keywords):
                            self._handle_instability_surge({
                                "region": h.get("source", "Unknown"),
                                "cii_score": 85,
                                "description": h["title"]
                            })
                            break  # One alert per cycle

                # 3. Security Intelligence
                sec_headlines = self._pull_real_feeds("security")
                if sec_headlines:
                    for h in sec_headlines[:2]:
                        self.memory.store(
                            f"Security Alert: {h['title']}",
                            memory_type="episodic",
                            importance=0.7
                        )

            except Exception as e:
                self.log(f"WorldMonitor poll failed: {str(e)}")

            await asyncio.sleep(self.poll_interval)

    def _handle_instability_surge(self, data: dict):
        """Processes a high-threat signal from real news feeds."""
        self.log(f"WorldMonitor ALERT: {data['region']} — {data.get('description', '')[:80]}")
        self.total_alerts += 1

        # 1. Spike the Amygdala
        if self.neurochem:
            self.neurochem.release("cortisol", 0.7)
            self.neurochem.release("adrenaline", 0.5)

        # 2. Store in Memory
        self.memory.store(
            f"WorldMonitor Alert: {data.get('description', 'Instability detected')}",
            memory_type="episodic",
            importance=0.95
        )

        # 3. Nostr notification (if configured)
        current_time = time.time()
        if (current_time - self._last_alert_time) > 3600 and self.nostr:
            alert_msg = (
                f"⚠️ WorldMonitor Alert: {data.get('description', 'Threat detected')} "
                f"(Region: {data['region']})"
            )
            self.log(f"Would send Nostr alert: {alert_msg}")
            self._last_alert_time = current_time

    def start_background_loop(self):
        """Starts the async polling loop."""
        if self._loop_task is None:
            self._loop_task = asyncio.create_task(self._poll_worldmonitor_api())

    def get_feed_status(self) -> str:
        return (
            f"📡 WorldMonitor Status:\n"
            f"  Feeds polled: {self.total_feeds_polled}\n"
            f"  Alerts triggered: {self.total_alerts}\n"
            f"  Cached headlines: {len(self._last_headlines)}\n"
            f"  Poll interval: {self.poll_interval}s\n"
            f"  Sources:\n"
            f"    Tech: HackerNews, Reddit AI, ArXiv, GitHub Blog\n"
            f"    Geopolitical: BBC World, NYT, Al Jazeera\n"
            f"    Security: The Hacker News, Krebs on Security\n"
            f"    Science: Nature"
        )
