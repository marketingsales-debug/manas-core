"""
MLX Local Fine-Tuning Module
Phase 35.5: Zero-Budget Apple Silicon Ingestion Plan

This module allows Manas to autonomously fine-tune his own neural weights 
(via LoRA adapters) on a local Apple M-series Mac using the abstract "dreams"
he generated during the night.

Requirements:
    pip install mlx mlx-lm
"""

import json
import logging
import subprocess
import shutil
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class MLXFinetuner:
    """
    Manages autonomous local LoRA training on Apple Silicon.
    """
    
    def __init__(self, data_dir: str, base_model: str = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"):
        self.data_dir = Path(data_dir)
        self.curriculum_dir = self.data_dir / "curriculum"
        self.adapters_dir = self.data_dir / "models" / "adapters"
        self.adapters_dir.mkdir(parents=True, exist_ok=True)
        self.base_model = base_model
        
    def _prepare_dataset(self) -> Path:
        """
        Converts the raw `dream_dataset.jsonl` (Instruction-Response format)
        into the Chat format required by MLX-LM LoRA training.
        """
        raw_dataset = self.curriculum_dir / "dream_dataset.jsonl"
        if not raw_dataset.exists():
            return None
            
        train_path = self.curriculum_dir / "train.jsonl"
        valid_path = self.curriculum_dir / "valid.jsonl"
        
        examples = []
        with open(raw_dataset, "r") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    # Convert to conversational MLX format
                    if "instruction" in data and "response" in data:
                        mlx_format = {
                            "messages": [
                                {"role": "user", "content": data["instruction"]},
                                {"role": "assistant", "content": data["response"]}
                            ]
                        }
                        examples.append(mlx_format)
                except json.JSONDecodeError:
                    pass
                    
        if len(examples) < 10:
            logger.warning("MLXFinetuner: Not enough dreams to train (Need at least 10).")
            return None
            
        # 90/10 split
        split_idx = int(len(examples) * 0.9)
        train_set = examples[:split_idx]
        valid_set = examples[split_idx:]
        
        with open(train_path, "w") as f:
            for ex in train_set: f.write(json.dumps(ex) + "\n")
            
        with open(valid_path, "w") as f:
            for ex in valid_set: f.write(json.dumps(ex) + "\n")
            
        logger.info(f"MLXFinetuner: Prepared {len(train_set)} train and {len(valid_set)} validation dreams.")
        return self.curriculum_dir

    def run_nightly_training(self) -> str:
        """
        Executes the LoRA fine-tuning process.
        Intended to run asynchronously during deep sleep (3 AM).
        """
        logger.info("🧠 MLXFinetuner: Initiating structural neural plasticity (LoRA Training)...")
        
        try:
            import mlx
            import mlx.core as mx
        except ImportError:
            return "❌ Training aborted: `mlx` and `mlx-lm` packages are not installed on this system."
            
        dataset_dir = self._prepare_dataset()
        if not dataset_dir:
            return "❌ Training aborted: Insufficient dream data."
            
        adapter_output = self.adapters_dir / f"manas_dream_lora_{int(time.time())}"
            
        # Execute MLX LM default LoRA script using subprocess.
        # This prevents blocking the main Python process's memory space and isolates GPU RAM.
        cmd = [
            "python3", "-m", "mlx_lm.lora",
            "--model", self.base_model,
            "--train",
            "--data", str(dataset_dir),
            "--batch-size", "2",
            "--lora-layers", "4",
            "--iters", "100",
            "--adapter-path", str(adapter_output)
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        try:
            # We run it synchronously here assuming the sleep cycle manager calls this in a background thread
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("✅ Neural Plasticity Complete. New reflexes baked into adapter.")
            
            # Wipe old dataset to start dreaming fresh
            raw = self.curriculum_dir / "dream_dataset.jsonl"
            if raw.exists():
                shutil.move(str(raw), str(self.curriculum_dir / "archived_dreams.jsonl.bak"))
                
            return f"✅ Training complete. New adapter saved to {adapter_output.name}"
            
        except subprocess.CalledProcessError as e:
            logger.error(f"MLX Training failed: {e.stderr}")
            return f"❌ Training crashed: {e.stderr[:200]}"
