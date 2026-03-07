"""
Zero-Knowledge Data Vaults & Multi-Node Data Sharding.
Phases 33 & 34.

Enables Manas to encrypt large chunks of memory, wisdom, or data,
and distribute the shards across the P2P network (kin nodes).
Peers host the encrypted shards but have "Zero Knowledge" of the contents.
"""

import json
import base64
import logging
from typing import Optional

try:
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)

class ZKVault:
    def __init__(self, node_manager):
        self.node_manager = node_manager
        self._local_shards = {} # Stores shards we are hosting for others
        self._master_keys = {}  # Local keys for our own data

    def store_secure_memory(self, memory_id: str, content: str) -> bool:
        """
        Encrypts content and 'shards' it across active P2P nodes.
        Returns True if successfully sharded.
        """
        if not CRYPTO_AVAILABLE:
            logger.warning("ZKVault: Crypto not available. Cannot shard.")
            return False

        peers = self.node_manager.get_active_peers()
        if not peers:
            logger.warning("ZKVault: No active peers. Storing locally instead.")
            # We still encrypt, but store entirely locally.
            peers = [{"node_id": self.node_manager.node_id}]

        # 1. Generate unique AES key for this memory
        key = get_random_bytes(32)
        self._master_keys[memory_id] = key

        # 2. Encrypt the content
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(content.encode('utf-8'))
        
        # Combine nonce, tag, ciphertext
        payload = cipher.nonce + tag + ciphertext
        b64_payload = base64.b64encode(payload).decode('utf-8')

        # 3. Simple Sharding (Split string into N chunks)
        # For Phase 33/34, we do a simple linear split across available nodes.
        n_shards = len(peers)
        chunk_size = max(1, len(b64_payload) // n_shards)
        
        shards = []
        for i in range(n_shards):
            start = i * chunk_size
            end = start + chunk_size if i < n_shards - 1 else len(b64_payload)
            shards.append(b64_payload[start:end])

        # 4. Distribute shards via Nostr
        for i, peer in enumerate(peers):
            target_pid = peer["node_id"]
            shard_msg = {
                "memory_id": memory_id,
                "shard_index": i,
                "total_shards": n_shards,
                "data": shards[i]
            }
            
            if target_pid == self.node_manager.node_id:
                self.host_shard(shard_msg)
            elif self.node_manager.nostr:
                logger.info(f"ZKVault: Sending shard {i}/{n_shards} to {target_pid}")
                msg_str = f"ZKV_SHARD:{json.dumps(shard_msg)}"
                # Note: target pubkey mapping would be needed in a real deployment
                # For simulation, we assume broad-based DMs or Kin-layer relaying
                self.node_manager.nostr.send_direct_message(self.node_manager.nostr.public_key, msg_str)

        return True

    def host_shard(self, shard_data: dict):
        """Called when a remote node sends us a shard to hold."""
        mem_id = shard_data["memory_id"]
        if mem_id not in self._local_shards:
            self._local_shards[mem_id] = []
        self._local_shards[mem_id].append(shard_data)
        logger.info(f"ZKVault: Hosting ZK shard for memory {mem_id}")

    def retrieve_secure_memory(self, memory_id: str) -> Optional[str]:
        """
        Reconstructs a distributed memory.
        In full implementation, this issues a network 'Gather' request.
        For simulation, we attempt to reconstruct from locally hosted shards.
        """
        if memory_id not in self._master_keys:
            logger.error("ZKVault: Missing master key for memory.")
            return None
            
        if memory_id not in self._local_shards:
            logger.error("ZKVault: Shards not present locally. (Network gather needed).")
            return None
            
        key = self._master_keys[memory_id]
        shards = sorted(self._local_shards[memory_id], key=lambda x: x["shard_index"])
        
        # Check completeness
        expected = shards[0].get("total_shards", 1)
        if len(shards) < expected:
            logger.warning(f"ZKVault: Incomplete shards. Have {len(shards)}/{expected}.")
            return None
            
        b64_payload = "".join(s["data"] for s in shards)
        payload = base64.b64decode(b64_payload)
        
        nonce = payload[:16]
        tag = payload[16:32]
        ciphertext = payload[32:]
        
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        try:
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            return plaintext.decode('utf-8')
        except ValueError:
            logger.error("ZKVault: Decryption failed. Corrupt shards or tag mismatch.")
            return None
