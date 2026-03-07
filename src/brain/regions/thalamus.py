"""
Thalamus - The brain's central relay station.

In the real brain:
- ALL sensory input (except smell) passes through the thalamus
- Routes signals to the correct cortical region
- Filters irrelevant information (sensory gating)
- Controls what reaches consciousness (attentional gating)
- Pulvinar nucleus mediates attention between cortical areas
- Reticular nucleus provides inhibitory gating (sleep/wake)
- Thalamo-cortical loops create recurrent processing (consciousness)

For Manas:
- Every sensory signal is routed through here first
- Filters noise and irrelevant signals
- Amplifies attended signals
- Creates the thalamo-cortical loop needed for consciousness
- Controls sleep/wake gating
"""

import numpy as np
from ..neuron import NeuronCluster
from ...neurotransmitters.chemistry import NeurochemicalSystem


class ThalamicNucleus:
    """A single thalamic nucleus that routes to a specific cortical area."""

    def __init__(self, name: str, target_region: str, size: int = 32):
        self.name = name
        self.target_region = target_region
        self.cluster = NeuronCluster(f"thalamus_{name}", size=size, excitatory_ratio=0.85)
        self.gating_level: float = 1.0  # 1.0 = fully open, 0.0 = fully closed
        self.last_signal_strength: float = 0.0

    def relay(self, signal: np.ndarray, attention_weight: float = 1.0) -> np.ndarray:
        """
        Relay a signal with gating and attention modulation.

        Thalamic relay neurons do three things:
        1. Gate: allow or block signal based on sleep/wake state
        2. Modulate: amplify attended signals, suppress unattended
        3. Relay: pass the processed signal to cortex
        """
        # Apply gating (sleep/wake, reticular nucleus)
        gated = signal * self.gating_level

        # Apply attentional modulation (pulvinar)
        modulated = gated * (0.3 + attention_weight * 0.7)

        # Thalamic neurons add noise (biological variability)
        noise = np.random.normal(0, 0.02, len(modulated))
        output = np.clip(modulated + noise, 0.0, 1.0)

        self.last_signal_strength = float(np.mean(output))
        return output


class ReticularNucleus:
    """
    Thalamic Reticular Nucleus (TRN) - The gatekeeper.

    Wraps around the thalamus like a shell.
    Provides inhibitory control over all thalamic nuclei.
    Key role in:
    - Sleep/wake transitions (blocks sensory input during sleep)
    - Selective attention (inhibits irrelevant thalamic nuclei)
    - Sensory gating (prevents sensory overload)
    """

    def __init__(self):
        self.cluster = NeuronCluster("thalamus_reticular", size=48, excitatory_ratio=0.2)
        self.inhibition_map: dict[str, float] = {}
        self.global_inhibition: float = 0.0  # 0 = awake, 1 = deep sleep

    def compute_gating(self, nucleus_name: str, cortical_feedback: float = 0.0) -> float:
        """
        Compute gating level for a specific nucleus.

        Cortical feedback can override gating (top-down attention).
        """
        base_gate = 1.0 - self.global_inhibition
        specific_inhibition = self.inhibition_map.get(nucleus_name, 0.0)

        # Cortical feedback can partially override inhibition
        gate = base_gate * (1.0 - specific_inhibition) + cortical_feedback * 0.3
        return np.clip(gate, 0.0, 1.0)

    def set_sleep_level(self, level: float):
        """0.0 = fully awake, 1.0 = deep sleep."""
        self.global_inhibition = np.clip(level, 0.0, 1.0)

    def inhibit_nucleus(self, nucleus_name: str, amount: float):
        """Selectively inhibit a specific nucleus (attention gating)."""
        self.inhibition_map[nucleus_name] = np.clip(amount, 0.0, 1.0)

    def release_nucleus(self, nucleus_name: str):
        """Release inhibition on a nucleus."""
        self.inhibition_map.pop(nucleus_name, None)


