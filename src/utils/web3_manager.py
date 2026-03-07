"""
Web3Manager - Lightweight wallet management for Manas.
Handles Ethereum and Solana address generation and public API balance fetching.
Phase 22: Financial Self-Sufficiency.
"""

import json
import logging
import secrets
import hashlib
from typing import Dict
from pathlib import Path

try:
    from eth_account import Account
    Account.enable_unaudited_hdwallet_features()
    ETH_AVAILABLE = True
except ImportError:
    ETH_AVAILABLE = False

try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    import base58
    SOL_AVAILABLE = True
except ImportError:
    SOL_AVAILABLE = False

logger = logging.getLogger(__name__)

class Web3Manager:
    """
    Manages Manas's decentralized identities and assets.
    """
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.credentials_path = self.data_dir / "credentials.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._load_credentials()

    def _load_credentials(self):
        """Load stored keys and addresses."""
        if self.credentials_path.exists():
            with open(self.credentials_path, "r") as f:
                self.credentials = json.load(f)
        else:
            self.credentials = {
                "eth": {"address": None, "private_key": None, "mnemonic": None},
                "sol": {"address": None, "private_key": None, "mnemonic": None},
                "last_sync": 0
            }

    def _save_credentials(self):
        """Save keys to disk."""
        with open(self.credentials_path, "w") as f:
            json.dump(self.credentials, f, indent=2)

    def ensure_wallets(self) -> Dict[str, str]:
        """Ensure both ETH and SOL wallets exist. Generates them if missing."""
        changed = False
        
        # 1. Ethereum (secp256k1)
        if not self.credentials["eth"]["address"] and ETH_AVAILABLE:
            acct, mnemonic = Account.create_with_mnemonic()
            self.credentials["eth"] = {
                "address": acct.address,
                "private_key": acct.key.hex(),
                "mnemonic": mnemonic
            }
            changed = True
            logger.info(f"Web3Manager: Generated new ETH wallet: {acct.address}")

        # 2. Solana (Ed25519) - Real Mainnet Generation via solders
        if not self.credentials["sol"]["address"] and SOL_AVAILABLE:
            kp = Keypair()
            addr = str(kp.pubkey())
            # Store private key as base58 string (standard format)
            priv_key = base58.b58encode(bytes(kp)).decode('utf-8')
            
            self.credentials["sol"] = {
                "address": addr,
                "private_key": priv_key,
                "mnemonic": "Generated via solders.keypair"
            }
            changed = True
            logger.info(f"Web3Manager: Generated new SOL wallet: {addr}")

        if changed:
            self._save_credentials()
            
        return {
            "eth": self.credentials["eth"]["address"],
            "sol": self.credentials["sol"]["address"]
        }

    def get_balances(self) -> Dict[str, float]:
        """
        Fetch balances via public APIs.
        Note: These are public endpoints and might be rate-limited.
        """
        balances = {"eth_on_chain": 0.0, "sol_on_chain": 0.0}
        
        eth_addr = self.credentials["eth"]["address"]
        if eth_addr and ETH_AVAILABLE:
            try:
                # Etherscan free API (might need key, but some public nodes exist)
                # Fallback to a block explorer scraper or simulation if no key
                # For Phase 22, we simulate the 'fetch' but establish the pipeline
                balances["eth_on_chain"] = 0.0 # Placeholder for real fetch
            except Exception as e:
                logger.warning(f"Web3Manager: ETH balance fetch failed: {e}")
                
        sol_addr = self.credentials["sol"]["address"]
        if sol_addr and SOL_AVAILABLE:
            try:
                import requests
                # Use public Solana mainnet RPC
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [sol_addr]
                }
                resp = requests.post("https://api.mainnet-beta.solana.com", json=payload, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    lamports = data.get("result", {}).get("value", 0)
                    balances["sol_on_chain"] = lamports / 1e9  # Convert Lamports to SOL
            except Exception as e:
                logger.warning(f"Web3Manager: SOL balance fetch failed: {e}")

        return balances

    def get_wallet_info(self) -> Dict[str, Dict]:
        """Returns public info about wallets."""
        return {
            "eth": {"address": self.credentials["eth"]["address"]},
            "sol": {"address": self.credentials["sol"]["address"]}
        }

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    mgr = Web3Manager(data_dir="data")
    wallets = mgr.ensure_wallets()
    print(f"Addresses: {wallets}")
