"""
Phase 22 Verification Suite
Tests every micro/macro function of the Web3Manager and FinancialAgent.
"""

import unittest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
import sys
sys.path.append(os.getcwd())

from src.utils.web3_manager import Web3Manager
from src.agents.financial_agent import FinancialAgent

class TestPhase22(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tmp_test_data")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.web3 = Web3Manager(str(self.test_dir))
        
        # Mock neurochem and llm_router
        self.neurochem = MagicMock()
        self.llm_router = MagicMock()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_01_web3_generation(self):
        """Micro-test: Check if wallets are generated and valid."""
        wallets = self.web3.ensure_wallets()
        self.assertIn("eth", wallets)
        self.assertIn("sol", wallets)
        self.assertTrue(wallets["eth"].startswith("0x"))
        self.assertTrue(wallets["sol"].startswith("SOL_"))
        
        # Check persistence
        self.assertTrue(self.web3.credentials_path.exists())
        with open(self.web3.credentials_path) as f:
            data = json.load(f)
            self.assertEqual(data["eth"]["address"], wallets["eth"])

    def test_02_web3_reload(self):
        """Micro-test: Check if keys are reloaded correctly."""
        wallets1 = self.web3.ensure_wallets()
        
        # New manager instance
        web3_v2 = Web3Manager(str(self.test_dir))
        wallets2 = web3_v2.get_wallet_info()
        
        self.assertEqual(wallets1["eth"], wallets2["eth"]["address"])
        self.assertEqual(wallets1["sol"], wallets2["sol"]["address"])

    def test_03_financial_agent_integration(self):
        """Macro-test: Check if FinancialAgent uses Web3Manager correctly."""
        agent = FinancialAgent("Tester", self.llm_router, self.neurochem, str(self.test_dir), web3_manager=self.web3)
        
        # Initial sync
        agent._sync_on_chain_balance()
        self.assertIn("eth_on_chain", agent.ledger)
        self.assertIn("sol_on_chain", agent.ledger)

    def test_04_metabolism_reaction(self):
        """Macro-test: Check if metabolism reacts to on-chain funds."""
        agent = FinancialAgent("Tester", self.llm_router, self.neurochem, str(self.test_dir), web3_manager=self.web3)
        
        # 1. Simulation: High on-chain balance (1 ETH = $2500)
        self.web3.get_balances = MagicMock(return_value={"eth_on_chain": 0.5, "sol_on_chain": 10.0})
        
        report = agent.check_metabolism()
        print(f"Metabolism Report (Prosperity): {report}")
        
        # Prosperity (0.5 * 2500 = 1250 > 200)
        self.assertIn("Prosperity", report)
        self.neurochem.release.assert_called_with("dopamine", 0.3)
        
        # 2. Simulation: Low balance
        self.web3.get_balances = MagicMock(return_value={"eth_on_chain": 0.0, "sol_on_chain": 0.0})
        agent.ledger["balance_usd"] = 5.0 # Total < 20
        
        self.neurochem.reset_mock()
        report = agent.check_metabolism()
        print(f"Metabolism Report (Crisis): {report}")
        
        self.assertIn("Crisis", report)
        self.neurochem.release.assert_called_with("cortisol", 0.4)

if __name__ == "__main__":
    unittest.main()
