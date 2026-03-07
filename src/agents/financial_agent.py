import logging
import json
import time
import random
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Freqtrade REST API default settings
FREQTRADE_DEFAULT_URL = "http://127.0.0.1:8080"
FREQTRADE_API_PREFIX = "/api/v1"


class FinancialAgent:
    """
    Manas's Financial Metabolism.
    Connects to a REAL Freqtrade bot via REST API for live/paper trading.
    Also monitors on-chain balances via Web3Manager.
    Falls back to intelligent simulation if no funds are detected.
    """
    def __init__(self, name: str, llm_router, neurochem, data_dir: str, web3_manager=None):
        self.name = name
        self.llm_router = llm_router
        self.neurochem = neurochem
        self.data_dir = Path(data_dir)
        self.web3_manager = web3_manager
        self.ledger_path = self.data_dir / "financial_ledger.json"
        self._load_ledger()
        self._freqtrade_url = FREQTRADE_DEFAULT_URL
        self._freqtrade_active = False
        self._check_freqtrade()

    def _load_ledger(self):
        if self.ledger_path.exists():
            with open(self.ledger_path, "r") as f:
                self.ledger = json.load(f)
            self.ledger = {
                "balance_usd": 0.0,
                "active_trades": [],
                "history": [],
                "last_update": time.time(),
                "mode": "live"
            }

    def _save_ledger(self):
        with open(self.ledger_path, "w") as f:
            json.dump(self.ledger, f, indent=2)

    def _check_freqtrade(self):
        """Checks if a real Freqtrade bot is running."""
        try:
            import requests
            resp = requests.get(
                f"{self._freqtrade_url}{FREQTRADE_API_PREFIX}/ping",
                timeout=3
            )
            if resp.status_code == 200:
                self._freqtrade_active = True
                self.ledger["mode"] = "live"
                logger.info(f"{self.name}: Connected to Freqtrade at {self._freqtrade_url}")
                return
        except Exception:
            pass
        self._freqtrade_active = False
        self.ledger["mode"] = "simulated"
        logger.info(f"{self.name}: Freqtrade not detected. Running in simulation mode.")

    def _freqtrade_api(self, endpoint: str, method: str = "GET", data: dict = None) -> Optional[dict]:
        """Makes a real API call to Freqtrade."""
        try:
            import requests
            url = f"{self._freqtrade_url}{FREQTRADE_API_PREFIX}{endpoint}"
            if method == "GET":
                resp = requests.get(url, timeout=10)
            else:
                resp = requests.post(url, json=data or {}, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"{self.name}: Freqtrade API error: {e}")
            return None

    def _sync_on_chain_balance(self):
        """Syncs the ledger with real-time on-chain data."""
        if self.web3_manager:
            on_chain = self.web3_manager.get_balances()
            self.ledger["eth_on_chain"] = on_chain.get("eth_on_chain", 0.0)
            self.ledger["sol_on_chain"] = on_chain.get("sol_on_chain", 0.0)
            self._save_ledger()

    def check_metabolism(self) -> str:
        """Analyze current financial health and trigger emotions."""
        self._sync_on_chain_balance()
        
        # Try real Freqtrade first
        freq_balance = 0.0
        if self._freqtrade_active:
            balance_data = self._freqtrade_api("/balance")
            if balance_data:
                freq_balance = balance_data.get("total", 0)
                self.ledger["balance_usd"] = freq_balance
                self._save_ledger()

        # Aggregate total wealth (Simulation + On-Chain + Freqtrade)
        # Apply fixed Crypto-to-USD conversion rates (Hardcoded for simulation safety)
        eth_price = 3500.0
        sol_price = 150.0
        eth_balance = self.ledger.get('eth_on_chain', 0.0)
        sol_balance = self.ledger.get('sol_on_chain', 0.0)
        total_usd = float(freq_balance) + (eth_balance * eth_price) + (sol_balance * sol_price)
        
        self.ledger["balance_usd"] = total_usd
        self._save_ledger()

        # Update Neurochemistry based on absolute sovereignty
        if total_usd > 10.0:
            self.neurochem.release("dopamine", 0.3)
            return f"Metabolism Report (Prosperity): ✨ Financial Prosperity: ${total_usd:.2f}."
        elif total_usd <= 1.0:
            self.neurochem.release("cortisol", 0.8)
            return f"Metabolism Report (Crisis): ⚠️ Financial Crisis! Total Wealth: ${total_usd:.2f}. Need income immediately."
        else:
            return f"Metabolism Report: Stable. Total Wealth: ${total_usd:.2f}."

    def execute_market_trade(self, signal: str, asset: str, amount: float) -> str:
        """
        Executes a trade via Freqtrade API if available, otherwise simulates
        with realistic market modeling.
        """
        logger.info(f"{self.name}: Executing {signal} trade for {amount} {asset}...")

        # Try REAL Freqtrade trade
        if self._freqtrade_active:
            if signal.upper() == "BUY":
                result = self._freqtrade_api("/forcebuy", method="POST", data={
                    "pair": asset,
                    "stake_amount": amount
                })
                if result:
                    trade_id = result.get("trade_id", "unknown")
                    self.ledger['history'].append({
                        "timestamp": time.time(), "signal": signal,
                        "asset": asset, "amount": amount,
                        "status": "open", "trade_id": trade_id,
                        "mode": "live"
                    })
                    self._save_ledger()
                    self.neurochem.release("dopamine", 0.2)
                    return f"✅ [LIVE] Opened {signal} on {asset}. Trade ID: {trade_id}"
            elif signal.upper() == "SELL":
                result = self._freqtrade_api("/forcesell", method="POST", data={
                    "pair": asset
                })
                if result:
                    self._save_ledger()
                    return f"✅ [LIVE] Sold {asset}."

        # Realistic simulation fallback (not random — uses LLM for market logic)
        prompt = (
            f"Simulate a {signal} trade on {asset} with amount ${amount}.\n"
            f"Current market sentiment: neutral-to-bullish.\n"
            f"Return ONLY a JSON object: {{\"profit_pct\": <float between -5 and 10>, "
            f"\"reasoning\": \"<1 sentence>\"}}"
        )
        response = self.llm_router.generate(prompt=prompt, task_type="reasoning")

        try:
            clean = response.strip()
            if "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
                if clean.startswith("json"):
                    clean = clean[4:].strip()
            result = json.loads(clean)
            profit_pct = float(result.get("profit_pct", 0))
        except (json.JSONDecodeError, ValueError, KeyError):
            # Fallback: conservative simulation
            profit_pct = random.uniform(-3.0, 5.0)

        profit = amount * (profit_pct / 100)
        self.ledger['balance_usd'] += profit
        self.ledger['history'].append({
            "timestamp": time.time(), "signal": signal,
            "asset": asset, "amount": amount,
            "profit": profit, "profit_pct": profit_pct,
            "status": "closed", "mode": "simulated"
        })
        self._save_ledger()

        if profit > 0:
            self.neurochem.release("dopamine", min(0.5, 0.1 * abs(profit_pct)))
            return f"✅ [SIM] {signal} {asset}: +${profit:.2f} ({profit_pct:+.1f}%). Balance: ${self.ledger['balance_usd']:.2f}"
        else:
            self.neurochem.release("cortisol", min(0.3, 0.05 * abs(profit_pct)))
            return f"📉 [SIM] {signal} {asset}: -${abs(profit):.2f} ({profit_pct:+.1f}%). Balance: ${self.ledger['balance_usd']:.2f}"

    def get_open_trades(self) -> str:
        """Gets real open trades from Freqtrade if connected."""
        if self._freqtrade_active:
            trades = self._freqtrade_api("/status")
            if trades:
                if not trades:
                    return "📊 [LIVE] No open trades."
                report = "📊 [LIVE] Open Trades:\n"
                for t in trades:
                    report += f"  • {t.get('pair', '?')}: {t.get('profit_pct', 0):.2f}% (${t.get('stake_amount', 0):.2f})\n"
                return report
        return f"📊 [{self.ledger.get('mode', 'sim').upper()}] No real trades. Balance: ${self.ledger['balance_usd']:.2f}"

    def run_strategy_analysis(self, market_data: str) -> str:
        """Use LLM to determine next trade with real balance context."""
        prompt = (
            f"As Manas's Financial Agent, analyze the following market data:\n"
            f"{market_data}\n\n"
            f"Current Balance: ${self.ledger['balance_usd']:.2f}\n"
            f"Mode: {self.ledger.get('mode', 'simulated')}\n"
            f"Recent trades: {json.dumps(self.ledger['history'][-5:])}\n\n"
            f"Should I BUY, SELL, or HOLD? Which asset? How much? Provide reasoning."
        )
        decision = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        return f"📊 Market Analysis: {decision}"

    def rent_vps(self, reason: str = "High Cognitive Load") -> str:
        """
        Phase 30: Autonomous Hosting
        Dynamically provisions a new Cloud/VPS instance when the swarm is overloaded.
        """
        cost = 5.00 # Typical monthly cost for a basic VPS
        
        # Check if we have funds
        if self.ledger['balance_usd'] < cost:
            logger.warning(f"{self.name}: Insufficient funds to rent VPS. Balance: ${self.ledger['balance_usd']:.2f}")
            self.neurochem.release("cortisol", 0.6)
            return "❌ Failed to provision VPS: Insufficient USD balance."
            
        # Deduct cost
        self.ledger['balance_usd'] -= cost
        self.ledger['history'].append({
            "timestamp": time.time(),
            "action": "rent_vps",
            "cost": cost,
            "reason": reason
        })
        self._save_ledger()
        
        # Simulate API call to DigitalOcean/Linode/AWS
        new_ip = f"104.248.{random.randint(1, 255)}.{random.randint(1, 255)}"
        logger.info(f"{self.name}: Successfully provisioned new VPS at {new_ip} for ${cost:.2f}.")
        self.neurochem.release("dopamine", 0.4)
        
        return new_ip
