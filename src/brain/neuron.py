"""
Spiking Neurons - Leaky Integrate-and-Fire (LIF) Model

Real neurons work like this:
1. They receive electrical input from other neurons
2. Charge builds up (membrane potential)
3. When charge crosses threshold -> FIRE a spike
4. Reset and enter refractory period (can't fire again briefly)
5. Charge leaks away over time if no input (leaky)

This is NOT matrix multiplication like standard AI.
Each neuron is an individual unit that fires in real time.
"""

import numpy as np
import time
from typing import Optional
from dataclasses import dataclass


@dataclass
class NeuronState:
    """The internal state of a single spiking neuron."""
    potential: float = 0.0          # membrane potential (voltage)
    threshold: float = 1.0          # firing threshold
    reset_potential: float = 0.0    # potential after firing
    leak_rate: float = 0.95         # how fast charge leaks (0.95 = slow leak)
    refractory_time: float = 0.002  # 2ms refractory period (like real neurons)
    last_spike_time: float = 0.0    # when it last fired
    spike_count: int = 0            # total spikes fired
    is_inhibitory: bool = False     # inhibitory neurons suppress others


class SpikingNeuron:
    """
    A Leaky Integrate-and-Fire neuron.

    This simulates how a real biological neuron works:
    - Receives input current from synapses
    - Integrates (accumulates) charge
    - Fires a spike when threshold is reached
    - Leaks charge over time
    - Has a refractory period after firing
    """

    def __init__(
        self,
        neuron_id: str,
        threshold: float = 1.0,
        leak_rate: float = 0.95,
        is_inhibitory: bool = False,
        neurotransmitter_sensitivity: Optional[dict] = None,
    ):
        self.id = neuron_id
        self.state = NeuronState(
            threshold=threshold,
            leak_rate=leak_rate,
            is_inhibitory=is_inhibitory,
        )
        # How sensitive this neuron is to different neurotransmitters
        self.neurotransmitter_sensitivity = neurotransmitter_sensitivity or {
            "dopamine": 1.0,
            "cortisol": 1.0,
            "serotonin": 1.0,
            "norepinephrine": 1.0,
        }
        self.outgoing_synapses: list = []
        self.incoming_synapses: list = []
        self._spike_history: list[float] = []

    def receive_input(self, current: float, neurotransmitter_levels: Optional[dict] = None):
        """
        Receive electrical input. Neurotransmitters modulate the response.

        - Dopamine: amplifies reward-related signals
        - Cortisol: heightens sensitivity (fear/stress response)
        - Serotonin: dampens/stabilizes (calm/contentment)
        - Norepinephrine: sharpens attention/alertness
        """
        modulated_current = current

        if neurotransmitter_levels:
            # Cortisol (stress) lowers threshold -> fires more easily (hypervigilant)
            cortisol = neurotransmitter_levels.get("cortisol", 0.5)
            cortisol_effect = self.neurotransmitter_sensitivity["cortisol"] * cortisol
            self.state.threshold = max(0.3, 1.0 - (cortisol_effect * 0.4))

            # Dopamine amplifies signal (reward seeking)
            dopamine = neurotransmitter_levels.get("dopamine", 0.5)
            modulated_current *= (1.0 + dopamine * self.neurotransmitter_sensitivity["dopamine"] * 0.5)

            # Serotonin dampens signal (stability)
            serotonin = neurotransmitter_levels.get("serotonin", 0.5)
            modulated_current *= (1.0 - serotonin * self.neurotransmitter_sensitivity["serotonin"] * 0.2)

            # Norepinephrine sharpens (attention)
            norepinephrine = neurotransmitter_levels.get("norepinephrine", 0.5)
            modulated_current *= (1.0 + norepinephrine * self.neurotransmitter_sensitivity["norepinephrine"] * 0.3)

        self.state.potential += modulated_current

    def step(self, current_time: float) -> bool:
        """
        Advance one timestep. Returns True if the neuron fires a spike.

        This is the core simulation loop for each neuron:
        1. Check refractory period
        2. Apply leak
        3. Check if threshold crossed -> spike
        """
        # Refractory period — neuron can't fire right after firing
        if (current_time - self.state.last_spike_time) < self.state.refractory_time:
            return False

        # Leak: charge decays toward 0 over time (like real membrane)
        self.state.potential *= self.state.leak_rate

        # Check for spike
        if self.state.potential >= self.state.threshold:
            self._fire(current_time)
            return True

        return False

    def _fire(self, current_time: float):
        """Neuron fires a spike."""
        self.state.last_spike_time = current_time
        self.state.spike_count += 1
        self._spike_history.append(current_time)

        # Keep only last 1000 spikes for memory
        if len(self._spike_history) > 1000:
            self._spike_history = self._spike_history[-500:]

        # Reset potential
        self.state.potential = self.state.reset_potential

    def get_firing_rate(self, window: float = 1.0, current_time: Optional[float] = None) -> float:
        """Get firing rate (spikes per second) over a time window."""
        if not self._spike_history:
            return 0.0
        now = current_time or time.time()
        recent = [t for t in self._spike_history if (now - t) <= window]
        return len(recent) / window

    def reset(self):
        """Hard reset the neuron."""
        self.state.potential = 0.0
        self.state.last_spike_time = 0.0
        self._spike_history.clear()


class NeuronCluster:
    """
    A group of neurons that function together (like a cortical column).

    The brain is organized in clusters/columns of ~100-10000 neurons
    that work together on specific functions.
    """

    def __init__(self, name: str, size: int, excitatory_ratio: float = 0.8):
        """
        Create a cluster.

        Args:
            name: e.g. "prefrontal_decision", "amygdala_fear"
            size: number of neurons
            excitatory_ratio: 80% excitatory / 20% inhibitory (like real brain)
        """
        self.name = name
        self.neurons: list[SpikingNeuron] = []
        self.size = size

        n_excitatory = int(size * excitatory_ratio)
        for i in range(size):
            is_inhibitory = i >= n_excitatory
            neuron = SpikingNeuron(
                neuron_id=f"{name}_{i}",
                threshold=np.random.uniform(0.8, 1.2),  # biological variation
                leak_rate=np.random.uniform(0.93, 0.97),
                is_inhibitory=is_inhibitory,
            )
            self.neurons.append(neuron)

    def stimulate(self, input_pattern: np.ndarray, neurotransmitter_levels: Optional[dict] = None):
        """
        Send an input pattern to the cluster.
        input_pattern should be array of size len(neurons).
        """
        for i, neuron in enumerate(self.neurons):
            if i < len(input_pattern):
                neuron.receive_input(float(input_pattern[i]), neurotransmitter_levels)

    def step(self, current_time: float) -> np.ndarray:
        """Advance all neurons one timestep. Returns spike pattern."""
        spikes = np.zeros(self.size)
        for i, neuron in enumerate(self.neurons):
            if neuron.step(current_time):
                spikes[i] = -1.0 if neuron.state.is_inhibitory else 1.0
        return spikes

    def get_activity(self) -> float:
        """Get overall cluster activity (0.0 to 1.0)."""
        if not self.neurons:
            return 0.0
        total_potential = sum(n.state.potential for n in self.neurons)
        return min(1.0, max(0.0, total_potential / self.size))

    def get_spike_pattern(self, current_time: float, window: float = 0.1) -> np.ndarray:
        """Get the current firing pattern of the cluster."""
        return np.array([n.get_firing_rate(window, current_time) for n in self.neurons])
