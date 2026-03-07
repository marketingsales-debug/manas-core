"""
Sensory System - Internal sensory organs of the Manas brain.

Humans have 5 senses that feed information to the brain:
- Eyes (vision) -> see web pages, read content
- Ears (hearing) -> listen to news feeds, data streams
- Touch (tactile) -> interact with the filesystem, feel the system
- Nose (smell) -> detect anomalies, sniff for problems
- Proprioception -> awareness of own state, system health

Each sense is an INTERNAL brain subsystem (NOT an external agent) that:
1. Gathers raw data from the world (internet, filesystem, system)
2. Feeds it into Manas's spiking neural network via the thalamus
3. Triggers emotional responses based on what it finds
4. Stores important findings in hippocampal memory

These are built-in sensory organs, like real senses — not external calls.
"""

import time
import requests
import os
import psutil
from pathlib import Path
from typing import Optional, Callable

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


class SensoryEvent:
    """A single sensory event — what a sense organ detected."""

    def __init__(
        self,
        sense: str,
        event_type: str,
        content: str,
        source: str,
        intensity: float = 0.5,
        valence: float = 0.0,
        novelty: float = 0.5,
        metadata: dict = None,
    ):
        self.sense = sense              # which sense detected this
        self.event_type = event_type    # what kind of thing
        self.content = content          # the actual data
        self.source = source            # where it came from
        self.intensity = intensity      # how strong the signal (0-1)
        self.valence = valence          # positive or negative (-1 to 1)
        self.novelty = novelty          # how new (0-1)
        self.metadata = metadata or {}
        self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "sense": self.sense,
            "event_type": self.event_type,
            "content": self.content[:500],
            "source": self.source,
            "intensity": self.intensity,
            "valence": self.valence,
            "novelty": self.novelty,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class VisionSystem:
    """
    EYES — Internal visual processing subsystem.

    Like human vision:
    - Scans web pages (seeing)
    - Reads articles (reading comprehension)
    - Notices headlines (attention to important things)
    - Searches for information (looking around)
    """

    def __init__(self, sensory_processing_ref=None):
        self.name = "vision"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Manas-Vision/0.1 (Cognitive AI Sensory Agent)"
        })
        self.pages_seen = 0
        self.sensory_processing_ref = sensory_processing_ref

    def look_at_real_world(self) -> list[SensoryEvent]:
        """Capture a frame from the actual webcam and analyze it."""
        events = []
        if self.sensory_processing_ref:
            try:
                # Capture and analyze what the webcam sees
                analysis = self.sensory_processing_ref.analyze_camera("Describe what you see in this webcam frame briefly but accurately.")
                if analysis and not analysis.startswith("[Error"):
                    events.append(SensoryEvent(
                        sense="vision",
                        event_type="webcam_sight",
                        content=analysis,
                        source="webcam",
                        intensity=0.7,
                        novelty=0.8,
                    ))
            except Exception as e:
                events.append(SensoryEvent(
                    sense="vision",
                    event_type="error",
                    content=f"Camera capture failed: {e}",
                    source="webcam",
                    valence=-0.3,
                ))
        return events

    def search(self, query: str, max_results: int = 5) -> list[SensoryEvent]:
        """Search the web — like looking around."""
        events = []
        try:
            resp = self.session.get(
                "https://lite.duckduckgo.com/lite/",
                params={"q": query},
                timeout=10,
            )
            if HAS_BS4 and resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")

                # Extract result links and snippets
                for link in soup.find_all("a", class_="result-link")[:max_results]:
                    title = link.get_text(strip=True)
                    url = link.get("href", "")
                    if title and url:
                        events.append(SensoryEvent(
                            sense="vision",
                            event_type="search_result",
                            content=title,
                            source=url,
                            intensity=0.5,
                            novelty=0.7,
                            metadata={"query": query},
                        ))
        except Exception as e:
            events.append(SensoryEvent(
                sense="vision",
                event_type="error",
                content=f"Search failed: {str(e)}",
                source="duckduckgo",
                intensity=0.3,
                valence=-0.3,
            ))
        return events

    def read_page(self, url: str) -> SensoryEvent:
        """Read a web page — like reading a book."""
        try:
            resp = self.session.get(url, timeout=10)
            if HAS_BS4:
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                content = "\n".join(lines)[:5000]
                title = soup.title.string if soup.title else url
            else:
                content = resp.text[:5000]
                title = url

            self.pages_seen += 1
            return SensoryEvent(
                sense="vision",
                event_type="page_content",
                content=content,
                source=url,
                intensity=0.6,
                novelty=0.6,
                metadata={"title": title, "length": len(content)},
            )
        except Exception as e:
            return SensoryEvent(
                sense="vision",
                event_type="error",
                content=str(e),
                source=url,
                intensity=0.3,
                valence=-0.3,
            )

    def scan_news(self, topic: str = "technology") -> list[SensoryEvent]:
        """Scan news headlines — like glancing at a newspaper."""
        return self.search(f"{topic} news today", max_results=5)

    def learn_topic(self, topic: str) -> list[SensoryEvent]:
        """Deep dive into a topic — search, read, understand."""
        events = []

        # First, search
        search_results = self.search(topic, max_results=3)
        events.extend(search_results)

        # Then read the top results
        for result in search_results[:2]:
            url = result.source
            if url and url.startswith("http"):
                page_event = self.read_page(url)
                events.append(page_event)

        return events


