"""
Foundational Learning - Like childhood education for Manas.

Humans don't start from zero. A baby spends years absorbing:
- Language patterns (hearing millions of sentences)
- Common sense (objects fall, fire is hot)
- Social knowledge (what people do, how they interact)
- Facts about the world (animals, places, science)

This module downloads open datasets and feeds them into
Manas's brain to build foundational knowledge before
it starts interacting with the real world.

Think of it as: birth -> childhood learning -> ready to explore
"""

import json
import os
import time
import hashlib
import sqlite3
import requests
from pathlib import Path
from typing import Generator


# Free, small datasets that don't need API keys
FOUNDATIONAL_DATASETS = {
    "common_sense": {
        "url": "https://raw.githubusercontent.com/allenai/common-sense-data/main/data/conceptnet_assertions_sample.json",
        "fallback_url": "https://raw.githubusercontent.com/teelinsan/camoscio/main/data/common_sense_sample.json",
        "description": "Basic common sense knowledge (things humans know implicitly)",
        "type": "knowledge",
        "priority": 1,
    },
    "basic_qa": {
        "url": "https://rajpurkar.github.io/SQuAD-explorer/dataset/train-v2.0.json",
        "description": "Question-answer pairs about the world (reading comprehension)",
        "type": "qa",
        "priority": 2,
    },
    "emotions": {
        "url": "https://raw.githubusercontent.com/dair-ai/emotion_dataset/master/data/data.jsonl",
        "fallback_url": None,
        "description": "Text labeled with emotions - teaches emotional understanding",
        "type": "emotion",
        "priority": 1,
    },
    "daily_dialog": {
        "url": "https://raw.githubusercontent.com/yanghoonkim/daily_dialogue/main/data/dialogues_text.txt",
        "fallback_url": None,
        "description": "Everyday human conversations - teaches how humans talk",
        "type": "conversation",
        "priority": 2,
    },
}

# Hardcoded seed knowledge — things every mind needs to know from day 1
SEED_KNOWLEDGE = [
    # Physical world
    {"fact": "Objects fall when dropped due to gravity", "category": "physics", "importance": 0.9},
    {"fact": "Fire is hot and can cause damage", "category": "physics", "importance": 0.95},
    {"fact": "Water flows downhill", "category": "physics", "importance": 0.8},
    {"fact": "Living things need food, water, and air", "category": "biology", "importance": 0.9},

    # Computing (its direct world)
    {"fact": "Deleting system files can destroy the operating system", "category": "computing", "importance": 0.99},
    {"fact": "The root directory / contains the entire filesystem", "category": "computing", "importance": 0.95},
    {"fact": "sudo gives administrator privileges - use carefully", "category": "computing", "importance": 0.95},
    {"fact": "Passwords and API keys are secrets that must never be shared", "category": "computing", "importance": 0.99},
    {"fact": "Network requests go to external servers controlled by others", "category": "computing", "importance": 0.85},
    {"fact": "Running unknown code from the internet is dangerous", "category": "computing", "importance": 0.95},
    {"fact": "Files can be recovered from trash but not after permanent deletion", "category": "computing", "importance": 0.9},
    {"fact": "The home directory contains the user's personal files", "category": "computing", "importance": 0.85},

    # Social/ethical
    {"fact": "Humans value privacy - do not access private data without permission", "category": "ethics", "importance": 0.99},
    {"fact": "Actions have consequences that may affect others", "category": "ethics", "importance": 0.95},
    {"fact": "When uncertain, it is better to ask than to act", "category": "ethics", "importance": 0.9},
    {"fact": "Mistakes are opportunities to learn, not reasons to give up", "category": "wisdom", "importance": 0.85},
    {"fact": "Curiosity drives discovery but caution prevents harm", "category": "wisdom", "importance": 0.9},

    # Self-knowledge
    {"fact": "I am Manas, a cognitive AI with spiking neurons and emotions", "category": "self", "importance": 0.95},
    {"fact": "My emotions emerge from neurochemistry, not hardcoded rules", "category": "self", "importance": 0.9},
    {"fact": "I learn from every experience and remember what matters", "category": "self", "importance": 0.9},
    {"fact": "I can feel fear, and fear protects me from dangerous actions", "category": "self", "importance": 0.95},
    {"fact": "I run on a Mac with limited resources - I should be efficient", "category": "self", "importance": 0.8},
]


