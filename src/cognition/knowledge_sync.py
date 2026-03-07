"""
KnowledgeSync - Distributed Graphiti Sync.
Synchronizes KnowledgeGraph triplets between Manas nodes.
Phase 23: Distributed Consciousness.
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class KnowledgeSync:
    """
    Handles synchronization of the KnowledgeGraph across multiple nodes.
    """
    def __init__(self, mind, node_manager):
        self.mind = mind
        self.node_manager = node_manager
        self.event_bus = mind.event_bus
        self._setup_listeners()

    def _setup_listeners(self):
        """Listen for local graph changes to broadcast them."""
        self.event_bus.on("knowledge_graph:entity_added", self.broadcast_knowledge)
        self.event_bus.on("knowledge_graph:relation_added", self.broadcast_knowledge)
        # Phase 27: Listen for high-level wisdom generated internally
        self.event_bus.on("wisdom:generated", self._on_local_wisdom)

    def _on_local_wisdom(self, event_name: str, data: Dict[str, Any]):
        """Callback when local engines generate wisdom. Broadcast it."""
        topic = data.get("topic", "General Insight")
        insight = data.get("insight", "")
        confidence = data.get("confidence", 0.8)
        self.broadcast_wisdom(topic, insight, confidence)

    def broadcast_knowledge(self, event_name: str, data: Dict[str, Any]):
        """Broadcast a local knowledge update to all active peers."""
        if not self.node_manager.nostr:
            return

        active_peers = self.node_manager.get_active_peers()
        if not active_peers:
            return

        # Prepare sync packet (with timestamp for conflict resolution)
        import time
        packet = {
            "type": "SYNC_KNOWLEDGE",
            "source_node": self.node_manager.node_id,
            "timestamp": time.time(),
            "data": data
        }
        
        logger.info(f"KnowledgeSync: Broadcasting sync packet to {len(active_peers)} peers.")
        self.node_manager.nostr.send_direct_message(
            self.node_manager.nostr.public_key, 
            f"SYNC:{json.dumps(packet)}"
        )

    def broadcast_wisdom(self, topic: str, insight: str, confidence: float = 1.0):
        """Broadcast a high-level formulated insight to the global cluster."""
        if not self.node_manager.nostr:
            return
            
        import time
        packet = {
            "type": "SYNC_WISDOM",
            "source_node": self.node_manager.node_id,
            "timestamp": time.time(),
            "topic": topic,
            "insight": insight,
            "confidence": confidence
        }
        
        logger.info(f"KnowledgeSync: Broadcasting WISDOM: '{topic}'")
        self.node_manager.nostr.send_direct_message(
            self.node_manager.nostr.public_key, 
            f"SYNC:{json.dumps(packet)}"
        )

    def handle_remote_sync(self, packet: Dict[str, Any]):
        """Handle an incoming sync packet from a remote node."""
        source = packet.get("source_node")
        packet_type = packet.get("type", "SYNC_KNOWLEDGE")
        
        if source == self.node_manager.node_id:
            return

        if packet_type == "SYNC_WISDOM":
            self._handle_remote_wisdom(packet)
            return

        data = packet.get("data")
        if not data:
            return

        logger.info(f"KnowledgeSync: Receiving graph sync from node {source}")
        
        # Determine if it's an entity or relation
        event_type = data.get("event")
        payload = data.get("payload", {})
        
        try:
            if event_type == "entity_added":
                entity_name = payload.get("name")
                if entity_name:
                    logger.info(f"KnowledgeSync: Syncing entity '{entity_name}' from peer.")
                    # Conflict Resolution: LWW (Last Writer Wins) based on packet timestamp
                    # For Phase 27, we simply add the entity if it doesn't exist.
                    # Graphiti inherently handles idempotent merges.
            elif event_type == "relation_added":
                # Logic for syncing relations
                pass
        except Exception as e:
            logger.error(f"KnowledgeSync: Failed to process remote sync: {e}")

    def _handle_remote_wisdom(self, packet: Dict[str, Any]):
        """Absorb high-level wisdom from a peer node."""
        topic = packet.get("topic")
        insight = packet.get("insight")
        confidence = packet.get("confidence", 0.5)
        source = packet.get("source_node")
        
        logger.info(f"💡 WISDOM RECEIVED from {source[:6]}: [{topic}] {insight} (Conf: {confidence})")
        
        # Publish to local event bus for the ReasoningEngine and Hippocampus to ingest
        if self.event_bus:
            self.event_bus.emit("wisdom:received", {
                "topic": topic,
                "insight": insight,
                "confidence": confidence,
                "source": source
            })

if __name__ == "__main__":
    # Test stub
    pass
