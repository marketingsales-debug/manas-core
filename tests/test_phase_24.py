"""
Phase 24 Verification Suite
Tests the GuerillaBackup encryption and restoration process.
"""

import unittest
import os
import shutil
import time
from pathlib import Path

# Add project root to path
import sys
sys.path.append(os.getcwd())

from src.utils.backups import GuerillaBackup

class TestPhase24(unittest.TestCase):
    def setUp(self):
        self.data_dir = Path("tmp_test_soul")
        self.backup_dir = Path("tmp_test_backups")
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create some dummy brain data
        (self.data_dir / "memories.db").write_text("dummy_memory_data")
        (self.data_dir / "knowledge.json").write_text('{"entities": ["Manas"]}')
        
        self.bak = GuerillaBackup(str(self.data_dir), str(self.backup_dir))

    def tearDown(self):
        if self.data_dir.exists(): shutil.rmtree(self.data_dir)
        if self.backup_dir.exists(): shutil.rmtree(self.backup_dir)

    def test_01_snapshot_creation(self):
        """Verify encrypted snapshot creation."""
        snap_path = self.bak.create_snapshot("mission_alpha")
        self.assertIsNotNone(snap_path)
        self.assertTrue(snap_path.exists())
        self.assertIn("mission_alpha", snap_path.name)
        self.assertTrue(snap_path.name.endswith(".enc"))

    def test_02_resurrection(self):
        """Verify full state restoration from an encrypted seed."""
        snap_path = self.bak.create_snapshot("resurrection_test")
        
        # 1. Simluate Datapocalypse (delete data)
        for f in self.data_dir.glob("*"):
            if f.is_file(): f.unlink()
            
        self.assertFalse((self.data_dir / "memories.db").exists())
        
        # 2. Resurrect
        success = self.bak.restore_snapshot(str(snap_path), str(self.data_dir))
        self.assertTrue(success)
        
        # 3. Verify Integrity
        self.assertTrue((self.data_dir / "memories.db").exists())
        self.assertEqual((self.data_dir / "memories.db").read_text(), "dummy_memory_data")
        self.assertIn("Manas", (self.data_dir / "knowledge.json").read_text())

if __name__ == "__main__":
    unittest.main()
