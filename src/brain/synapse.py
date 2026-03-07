"""
Synapses - Connections between neurons with STDP learning.

"Neurons that fire together, wire together" — Donald Hebb

STDP (Spike-Timing Dependent Plasticity):
- If neuron A fires BEFORE neuron B -> strengthen connection (A caused B)
- If neuron A fires AFTER neuron B -> weaken connection (wrong order)
- This is how the brain learns without backpropagation

This is fundamentally different from AI gradient descent.
The brain learns through timing, not math.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class SynapseState:
    """State of a synapse (connection between two neurons)."""
    weight: float = 0.5            # connection strength
    delay: float = 0.001           # signal travel time (1ms like real axons)
    max_weight: float = 1.0
    min_weight: float = 0.0
    neurotransmitter_type: str = "glutamate"  # excitatory default


class Synapse:
    """
    A connection between two neurons.

    Real synapses:
    - Have different strengths (weights)
    - Have signal delay (axon length)
    - Release neurotransmitters
    - Strengthen or weaken based on activity (plasticity)
    """

    def __init__(
        self,
        pre_neuron_id: str,
        post_neuron_id: str,
        weight: float = 0.5,
        delay: float = 0.001,
        neurotransmitter_type: str = "glutamate",
    ):
        self.pre_neuron_id = pre_neuron_id
        self.post_neuron_id = post_neuron_id
        self.state = SynapseState(
            weight=weight,
            delay=delay,
            neurotransmitter_type=neurotransmitter_type,
        )
        self._pending_spikes: list[float] = []  # spikes in transit

    def transmit(self, spike_time: float) -> Optional[float]:
        """
        Transmit a spike. Returns the arrival time.
        Spike travels along the axon with a delay.
        """
        arrival_time = spike_time + self.state.delay
        self._pending_spikes.append(arrival_time)
        return arrival_time

    def deliver(self, current_time: float) -> float:
        """
        Deliver any spikes that have arrived. Returns total current.
        """
        delivered_current = 0.0
        remaining = []
        for arrival in self._pending_spikes:
            if current_time >= arrival:
                delivered_current += self.state.weight
            else:
                remaining.append(arrival)
        self._pending_spikes = remaining

        # Inhibitory synapses send negative current
        if self.state.neurotransmitter_type == "gaba":
            delivered_current *= -1.0

        return delivered_current


class SynapticPlasticity:
    """
    STDP - Spike-Timing Dependent Plasticity.

    The brain's learning rule:
    - Pre fires before Post (causal) -> STRENGTHEN (LTP)
    - Pre fires after Post (anti-causal) -> WEAKEN (LTD)
    - Closer in time -> bigger change

    This creates associations: things that happen together get linked.
    Fear learning: pain neuron fires after danger neuron -> connection strengthens
    -> next time danger signal comes, fear response is faster
    """

    def __init__(
        self,
        learning_rate_potentiation: float = 0.01,  # strengthen rate
        learning_rate_depression: float = 0.012,     # weaken rate (slightly stronger)
        time_window: float = 0.02,                   # 20ms STDP window
    ):
        self.lr_pot = learning_rate_potentiation
        self.lr_dep = learning_rate_depression
        self.time_window = time_window

    def update(
        self,
        synapse: Synapse,
        pre_spike_time: float,
        post_spike_time: float,
        dopamine_level: float = 0.5,
    ) -> float:
        """
        Apply STDP learning rule.

        Dopamine modulates learning:
        - High dopamine (reward) -> amplifies strengthening
        - Low dopamine (no reward) -> allows weakening

        Returns the weight change.
        """
        dt = post_spike_time - pre_spike_time

        if abs(dt) > self.time_window:
            return 0.0  # outside learning window

        if dt > 0:
            # Pre before Post -> strengthen (LTP)
            # Exponential decay: closer timing = bigger change
            dw = self.lr_pot * np.exp(-dt / self.time_window)
            # Dopamine amplifies potentiation (reward learning)
            dw *= (0.5 + dopamine_level)
        else:
            # Post before Pre -> weaken (LTD)
            dw = -self.lr_dep * np.exp(dt / self.time_window)
            # Low dopamine allows depression
            dw *= (1.5 - dopamine_level)

        # Apply weight change with bounds
        old_weight = synapse.state.weight
        synapse.state.weight = np.clip(
            synapse.state.weight + dw,
            synapse.state.min_weight,
            synapse.state.max_weight,
        )

        return synapse.state.weight - old_weight


class HebbianPlasticity:
    """
    Simple Hebbian learning: "fire together, wire together"

    Used for fast pattern learning in hippocampus.
    Simpler than STDP but good for memory formation.
    """

    def __init__(self, learning_rate: float = 0.005):
        self.lr = learning_rate

    def update(
        self,
        synapse: Synapse,
        pre_active: bool,
        post_active: bool,
        modulation: float = 1.0,
    ) -> float:
        """Strengthen if both active, weaken if only pre is active."""
        if pre_active and post_active:
            dw = self.lr * modulation
        elif pre_active and not post_active:
            dw = -self.lr * 0.5 * modulation
        else:
            dw = 0.0

        old_weight = synapse.state.weight
        synapse.state.weight = np.clip(
            synapse.state.weight + dw,
            synapse.state.min_weight,
            synapse.state.max_weight,
        )
        return synapse.state.weight - old_weight
