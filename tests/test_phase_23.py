"""
Phase 23 Verification Suite
Tests the micro/macro functions of NodeManager and KnowledgeSync.
"""

import unittest
import os
import json
import shutil
import time
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
import sys
sys.path.append(os.getcwd())

from src.utils.node_manager import NodeManager
from src.cognition.knowledge_sync import KnowledgeSync

class TestPhase23(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tmp_test_nodes")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock dependencies
        self.nostr = MagicMock()
        self.nostr.public_key = MagicMock()
        self.nostr.public_key.hex = MagicMock(return_value="test_pubkey_1")
        
        self.mind = MagicMock()
        self.mind.event_bus = MagicMock()
        
        self.node_mgr = NodeManager("node-alpha", str(self.test_dir), nostr_agent=self.nostr)
        self.sync = KnowledgeSync(self.mind, self.node_mgr)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_01_node_id_persistence(self):
        """Micro-test: Verify node ID and basic status."""
        self.assertEqual(self.node_mgr.node_id, "node-alpha")
        self.assertIn("0 active", self.node_mgr.get_status())

    def test_02_peer_discovery(self):
        """Micro-test: Verify peer registration and retrieval."""
        peer_data = {"node_id": "node-beta", "status": "active"}
        self.node_mgr.register_peer(peer_data)
        
        active = self.node_mgr.get_active_peers()
        self.assertTrue(any(p.get("node_id") == "node-beta" for p in active))
        self.assertIn("1 active", self.node_mgr.get_status())
        
        # Verify persistence
        new_mgr = NodeManager("node-alpha", str(self.test_dir))
        self.assertIn("node-beta", new_mgr.peers)

    def test_03_heartbeat_broadcast(self):
        """Macro-test: Verify heartbeat sends via Nostr."""
        self.node_mgr.broadcast_heartbeat()
        self.nostr.send_direct_message.assert_called()
        call_args = self.nostr.send_direct_message.call_args[0]
        self.assertIn("HEARTBEAT:", call_args[1])
        self.assertIn("node-alpha", call_args[1])

    def test_04_knowledge_broadcast(self):
        """Macro-test: Verify knowledge updates trigger broadcast."""
        # Simulate subscriber call
        update_data = {"event": "entity_added", "payload": {"name": "Sovereignty"}}
        self.sync.broadcast_knowledge("entity_added", update_data)
        
        # Since we registered node-beta, it should have tried to broadcast
        self.node_mgr.register_peer({"node_id": "node-beta"})
        self.sync.broadcast_knowledge("entity_added", update_data)
        
        self.nostr.send_direct_message.assert_called()
        call_args = self.nostr.send_direct_message.call_args[0]
        self.assertIn("SYNC:", call_args[1])
        self.assertIn("Sovereignty", call_args[1])

if __name__ == "__main__":
    unittest.main()