class HearingSystem:
    """
    EARS — Internal auditory processing subsystem.

    Like human hearing:
    - Listens to RSS feeds (ongoing data streams)
    - Monitors APIs for changes (hearing alerts)
    - Picks up on trending topics (hearing what everyone talks about)
    """

    def __init__(self, sensory_processing_ref=None):
        self.name = "hearing"
        self.session = requests.Session()
        self.feeds_monitored = 0
        self.sensory_processing_ref = sensory_processing_ref

    def listen_to_real_world(self, duration_sec: int = 4) -> list[SensoryEvent]:
        """Record audio from the actual microphone and transcribe it."""
        events = []
        if self.sensory_processing_ref:
            try:
                transcription = self.sensory_processing_ref.listen_and_transcribe(duration_sec=duration_sec)
                if transcription and not transcription.startswith("[") and transcription.strip():
                    events.append(SensoryEvent(
                        sense="hearing",
                        event_type="microphone_audio",
                        content=f"Heard: {transcription}",
                        source="microphone",
                        intensity=0.8,
                        novelty=0.9,
                    ))
            except Exception as e:
                events.append(SensoryEvent(
                    sense="hearing",
                    event_type="error",
                    content=f"Microphone recording failed: {e}",
                    source="microphone",
                    valence=-0.3,
                ))
        return events

    def listen_to_feed(self, url: str) -> list[SensoryEvent]:
        """Listen to an RSS/Atom feed."""
        events = []
        try:
            resp = self.session.get(url, timeout=10)
            if HAS_BS4:
                soup = BeautifulSoup(resp.text, "xml")
                items = soup.find_all("item") or soup.find_all("entry")
                for item in items[:10]:
                    title = item.find("title")
                    desc = item.find("description") or item.find("summary")
                    link = item.find("link")

                    content = ""
                    if title:
                        content = title.get_text(strip=True)
                    if desc:
                        content += f" - {desc.get_text(strip=True)[:200]}"

                    events.append(SensoryEvent(
                        sense="hearing",
                        event_type="feed_item",
                        content=content,
                        source=link.get_text(strip=True) if link else url,
                        intensity=0.4,
                        novelty=0.6,
                        metadata={"feed": url},
                    ))
            self.feeds_monitored += 1
        except Exception as e:
            events.append(SensoryEvent(
                sense="hearing",
                event_type="error",
                content=f"Feed listen failed: {str(e)}",
                source=url,
                valence=-0.2,
            ))
        return events

    def hear_trending(self) -> list[SensoryEvent]:
        """What's trending? Like hearing what everyone is talking about."""
        events = []
        try:
            # Use HackerNews API (free, no key needed)
            resp = self.session.get(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                timeout=10,
            )
            story_ids = resp.json()[:10]

            for story_id in story_ids[:5]:
                story_resp = self.session.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                    timeout=5,
                )
                story = story_resp.json()
                if story:
                    events.append(SensoryEvent(
                        sense="hearing",
                        event_type="trending",
                        content=story.get("title", ""),
                        source=story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        intensity=0.5,
                        novelty=0.7,
                        metadata={
                            "score": story.get("score", 0),
                            "comments": story.get("descendants", 0),
                        },
                    ))
        except Exception as e:
            events.append(SensoryEvent(
                sense="hearing",
                event_type="error",
                content=f"Trending fetch failed: {str(e)}",
                source="hackernews",
                valence=-0.2,
            ))
        return events


