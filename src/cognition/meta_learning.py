"""
Meta-Learning System (Phase 4).

Allows Manas to:
1. Optimize its own cognitive parameters via A/B testing (learning rate, memory TTL, etc.)
2. Run AutoML routines using the CoderAgent to build custom internal models.
3. Track and evaluate performance metrics over time to guide self-improvement.
"""

import os
import json
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MetaLearningSystem:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), "manas", "data")
        self.params_file = os.path.join(self.data_dir, "cognitive_params.json")
        self.metrics_file = os.path.join(self.data_dir, "meta_metrics.json")
        
        self.active_experiment: Dict[str, Any] = None
        self.params = self._load_params()
        self.metrics_history = self._load_metrics()

    def _default_params(self) -> dict:
        return {
            "sleep_debt_decay": 0.05,
            "memory_consolidation_threshold": 0.5,
            "episodic_ttl_days": 7,
            "working_memory_capacity": 7,
            "curiosity_baseline": 0.4
        }

    def _load_params(self) -> dict:
        if os.path.exists(self.params_file):
            try:
                with open(self.params_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cognitive params: {e}")
        return self._default_params()

    def _save_params(self):
        os.makedirs(os.path.dirname(self.params_file), exist_ok=True)
        with open(self.params_file, "w") as f:
            json.dump(self.params, f, indent=2)

    def _load_metrics(self) -> list:
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def get_param(self, name: str, default: Any = None) -> Any:
        return self.params.get(name, default)

    # ─────────────────────────────────────────────────────────
    # A/B Testing
    # ─────────────────────────────────────────────────────────

    def start_ab_test(self, param_name: str, variant_value: float, duration_hours: int = 24):
        """Start a cognitive A/B test to see if a new parameter value improves performance."""
        if self.active_experiment:
            logger.warning(f"Experiment already running on {self.active_experiment['param']}")
            return False

        if param_name not in self.params:
            logger.warning(f"Parameter '{param_name}' not found.")
            return False

        control_value = self.params[param_name]
        self.active_experiment = {
            "param": param_name,
            "control": control_value,
            "variant": variant_value,
            "start_time": time.time(),
            "duration_sec": duration_hours * 3600,
            "metrics": {
                "control_score": 0.0,
                "variant_score": 0.0,
                "evaluations": 0
            }
        }
        
        # Apply the variant
        self.params[param_name] = variant_value
        self._save_params()
        
        logger.info(f"Started A/B test on {param_name}: Control={control_value}, Variant={variant_value}")
        return True

    def record_metric_event(self, performance_score: float):
        """Record a performance event. Plugs into the active experiment if one is running."""
        history_entry = {
            "timestamp": time.time(),
            "score": performance_score
        }
        self.metrics_history.append(history_entry)
        
        # Only keep last 1000 records
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
            
        with open(self.metrics_file, "w") as f:
            json.dump(self.metrics_history, f)
            
        # Update active experiment
        if self.active_experiment:
            exp = self.active_experiment
            # Very simplified: just sum the scores to the variant side 
            # (in a real A/B we'd alternate or do sequential testing)
            exp["metrics"]["variant_score"] += performance_score
            exp["metrics"]["evaluations"] += 1
            
            # Check if experiment is done
            if time.time() - exp["start_time"] > exp["duration_sec"] or exp["metrics"]["evaluations"] > 100:
                self.conclude_ab_test()

    def conclude_ab_test(self):
        """End the experiment and pick the winner."""
        if not self.active_experiment:
            return

        exp = self.active_experiment
        v_score = exp["metrics"]["variant_score"]
        # In this simplified model we compare variant against a fixed historical baseline
        # Let's say baseline was 0.5 expected score per evaluation
        baseline_score = 0.5 * exp["metrics"]["evaluations"]
        
        if v_score > baseline_score:
            logger.info(f"A/B Test WON! Keeping {exp['param']} = {exp['variant']}")
            # Keep variant (already applied)
        else:
            logger.info(f"A/B Test LOST. Reverting {exp['param']} = {exp['control']}")
            # Revert to control
            self.params[exp["param"]] = exp["control"]
            self._save_params()
            
        self.active_experiment = None

    # ─────────────────────────────────────────────────────────
    # AutoML Integration
    # ─────────────────────────────────────────────────────────

    def run_automl_cycle(self, coder_agent, dataset_path: str, target_metric: str = "accuracy") -> dict:
        """
        Use the CoderAgent to completely autonomously build, train, and optimize
        a new machine learning model for Manas's internal organs.
        """
        if not coder_agent:
            return {"success": False, "error": "No CoderAgent provided."}
            
        task = f"""
We need to evolve a new internal machine learning model using an AutoML-Zero inspired approach.
1. Read the dataset located at: {dataset_path}
2. Write a Python script to build, train, and evaluate a small model (e.g. scikit-learn or PyTorch).
3. Maximize the {target_metric}. Try different hyper-parameters or architectures.
4. Save the absolute best model you find to {self.data_dir}/custom_model.pkl.
5. Save the best metrics to {self.data_dir}/model_metrics.json.
Your environment has bash, python_repl, file_reader, file_writer. Run it iteratively until you're satisfied with the {target_metric}.
"""
        logger.info("Starting AutoML cycle via CoderAgent...")
        result = coder_agent.run(task)
        
        return {
            "success": result.success,
            "agent_output": result.output,
            "logs": result.logs
        }
