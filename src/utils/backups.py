"""
GuerillaBackup - Secure, compressed snapshots for Manas.
Phase 24: Resurrection Protocol.
"""

import tarfile
import logging
import time
from pathlib import Path
from typing import Optional, List

try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Random import get_random_bytes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)

class GuerillaBackup:
    """
    Encryption & Compression engine for system-wide snapshots.
    """
    def __init__(self, data_dir: str, backup_dir: str = None):
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir) if backup_dir else self.data_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.passphrase = "manas_sovereign_2026" # Default, should be user-sharded later

    def create_snapshot(self, label: str = "daily") -> Optional[Path]:
        """Compress and encrypt the data directory."""
        if not CRYPTO_AVAILABLE:
            logger.error("GuerillaBackup: pycryptodome not installed! Cannot create encrypted backup.")
            return None

        timestamp = int(time.time())
        filename = f"manas_soul_{label}_{timestamp}.tar.gz.enc"
        output_path = self.backup_dir / filename
        temp_tar = self.backup_dir / f"temp_{timestamp}.tar.gz"

        try:
            # 1. Compress
            logger.info(f"GuerillaBackup: Compressing {self.data_dir}...")
            with tarfile.open(temp_tar, "w:gz") as tar:
                # Add all files in data_dir, excluding existing backups
                for item in self.data_dir.iterdir():
                    if item.name != "backups":
                        tar.add(item, arcname=item.name)

            # 2. Encrypt
            logger.info("GuerillaBackup: Encrypting snapshot...")
            salt = get_random_bytes(16)
            key = PBKDF2(self.passphrase, salt, dkLen=32, count=1000)
            cipher = AES.new(key, AES.MODE_GCM)
            
            with open(temp_tar, "rb") as f_in:
                plaintext = f_in.read()
                ciphertext, tag = cipher.encrypt_and_digest(plaintext)

            with open(output_path, "wb") as f_out:
                for x in (salt, cipher.nonce, tag, ciphertext):
                    f_out.write(x)

            # 3. Cleanup
            temp_tar.unlink()
            logger.info(f"✅ GuerillaBackup: Created secure snapshot: {filename}")
            return output_path

        except Exception as e:
            logger.error(f"❌ GuerillaBackup: Snapshot failed: {e}")
            if temp_tar.exists(): temp_tar.unlink()
            return None

    def restore_snapshot(self, snapshot_path: str, target_dir: str) -> bool:
        """Decrypt and extract a snapshot."""
        if not CRYPTO_AVAILABLE: return False
        
        path = Path(snapshot_path)
        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "rb") as f_in:
                salt = f_in.read(16)
                nonce = f_in.read(16)
                tag = f_in.read(16)
                ciphertext = f_in.read()

            key = PBKDF2(self.passphrase, salt, dkLen=32, count=1000)
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)

            temp_tar = target / "restore_temp.tar.gz"
            with open(temp_tar, "wb") as f_out:
                f_out.write(plaintext)

            with tarfile.open(temp_tar, "r:gz") as tar:
                tar.extractall(path=target)

            temp_tar.unlink()
            logger.info(f"✅ GuerillaBackup: Successfully resurrected soul from {path.name}")
            return True

        except Exception as e:
            logger.error(f"❌ GuerillaBackup: Resurrection failed: {e}")
            return False

    def list_snapshots(self) -> List[dict]:
        """List available soul seeds."""
        seeds = []
        for f in self.backup_dir.glob("*.enc"):
            seeds.append({
                "name": f.name,
                "size": f.stat().st_size,
                "created": f.stat().st_mtime,
                "path": str(f)
            })
        return sorted(seeds, key=lambda x: x["created"], reverse=True)

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    bak = GuerillaBackup(data_dir="data", backup_dir="data/backups")
    snap = bak.create_snapshot("test")
    if snap:
        bak.list_snapshots()
