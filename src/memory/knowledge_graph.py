import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """
    Neural Knowledge Graph (Graphiti) — Manas's relational memory.
    Stores Entities (Nodes) and Relations (Edges).
    Allows Manas to understand how disparate pieces of information are connected.
    """

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.graph_path = self.data_dir / "knowledge_graph.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._load_graph()

    def _load_graph(self):
        if self.graph_path.exists():
            with open(self.graph_path, "r") as f:
                self.graph = json.load(f)
        else:
            self.graph = {
                "entities": {},  # id -> {name, type, properties, created_at}
                "relations": [], # [{source, target, relation_type, weight, timestamp}]
                "version": "1.0"
            }

    def _save_graph(self):
        with open(self.graph_path, "w") as f:
            json.dump(self.graph, f, indent=2)

    def add_entity(self, entity_id: str, name: str, entity_type: str, properties: Dict[str, Any] = None) -> bool:
        """Adds a new entity node to the graph."""
        if entity_id in self.graph["entities"]:
            # Update existing properties
            self.graph["entities"][entity_id]["properties"].update(properties or {})
            return True

        self.graph["entities"][entity_id] = {
            "name": name,
            "type": entity_type,
            "properties": properties or {},
            "created_at": time.time()
        }
        self._save_graph()
        return True

    def add_relation(self, source_id: str, target_id: str, relation_type: str, weight: float = 1.0) -> bool:
        """Adds a directed relation edge between two entities."""
        if source_id not in self.graph["entities"] or target_id not in self.graph["entities"]:
            logger.warning(f"KnowledgeGraph: Cannot link missing entities {source_id} -> {target_id}")
            return False

        relation = {
            "source": source_id,
            "target": target_id,
            "type": relation_type,
            "weight": weight,
            "timestamp": time.time()
        }
        self.graph["relations"].append(relation)
        self._save_graph()
        return True

    def get_related_entities(self, entity_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Finds entities related to the given id within specified depth."""
        if entity_id not in self.graph["entities"]:
            return []

        related = []
        visited = {entity_id}
        queue = [(entity_id, 0)]

        while queue:
            current_id, current_depth = queue.pop(0)
            if current_depth >= depth:
                break

            for rel in self.graph["relations"]:
                neighbor_id = None
                if rel["source"] == current_id:
                    neighbor_id = rel["target"]
                elif rel["target"] == current_id:
                    neighbor_id = rel["source"]

                if neighbor_id and neighbor_id not in visited:
                    visited.add(neighbor_id)
                    entity_info = self.graph["entities"][neighbor_id]
                    entity_info["id"] = neighbor_id
                    entity_info["relation"] = rel["type"]
                    related.append(entity_info)
                    queue.append((neighbor_id, current_depth + 1))

        return related

    def query_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Returns all entities of a specific type."""
        results = []
        for eid, info in self.graph["entities"].items():
            if info["type"] == entity_type:
                res = info.copy()
                res["id"] = eid
                results.append(res)
        return results

    def get_context_summary(self, entity_id: str) -> str:
        """Returns a string summary of an entity and its connections."""
        if entity_id not in self.graph["entities"]:
            return f"No knowledge about '{entity_id}'."

        entity = self.graph["entities"][entity_id]
        related = self.get_related_entities(entity_id)
        
        summary = f"Entity: {entity['name']} ({entity['type']})\n"
        if entity['properties']:
            summary += f"Properties: {json.dumps(entity['properties'])}\n"
        
        if related:
            summary += "Connected to:\n"
            for r in related:
                summary += f"  - [{r['relation']}] -> {r['name']} ({r['type']})\n"
        else:
            summary += "No direct connections found."
        
        return summary

    def find_path(self, start_id: str, end_id: str, max_depth: int = 5) -> List[Dict]:
        """BFS to find the shortest path between two entities."""
        if start_id not in self.graph["entities"] or end_id not in self.graph["entities"]:
            return []

        queue = [(start_id, [])]
        visited = {start_id}

        while queue:
            (node_id, path) = queue.pop(0)
            
            for rel in self.graph["relations"]:
                neighbor_id = None
                if rel["source"] == node_id:
                    neighbor_id = rel["target"]
                elif rel["target"] == node_id:
                    neighbor_id = rel["source"]

                if neighbor_id == end_id:
                    return path + [{"source": node_id, "target": neighbor_id, "type": rel["type"]}]

                if neighbor_id and neighbor_id not in visited and len(path) < max_depth:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [{"source": node_id, "target": neighbor_id, "type": rel["type"]}]))
        
        return []
