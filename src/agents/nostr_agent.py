import asyncio
import json
import logging
import hashlib
import time
import queue
from typing import Optional
import websockets
try:
    from nostr.key import PrivateKey
    from nostr.event import Event, EventKind
    NOSTR_AVAILABLE = True
except (ImportError, Exception):
    NOSTR_AVAILABLE = False
    class PrivateKey: 
        def __init__(self, *args, **kwargs): pass
        def public_key(self): pass
        def hex(self): return "nostr_not_available"
        def encrypt_message(self, *args, **kwargs): return "nostr_inactive"
        def sign_event(self, *args, **kwargs): pass
    class Event: 
        def __init__(self, *args, **kwargs): pass
        def to_dict(self): return {}
    class EventKind: pass
from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)

class NostrAgent(BaseAgent):
    """
    Connects Manas to the Nostr protocol (Phase 5).
    Allows receiving and sending encrypted DMs (NIP-17/NIP-04) via internet relays,
    acting as a bridge to Bit Chat.
    """

    def __init__(self, name: str, llm_router, memory, private_key_hex: str = None):
        super().__init__(name, llm_router, memory)
        self.relays = [
            "wss://relay.damus.io",
            "wss://nos.lol",
            "wss://relay.nostr.band"
        ]
        
        self.connected_websockets = []
        self._loop_task: Optional[asyncio.Task] = None
        self.send_queue = queue.Queue()
        
        # Initialize identity
        if not NOSTR_AVAILABLE:
            self.private_key = PrivateKey()
            self.public_key = self.private_key
            logger.debug("NostrAgent: Inactive due to library availability (expected on 3.14).")
            return

        if private_key_hex:
            self.private_key = PrivateKey(bytes.fromhex(private_key_hex))
        else:
            self.private_key = PrivateKey()
            logger.info("NostrAgent: Generated new private key.")
            
        self.public_key = self.private_key.public_key
        logger.info(f"NostrAgent Pubkey: {self.public_key.bech32()}")
            
        self.connected_websockets = []
        self._loop_task: Optional[asyncio.Task] = None

    def get_private_key_hex(self) -> str:
        """Returns the private key in hex format for persistence."""
        return self.private_key.hex()

    def run(self, task: str) -> AgentResult:
        """
        Since Nostr is a continuous connection, a 'run' task here might mean
        'Send message X to Pubkey Y' instead of a standing background thread.
        For continuous monitoring, start_listening() is used.
        """
        # A simple parser for single-shot tasks if orchestrated
        if task.startswith("send_msg:"):
            parts = task.replace("send_msg:", "").split("|", 1)
            if len(parts) == 2:
                target_pubkey, msg = parts
                self.log(f"Attempting to send DM to {target_pubkey}: {msg}")
                # Use now-sync wrapper
                self.send_direct_message(target_pubkey.strip(), msg.strip())
                return AgentResult(True, f"Sent DM to {target_pubkey}", "\n".join(self.logs))
        
        return AgentResult(False, "Unknown task format for NostrAgent", "\n".join(self.logs))

    def _init_chroma(self):
        """Initializes the local ChromaDB client and collection."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Use persistent local storage
            self.chroma_client = chromadb.PersistentClient(path=self.db_path)
            
            # Create or get the main 'hippocampus' collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="hippocampus",
                metadata={"hnsw:space": "cosine"}
            )
            logger.debug(f"Hippocampus: ChromaDB active at {self.db_path}.")
            self.has_chromadb = True
            
        except (ImportError, Exception) as e:
            # Silencing the error for the user as requested, but keeping it for debugging
            logger.debug(f"Hippocampus: ChromaDB failed (expected on 3.14): {e}")
            self.has_chromadb = False

    async def publish_metadata(self, name: str, about: str, lud16: str = ""):
        """
        Phase 36: Monetization broadcast.
        Publishes Manas's profile (NIP-01 Kind 0) containing a Lightning Address (lud16)
        so humans can send him Zaps (micropayments).
        """
        if not self.connected_websockets:
            self.log("Cannot publish metadata: Not connected to any relays.")
            return

        metadata = {
            "name": name,
            "about": about,
            "picture": "https://robohash.org/manas_node.png"
        }
        if lud16:
            metadata["lud16"] = lud16  # The critical earning hook

        content = json.dumps(metadata)
        created_at = int(time.time())
        kind = 0
        tags = []

        # Construct and sign event
        event_data = [
            0,
            self.public_key.hex(),
            created_at,
            kind,
            tags,
            content
        ]
        
        # Serialize and hash the event
        serialized_event = json.dumps(event_data, separators=(',', ':'))
        event_id = hashlib.sha256(serialized_event.encode()).hexdigest()
        sig = self.private_key.sign(event_id.encode())
        
        event = {
            "id": event_id,
            "pubkey": self.public_key.hex(),
            "created_at": created_at,
            "kind": kind,
            "tags": tags,
            "content": content,
            "sig": sig
        }
        
        message = json.dumps(["EVENT", event])
        for ws in self.connected_websockets:
            try:
                await ws.send(message)
                self.log(f"Published profile metadata to {ws.remote_address}")
            except Exception as e:
                self.log(f"Failed to publish to relay: {e}")

    async def connect_and_listen(self):
        """Connects to configured relays and listens for incoming DMs."""
        self.status = "listening"
        
        # Start the queue processor
        asyncio.create_task(self._process_send_queue())
        
        for relay in self.relays:
            try:
                ws = await websockets.connect(relay)
                self.connected_websockets.append(ws)
                self.log(f"Connected to relay: {relay}")
                
                # Setup subscription for DMs directed at us
                req_id = "manas_dms"
                filter_json = json.dumps([
                    "REQ", req_id,
                    {"kinds": [4], "#p": [self.public_key.hex()]}
                ])
                await ws.send(filter_json)
                
                # Start listener task for this specific websocket
                asyncio.create_task(self._listen_to_relay(ws))
                
            except Exception as e:
                self.log(f"Failed to connect to {relay}: {str(e)}")

    async def _process_send_queue(self):
        """Background task to drain the send queue."""
        while True:
            try:
                if not self.send_queue.empty():
                    target_pubkey_hex, message = self.send_queue.get()
                    await self._send_direct_message_async(target_pubkey_hex, message)
                    self.send_queue.task_done()
                await asyncio.sleep(1) # Don't spin too hard
            except Exception as e:
                logger.error(f"NostrAgent: Exception in send_queue processor: {e}")
                await asyncio.sleep(5)

    async def _listen_to_relay(self, ws):
        """Processes messages from a single relay."""
        try:
            async for message in ws:
                data = json.loads(message)
                if data[0] == "EVENT":
                    event_data = data[2]
                    await self._handle_event(event_data)
        except Exception as e:
            self.log(f"Relay connection lost: {str(e)}")

    async def _handle_event(self, event_data: dict):
        """Handle incoming Nostr events."""
        kind = event_data.get("kind")
        if kind == 4: # NIP-04 Encrypted Direct Message
            sender_pubkey = event_data.get("pubkey")
            encrypted_content = event_data.get("content")
            
            try:
                # Decrypt the message
                decrypted = self.private_key.decrypt_message(encrypted_content, sender_pubkey)
                
                # Phase 23: Handle Peering Logic
                if decrypted.startswith("HEARTBEAT:"):
                    hb_data = json.loads(decrypted.replace("HEARTBEAT:", ""))
                    if hasattr(self, "on_heartbeat"):
                        self.on_heartbeat(hb_data)
                    return

                if decrypted.startswith("SYNC:"):
                    sync_data = json.loads(decrypted.replace("SYNC:", ""))
                    if hasattr(self, "on_sync"):
                        self.on_sync(sync_data)
                    return

                # Normal DM processing
                self.log(f"Received DM from {sender_pubkey}: {decrypted}")
                self.memory.store(
                    content=decrypted,
                    memory_type="nostr_dm",
                    context=f"From: {sender_pubkey}",
                    importance=0.8
                )
                
                # Generate an autonomous reply via LLMRouter if it's a direct conversation
                # Only reply if it's not from ourselves (self-sync)
                if sender_pubkey != self.public_key.hex():
                    response = self.llm_router.generate(
                        prompt=f"You received a direct message from '{sender_pubkey}': '{decrypted}'. Formulate a friendly, concise reply as Manas.",
                        task_type="simple"
                    )
                    # Now sync-wrapper, no await needed
                    self.send_direct_message(sender_pubkey, response)
                
            except Exception as e:
                self.log(f"Failed to decrypt or process DM: {str(e)}")

    def send_direct_message(self, target_pubkey_hex: str, message: str):
        """Synchronous wrapper to enqueue a DM."""
        self.send_queue.put((target_pubkey_hex, message))
        self.log(f"Enqueued DM for {target_pubkey_hex}")

    async def _send_direct_message_async(self, target_pubkey_hex: str, message: str):
        """The actual async logic to send an encrypted NIP-04 message."""
        if not self.private_key or not NOSTR_AVAILABLE:
            return

        encrypted_msg = self.private_key.encrypt_message(message, target_pubkey_hex)
        
        event = Event(
            public_key=self.public_key.hex(),
            content=encrypted_msg,
            kind=4,
            tags=[["p", target_pubkey_hex]]
        )
        self.private_key.sign_event(event)
        
        event_json = json.dumps(["EVENT", event.to_dict()])
        
        # Broadcast to all connected relays
        success_count = 0
        for ws in self.connected_websockets:
            try:
                await ws.send(event_json)
                success_count += 1
            except Exception as e:
                self.log(f"Failed to send to a relay: {str(e)}")
                
        self.log(f"Sent DM to {target_pubkey_hex} across {success_count} relays.")

    def start_background_loop(self):
        """Starts the async listener in the background (fire and forget)."""
        if self._loop_task is None:
            self._loop_task = asyncio.create_task(self.connect_and_listen())