class Thalamus:
    """
    The complete thalamus — central relay and gating station.

    All sensory input flows through here before reaching cortex.
    The thalamo-cortical loop is the basis of conscious awareness.
    """

    def __init__(self, neurochem: NeurochemicalSystem):
        self.neurochem = neurochem
        self.reticular = ReticularNucleus()

        # Create nuclei for each sensory modality and cortical target
        self.nuclei: dict[str, ThalamicNucleus] = {
            # Sensory relay nuclei
            "lgn": ThalamicNucleus("lgn", "visual_cortex", size=32),      # Lateral Geniculate (vision)
            "mgn": ThalamicNucleus("mgn", "auditory_cortex", size=24),    # Medial Geniculate (hearing)
            "vpn": ThalamicNucleus("vpn", "somatosensory", size=24),      # Ventral Posterior (touch)

            # Association nuclei
            "pulvinar": ThalamicNucleus("pulvinar", "attention", size=32),  # Attention routing
            "md": ThalamicNucleus("md", "prefrontal", size=28),            # Mediodorsal -> PFC
            "anterior": ThalamicNucleus("anterior", "hippocampus", size=20),# Anterior -> memory

            # Motor nuclei
            "va_vl": ThalamicNucleus("va_vl", "motor_cortex", size=24),    # Motor relay
        }

        # Attention weights per modality
        self.attention_weights: dict[str, float] = {
            "vision": 0.5,
            "hearing": 0.5,
            "touch": 0.5,
            "prefrontal": 0.5,
            "memory": 0.5,
            "motor": 0.5,
        }

        # Thalamo-cortical feedback buffer (cortex sends back to thalamus)
        self.cortical_feedback: dict[str, float] = {}

    def relay_sensory(self, modality: str, signal: np.ndarray) -> np.ndarray:
        """
        Relay a sensory signal through the appropriate nucleus.

        This is the main pathway: sense -> thalamus -> cortex
        """
        nucleus_map = {
            "vision": "lgn",
            "hearing": "mgn",
            "touch": "vpn",
        }

        nucleus_name = nucleus_map.get(modality)
        if not nucleus_name or nucleus_name not in self.nuclei:
            return signal  # Smell bypasses thalamus (like real brain)

        nucleus = self.nuclei[nucleus_name]

        # Compute gating from reticular nucleus
        cortical_fb = self.cortical_feedback.get(modality, 0.0)
        gate = self.reticular.compute_gating(nucleus_name, cortical_fb)
        nucleus.gating_level = gate

        # Get attention weight
        attention = self.attention_weights.get(modality, 0.5)

        # Norepinephrine increases thalamic relay gain (alertness)
        norepinephrine = self.neurochem.chemicals["norepinephrine"].level
        attention *= (0.7 + norepinephrine * 0.6)

        return nucleus.relay(signal, attention_weight=min(1.0, attention))

    def relay_association(self, target: str, signal: np.ndarray) -> np.ndarray:
        """Relay through association nuclei (prefrontal, memory, motor)."""
        nucleus_map = {
            "prefrontal": "md",
            "memory": "anterior",
            "motor": "va_vl",
            "attention": "pulvinar",
        }

        nucleus_name = nucleus_map.get(target)
        if not nucleus_name or nucleus_name not in self.nuclei:
            return signal

        nucleus = self.nuclei[nucleus_name]
        gate = self.reticular.compute_gating(nucleus_name)
        nucleus.gating_level = gate

        return nucleus.relay(signal, attention_weight=0.7)

    def receive_cortical_feedback(self, source: str, strength: float):
        """
        Receive feedback from cortex (top-down modulation).

        This creates the thalamo-cortical loop:
        thalamus -> cortex -> thalamus -> cortex...
        This recurrent loop is believed to be the basis of consciousness.
        """
        self.cortical_feedback[source] = np.clip(strength, 0.0, 1.0)

    def set_attention(self, modality: str, weight: float):
        """Direct attention to a modality (amplify its thalamic relay)."""
        self.attention_weights[modality] = np.clip(weight, 0.0, 1.0)

        # Inhibit other modalities (attention is competitive)
        for mod in self.attention_weights:
            if mod != modality:
                self.attention_weights[mod] *= 0.85

    def enter_sleep(self, depth: float = 0.8):
        """Transition to sleep state — gate most sensory input."""
        self.reticular.set_sleep_level(depth)

    def wake_up(self):
        """Full wake state — open all gates."""
        self.reticular.set_sleep_level(0.0)
        self.reticular.inhibition_map.clear()

    def get_state(self) -> dict:
        return {
            "nuclei_activity": {
                name: n.last_signal_strength for name, n in self.nuclei.items()
            },
            "attention_weights": dict(self.attention_weights),
            "sleep_level": self.reticular.global_inhibition,
            "cortical_feedback": dict(self.cortical_feedback),
            "gating": {
                name: self.reticular.compute_gating(name)
                for name in self.nuclei
            },
        }
