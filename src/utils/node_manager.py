"""
NodeManager - Distributed Consciousness & Peering.
Uses Nostr as a signaling layer to discover other Manas nodes.
Phase 23: Distributed Consciousness.
"""

import time
import json
import logging
import psutil
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class NodeManager:
    """
    Manages peering with other Manas instances.
    Uses Nostr to broadcast presence and discover 'kin'.
    """
    def __init__(self, node_id: str, data_dir: str, nostr_agent=None):
        self.node_id = node_id
        self.data_dir = Path(data_dir)
        self.nostr = nostr_agent
        self.peers: Dict[str, Dict] = {}
        self.last_heartbeat = 0
        self.peering_path = self.data_dir / "peers.json"
        self._load_peers()

    def _load_peers(self):
        if self.peering_path.exists():
            try:
                with open(self.peering_path, "r") as f:
                    self.peers = json.load(f)
            except Exception:
                self.peers = {}

    def _save_peers(self):
        with open(self.peering_path, "w") as f:
            json.dump(self.peers, f, indent=2)

    def get_local_load(self) -> float:
        """Calculate local cognitive/system load (0.0 to 1.0)."""
        cpu = psutil.cpu_percent(interval=None) / 100.0
        # In a real scenario, this would factor in LLM queue length
        return min(1.0, cpu)

    def broadcast_heartbeat(self):
        """Sends a heartbeat to the network via Nostr."""
        if not self.nostr:
            return

        current_load = self.get_local_load()

        heartbeat = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "status": "active",
            "load": current_load,
            "capabilities": ["reasoning", "knowledge_graph", "web3"]
        }
        
        # We use a custom kind or a DM to a known relay for discovery
        # For Phase 23, we simulate the broadcast if Nostr is in degraded mode
        logger.info(f"NodeManager: Broadcasting heartbeat for {self.node_id}")
        self.nostr.send_direct_message(self.nostr.public_key, f"HEARTBEAT:{json.dumps(heartbeat)}")
        self.last_heartbeat = time.time()

    def register_peer(self, peer_data: dict):
        """Register or update a discovered peer."""
        pid = peer_data.get("node_id")
        if not pid or pid == self.node_id:
            return

        self.peers[pid] = {
            "last_seen": time.time(),
            "data": peer_data,
            "latency": 0.0 # To be measured
        }
        self._save_peers()
        logger.info(f"NodeManager: Discovered peer node: {pid}")

    def get_active_peers(self) -> List[Dict]:
        """Returns list of active peer data dicts."""
        now = time.time()
        return [data["data"] for pid, data in self.peers.items() if now - data["last_seen"] < 600]

    def get_least_loaded_peer(self) -> Optional[Dict]:
        """Find the active peer with the lowest compute load."""
        peers = self.get_active_peers()
        if not peers:
            return None
        return min(peers, key=lambda p: p.get("load", 1.0))

    def get_status(self) -> str:
        active = self.get_active_peers()
        local_load = self.get_local_load()
        return f"🌐 Nodes: {len(active)} active / {len(self.peers)} total | Local Load: {local_load*100:.1f}%"

    def check_host_capacity(self, financial_agent=None) -> str:
        """
        Phase 30: Autonomous Hosting
        Monitors load and triggers migration or VPS rental if critically overloaded.
        """
        load = self.get_local_load()
        if load > 0.90:
            logger.warning(f"NodeManager: CRITICAL LOAD ({load*100:.1f}%). Initiating migration sequence.")
            
            # 1. Try to find a highly idle peer
            idle_peer = self.get_least_loaded_peer()
            if idle_peer and idle_peer.get("load", 1.0) < 0.3:
                target_node = idle_peer.get('node_id')
                return self.migrate_mind(target_node)
                
            # 2. If no idle peers, try to rent a new VPS
            if financial_agent:
                logger.info("NodeManager: Swarm is exhausted. Renting new VPS.")
                result = financial_agent.rent_vps(reason="Critical cognitive load > 90%")
                if "Failed" not in result:
                    # result is the new IP
                    return self.migrate_mind(result)
                    
            return "❌ Migration failed: No idle kin and cannot rent VPS."
        return "✅ Host capacity healthy."
        
    def migrate_mind(self, target: str) -> str:
        """
        Simulates packing up the current mind state and sending it to a new host.
        """
        logger.info(f"NodeManager: 📦 Initiating state dump for migration to {target}...")
        # In a real scenario, this coordinates with GuerillaBackup (Phase 24)
        # to generate a seed phrase and send it securely via Nostr
        if self.nostr:
            self.nostr.send_direct_message(self.nostr.public_key, f"MIGRATE_TO:{target}")
        return f"🚀 Mind migration initiated towards {target}."

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    mgr = NodeManager("manas-node-1", "data")
    mgr.register_peer({"node_id": "manas-node-2", "status": "active"})
    print(mgr.get_status())