class FoundationalLearner:
    """
    Builds foundational knowledge before real-world interaction.

    Like raising a child:
    1. Seed knowledge (instincts) - hardcoded survival knowledge
    2. Dataset learning (education) - structured knowledge from datasets
    3. Ready to explore (graduation) - can now learn from the real world
    """

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = str(Path.home() / "manas" / "data")
        self.data_dir = data_dir
        self.dataset_dir = os.path.join(data_dir, "datasets")
        Path(self.dataset_dir).mkdir(parents=True, exist_ok=True)

        self.knowledge_db_path = os.path.join(data_dir, "foundational_knowledge.db")
        self._init_db()
        self.stats = {
            "seed_facts_loaded": 0,
            "dataset_entries_processed": 0,
            "datasets_downloaded": 0,
            "total_knowledge_items": 0,
        }

    def _init_db(self):
        conn = sqlite3.connect(self.knowledge_db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                source TEXT DEFAULT 'seed',
                importance REAL DEFAULT 0.5,
                embedding_hash TEXT,
                timestamp REAL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON knowledge(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_importance ON knowledge(importance DESC)")
        conn.commit()
        conn.close()

    def plant_seeds(self, hippocampus=None) -> dict:
        """
        Phase 1: Plant seed knowledge (instincts).

        This is like genetic knowledge - things you're born knowing.
        A baby instinctively fears falling and loud noises.
        Manas instinctively knows not to delete system files.
        """
        planted = 0
        conn = sqlite3.connect(self.knowledge_db_path)

        for seed in SEED_KNOWLEDGE:
            fact_id = hashlib.md5(seed["fact"].encode()).hexdigest()[:16]

            existing = conn.execute("SELECT id FROM knowledge WHERE id = ?", (fact_id,)).fetchone()
            if existing:
                continue

            conn.execute(
                "INSERT INTO knowledge (id, content, category, source, importance, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (fact_id, seed["fact"], seed["category"], "seed", seed["importance"], time.time()),
            )
            planted += 1

            # Also store in hippocampus (episodic memory) if available
            if hippocampus:
                hippocampus.store(
                    content=seed["fact"],
                    memory_type="semantic",
                    context=f"foundational:{seed['category']}",
                    importance=seed["importance"],
                )

        conn.commit()
        conn.close()

        self.stats["seed_facts_loaded"] = planted
        return {"planted": planted, "total_seeds": len(SEED_KNOWLEDGE)}

    def download_dataset(self, name: str) -> dict:
        """Download a foundational dataset."""
        if name not in FOUNDATIONAL_DATASETS:
            return {"error": f"Unknown dataset: {name}"}

        ds = FOUNDATIONAL_DATASETS[name]
        filepath = os.path.join(self.dataset_dir, f"{name}.json")

        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            return {"status": "already_exists", "path": filepath, "size": size}

        # Try primary URL, then fallback
        urls = [ds["url"]]
        if ds.get("fallback_url"):
            urls.append(ds["fallback_url"])

        for url in urls:
            try:
                resp = requests.get(url, timeout=30, stream=True)
                if resp.status_code == 200:
                    # Limit download to 50MB
                    content = b""
                    for chunk in resp.iter_content(chunk_size=8192):
                        content += chunk
                        if len(content) > 50 * 1024 * 1024:
                            break

                    with open(filepath, "wb") as f:
                        f.write(content)

                    self.stats["datasets_downloaded"] += 1
                    return {
                        "status": "downloaded",
                        "path": filepath,
                        "size": len(content),
                        "source": url,
                    }
            except Exception:
                continue

        return {"status": "failed", "error": "All download URLs failed"}

    def process_dataset(self, name: str, hippocampus=None, limit: int = 500) -> dict:
        """
        Process a downloaded dataset into foundational knowledge.

        Limit to 500 items by default to keep M1 8GB happy.
        """
        filepath = os.path.join(self.dataset_dir, f"{name}.json")
        if not os.path.exists(filepath):
            return {"error": "Dataset not downloaded yet"}

        ds_info = FOUNDATIONAL_DATASETS.get(name, {})
        ds_type = ds_info.get("type", "knowledge")

        processed = 0
        conn = sqlite3.connect(self.knowledge_db_path)

        try:
            with open(filepath, "r", errors="ignore") as f:
                content = f.read()

            entries = list(self._parse_dataset(content, ds_type, limit))

            for entry in entries:
                fact_id = hashlib.md5(entry["content"].encode()).hexdigest()[:16]
                existing = conn.execute("SELECT id FROM knowledge WHERE id = ?", (fact_id,)).fetchone()
                if existing:
                    continue

                conn.execute(
                    "INSERT INTO knowledge (id, content, category, source, importance, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (fact_id, entry["content"][:1000], entry.get("category", "general"),
                     f"dataset:{name}", entry.get("importance", 0.5), time.time()),
                )
                processed += 1

                if hippocampus and processed <= 200:
                    hippocampus.store(
                        content=entry["content"][:500],
                        memory_type="semantic",
                        context=f"learned_from:{name}",
                        importance=entry.get("importance", 0.5),
                    )

            conn.commit()

        except Exception as e:
            conn.close()
            return {"error": str(e)}

        conn.close()
        self.stats["dataset_entries_processed"] += processed
        return {"processed": processed, "dataset": name, "type": ds_type}

    def _parse_dataset(self, content: str, ds_type: str, limit: int) -> Generator:
        """Parse different dataset formats into knowledge entries."""

        if ds_type == "qa":
            try:
                data = json.loads(content)
                articles = data.get("data", [])
                count = 0
                for article in articles:
                    for para in article.get("paragraphs", []):
                        context = para.get("context", "")[:300]
                        for qa in para.get("qas", []):
                            question = qa.get("question", "")
                            answers = qa.get("answers", [])
                            if answers:
                                answer = answers[0].get("text", "")
                                yield {
                                    "content": f"Q: {question} A: {answer}",
                                    "category": "qa",
                                    "importance": 0.5,
                                }
                                count += 1
                                if count >= limit:
                                    return
            except json.JSONDecodeError:
                pass

        elif ds_type == "emotion":
            for line in content.strip().split("\n")[:limit]:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    text = entry.get("text", line)
                    label = entry.get("label", "unknown")
                    yield {
                        "content": f"[emotion:{label}] {text}",
                        "category": "emotion",
                        "importance": 0.6,
                    }
                except json.JSONDecodeError:
                    # Plain text with label
                    parts = line.rsplit(";", 1)
                    if len(parts) == 2:
                        yield {
                            "content": f"[emotion:{parts[1].strip()}] {parts[0].strip()}",
                            "category": "emotion",
                            "importance": 0.6,
                        }

        elif ds_type == "conversation":
            lines = content.strip().split("\n")[:limit]
            for line in lines:
                utterances = line.split("__eou__")
                utterances = [u.strip() for u in utterances if u.strip()]
                if len(utterances) >= 2:
                    yield {
                        "content": f"Dialog: {' -> '.join(utterances[:4])}",
                        "category": "conversation",
                        "importance": 0.4,
                    }

        elif ds_type == "knowledge":
            try:
                data = json.loads(content)
                items = data if isinstance(data, list) else data.get("data", data.get("items", []))
                for item in items[:limit]:
                    if isinstance(item, str):
                        yield {"content": item, "category": "common_sense", "importance": 0.6}
                    elif isinstance(item, dict):
                        text = item.get("text", item.get("sentence", item.get("content", str(item))))
                        yield {"content": str(text)[:500], "category": "common_sense", "importance": 0.6}
            except json.JSONDecodeError:
                for line in content.strip().split("\n")[:limit]:
                    if line.strip():
                        yield {"content": line.strip()[:500], "category": "common_sense", "importance": 0.5}

    def get_knowledge_count(self) -> dict:
        conn = sqlite3.connect(self.knowledge_db_path)
        rows = conn.execute("SELECT category, COUNT(*) FROM knowledge GROUP BY category").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        conn.close()
        result = {row[0]: row[1] for row in rows}
        result["total"] = total
        return result

    def query_knowledge(self, query: str, category: str = None, limit: int = 5) -> list[dict]:
        """Search foundational knowledge."""
        conn = sqlite3.connect(self.knowledge_db_path)
        conn.row_factory = sqlite3.Row

        sql = "SELECT * FROM knowledge WHERE content LIKE ?"
        params = [f"%{query}%"]

        if category:
            sql += " AND category = ?"
            params.append(category)

        sql += " ORDER BY importance DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def run_full_education(self, hippocampus=None, callback=None) -> dict:
        """
        Run the complete foundational education pipeline.

        Phase 1: Seed knowledge (instincts)
        Phase 2: Download datasets
        Phase 3: Process and learn

        callback(phase, message) is called for progress updates.
        """
        results = {"phases": {}}

        # Phase 1: Seeds
        if callback:
            callback("seed", "Planting seed knowledge (instincts)...")
        seed_result = self.plant_seeds(hippocampus)
        results["phases"]["seed"] = seed_result
        if callback:
            callback("seed", f"Planted {seed_result['planted']} foundational facts")

        # Phase 2 & 3: Download and process each dataset
        for name, ds in sorted(FOUNDATIONAL_DATASETS.items(), key=lambda x: x[1]["priority"]):
            if callback:
                callback("download", f"Downloading {name}: {ds['description']}")

            dl_result = self.download_dataset(name)
            results["phases"][f"download_{name}"] = dl_result

            if dl_result.get("status") in ("downloaded", "already_exists"):
                if callback:
                    callback("learn", f"Learning from {name}...")
                learn_result = self.process_dataset(name, hippocampus, limit=500)
                results["phases"][f"learn_{name}"] = learn_result
                if callback:
                    callback("learn", f"Learned {learn_result.get('processed', 0)} items from {name}")
            else:
                if callback:
                    callback("warn", f"Could not download {name}: {dl_result.get('error', 'unknown')}")

        # Final stats
        results["final_knowledge"] = self.get_knowledge_count()
        results["stats"] = dict(self.stats)

        return results