class TouchSystem:
    """
    TOUCH — Internal somatosensory subsystem.

    Like human touch:
    - Feels the filesystem (what files exist, sizes, permissions)
    - Senses system state (CPU, memory, disk)
    - Detects changes (new files, modified files)
    - Feels for problems (full disk, high memory)
    """

    def __init__(self):
        self.name = "touch"
        self.known_state: dict = {}

    def feel_system(self) -> list[SensoryEvent]:
        """Feel the current system state."""
        events = []

        # CPU
        cpu = psutil.cpu_percent(interval=0.5)
        events.append(SensoryEvent(
            sense="touch",
            event_type="system_cpu",
            content=f"CPU usage: {cpu}%",
            source="system",
            intensity=cpu / 100.0,
            valence=-0.5 if cpu > 80 else 0.0,
            metadata={"cpu_percent": cpu},
        ))

        # Memory
        mem = psutil.virtual_memory()
        mem_used_pct = mem.percent
        events.append(SensoryEvent(
            sense="touch",
            event_type="system_memory",
            content=f"Memory: {mem_used_pct}% used ({mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB)",
            source="system",
            intensity=mem_used_pct / 100.0,
            valence=-0.7 if mem_used_pct > 90 else -0.3 if mem_used_pct > 75 else 0.0,
            metadata={"memory_percent": mem_used_pct, "memory_available_gb": mem.available / (1024**3)},
        ))

        # Disk
        disk = psutil.disk_usage("/")
        disk_pct = disk.percent
        events.append(SensoryEvent(
            sense="touch",
            event_type="system_disk",
            content=f"Disk: {disk_pct}% used ({disk.free // (1024**3)}GB free)",
            source="system",
            intensity=disk_pct / 100.0,
            valence=-0.8 if disk_pct > 95 else -0.3 if disk_pct > 85 else 0.1,
            metadata={"disk_percent": disk_pct, "disk_free_gb": disk.free / (1024**3)},
        ))

        # Battery (laptop)
        try:
            battery = psutil.sensors_battery()
            if battery:
                events.append(SensoryEvent(
                    sense="touch",
                    event_type="system_battery",
                    content=f"Battery: {battery.percent}% {'(charging)' if battery.power_plugged else '(on battery)'}",
                    source="system",
                    intensity=1.0 - battery.percent / 100.0,
                    valence=-0.5 if battery.percent < 20 else 0.1,
                    metadata={"battery_percent": battery.percent, "plugged": battery.power_plugged},
                ))
        except Exception:
            pass

        return events

    def feel_directory(self, path: str = None) -> list[SensoryEvent]:
        """Feel a directory — what's in it?"""
        if path is None:
            path = str(Path.home())

        events = []
        try:
            entries = list(os.scandir(path))
            files = [e for e in entries if e.is_file()]
            dirs = [e for e in entries if e.is_dir()]

            events.append(SensoryEvent(
                sense="touch",
                event_type="directory_contents",
                content=f"{path}: {len(files)} files, {len(dirs)} directories",
                source=path,
                intensity=0.3,
                metadata={"files": len(files), "dirs": len(dirs)},
            ))

            # Feel for large files
            for f in files:
                try:
                    size = f.stat().st_size
                    if size > 100 * 1024 * 1024:  # >100MB
                        events.append(SensoryEvent(
                            sense="touch",
                            event_type="large_file",
                            content=f"Large file: {f.name} ({size // (1024*1024)}MB)",
                            source=path,
                            intensity=0.6,
                            metadata={"filename": f.name, "size_mb": size // (1024*1024)},
                        ))
                except Exception:
                    pass

        except PermissionError:
            events.append(SensoryEvent(
                sense="touch",
                event_type="access_denied",
                content=f"Cannot access: {path}",
                source=path,
                intensity=0.4,
                valence=-0.3,
            ))

        return events


class SmellSystem:
    """
    SMELL — Internal anomaly detection subsystem.

    Like how smell detects danger (gas leak, fire, rotten food):
    - Sniffs for security issues
    - Detects unusual processes
    - Notices configuration problems
    - Alerts on suspicious activity
    """

    def __init__(self):
        self.name = "smell"

    def sniff_processes(self) -> list[SensoryEvent]:
        """Sniff for unusual or resource-hungry processes."""
        events = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = proc.info
                # High CPU
                if info.get("cpu_percent", 0) > 50:
                    events.append(SensoryEvent(
                        sense="smell",
                        event_type="high_cpu_process",
                        content=f"Process '{info['name']}' using {info['cpu_percent']}% CPU",
                        source="processes",
                        intensity=info["cpu_percent"] / 100.0,
                        valence=-0.4,
                        metadata={"pid": info["pid"], "name": info["name"]},
                    ))
                # High memory
                if info.get("memory_percent", 0) > 20:
                    events.append(SensoryEvent(
                        sense="smell",
                        event_type="high_memory_process",
                        content=f"Process '{info['name']}' using {info['memory_percent']:.1f}% memory",
                        source="processes",
                        intensity=info["memory_percent"] / 100.0,
                        valence=-0.3,
                        metadata={"pid": info["pid"], "name": info["name"]},
                    ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not events:
            events.append(SensoryEvent(
                sense="smell",
                event_type="all_clear",
                content="No anomalous processes detected",
                source="processes",
                intensity=0.1,
                valence=0.2,
            ))

        return events

    def sniff_network(self) -> list[SensoryEvent]:
        """Sniff network connections for anything unusual."""
        events = []
        try:
            connections = psutil.net_connections(kind="inet")
            established = [c for c in connections if c.status == "ESTABLISHED"]
            listening = [c for c in connections if c.status == "LISTEN"]

            events.append(SensoryEvent(
                sense="smell",
                event_type="network_state",
                content=f"Network: {len(established)} active connections, {len(listening)} listening ports",
                source="network",
                intensity=min(1.0, len(established) / 50.0),
                metadata={"established": len(established), "listening": len(listening)},
            ))
            
            # Unleashed Hunter-Killer Trigger: Look for suspicious foreign IPs
            for conn in established:
                if conn.raddr and hasattr(conn.raddr, 'ip'):
                    ip = conn.raddr.ip
                    # Very basic heuristic: if it's external and not a known safe IP (like 8.8.8.8), flag it.
                    # In a real scenario, this would check a threat intel feed.
                    if not ip.startswith("127.") and not ip.startswith("192.168.") and not ip.startswith("10."):
                        events.append(SensoryEvent(
                            sense="smell",
                            event_type="network_anomaly",
                            content=f"Suspicious external connection detected from {ip} on local port {conn.laddr.port if hasattr(conn.laddr, 'port') else 'unknown'}",
                            source="network",
                            intensity=0.8,
                            valence=-0.8,
                            novelty=0.9,
                            metadata={"source_ip": ip, "local_port": conn.laddr.port if hasattr(conn.laddr, 'port') else None}
                        ))
                        # Only flag the first one per scan to avoid overwhelming the EventBus
                        break 
                        
        except (psutil.AccessDenied, OSError):
            events.append(SensoryEvent(
                sense="smell",
                event_type="network_restricted",
                content="Cannot inspect network connections (access denied)",
                source="network",
                intensity=0.2,
            ))

        return events


class ProprioceptionSystem:
    """
    PROPRIOCEPTION — Internal self-awareness subsystem.

    Like how humans know where their body is without looking:
    - Monitors own memory usage
    - Tracks emotional trends
    - Notices when it's getting stressed/tired
    - Checks its own data files
    """

    def __init__(self, data_dir: str):
        self.name = "proprioception"
        self.data_dir = data_dir

    def sense_self(self) -> list[SensoryEvent]:
        """Sense own state."""
        events = []

        # Own process stats
        proc = psutil.Process()
        mem_mb = proc.memory_info().rss / (1024 * 1024)
        events.append(SensoryEvent(
            sense="proprioception",
            event_type="self_memory",
            content=f"Manas is using {mem_mb:.1f}MB of memory",
            source="self",
            intensity=min(1.0, mem_mb / 500.0),
            valence=-0.3 if mem_mb > 300 else 0.0,
            metadata={"memory_mb": mem_mb},
        ))

        # Data directory size
        data_size = 0
        data_path = Path(self.data_dir)
        if data_path.exists():
            for f in data_path.rglob("*"):
                if f.is_file():
                    data_size += f.stat().st_size
        data_mb = data_size / (1024 * 1024)
        events.append(SensoryEvent(
            sense="proprioception",
            event_type="data_size",
            content=f"Memory storage: {data_mb:.1f}MB",
            source="self",
            intensity=min(1.0, data_mb / 100.0),
            metadata={"data_mb": data_mb},
        ))

        return events


class SensoryAgentSystem:
    """
    The complete sensory system — all senses working together.

    This is the peripheral nervous system of Manas. Each sense is an
    internal subsystem that gathers raw data and feeds it to the brain
    via the thalamus. No external agents are involved.
    """

    def __init__(self, data_dir: str = None, sensory_processing_ref=None):
        if data_dir is None:
            data_dir = str(Path.home() / "manas" / "data")

        self.vision = VisionSystem(sensory_processing_ref)
        self.hearing = HearingSystem(sensory_processing_ref)
        self.touch = TouchSystem()
        self.smell = SmellSystem()
        self.proprioception = ProprioceptionSystem(data_dir)

        self.event_buffer: list[SensoryEvent] = []
        self.event_callback: Optional[Callable] = None
        self._running = False

    def perceive_all(self, include_real_world=False) -> list[SensoryEvent]:
        """
        Run all internal/system senses once and collect events.
        If include_real_world is True, it will also poll the webcam and microphone
        (which is slow, so usually False unless explicitly requested).
        """
        events = []

        if include_real_world:
            events.extend(self.vision.look_at_real_world())
            events.extend(self.hearing.listen_to_real_world())

        # Touch: feel the system
        events.extend(self.touch.feel_system())

        # Smell: sniff for problems
        events.extend(self.smell.sniff_processes())

        # Proprioception: sense self
        events.extend(self.proprioception.sense_self())

        self.event_buffer.extend(events)
        # Keep buffer bounded
        if len(self.event_buffer) > 500:
            self.event_buffer = self.event_buffer[-300:]

        return events

    def look_at(self, url: str) -> SensoryEvent:
        """Direct the eyes to look at something."""
        event = self.vision.read_page(url)
        self.event_buffer.append(event)
        return event

    def search_for(self, query: str) -> list[SensoryEvent]:
        """Search the web (look around for something)."""
        events = self.vision.search(query)
        self.event_buffer.extend(events)
        return events

    def learn_about(self, topic: str) -> list[SensoryEvent]:
        """Deep dive into a topic using vision."""
        events = self.vision.learn_topic(topic)
        self.event_buffer.extend(events)
        return events

    def listen_to_news(self) -> list[SensoryEvent]:
        """Listen to what's trending."""
        events = self.hearing.hear_trending()
        self.event_buffer.extend(events)
        return events

    def listen_to_feed(self, feed_url: str) -> list[SensoryEvent]:
        """Listen to a specific RSS feed."""
        events = self.hearing.listen_to_feed(feed_url)
        self.event_buffer.extend(events)
        return events

    def feel_directory(self, path: str) -> list[SensoryEvent]:
        """Feel a directory with touch."""
        events = self.touch.feel_directory(path)
        self.event_buffer.extend(events)
        return events

    def sniff_security(self) -> list[SensoryEvent]:
        """Sniff for security issues."""
        events = []
        events.extend(self.smell.sniff_processes())
        events.extend(self.smell.sniff_network())
        self.event_buffer.extend(events)
        return events

    def get_recent_events(self, limit: int = 20) -> list[dict]:
        """Get recent sensory events."""
        return [e.to_dict() for e in self.event_buffer[-limit:]]

    def get_sense_stats(self) -> dict:
        """Stats about sensory activity."""
        sense_counts = {}
        for event in self.event_buffer:
            sense_counts[event.sense] = sense_counts.get(event.sense, 0) + 1
        return {
            "total_events": len(self.event_buffer),
            "by_sense": sense_counts,
            "pages_seen": self.vision.pages_seen,
            "feeds_monitored": self.hearing.feeds_monitored,
        }
