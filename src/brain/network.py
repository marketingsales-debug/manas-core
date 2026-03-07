"""
BrainNetwork - The full neural network connecting all brain regions.

This connects neuron clusters (brain regions) with synapses
and runs the simulation forward in time.
"""

import numpy as np
from .neuron import SpikingNeuron, NeuronCluster
from .liquid import LiquidCluster
from .synapse import Synapse, SynapticPlasticity, HebbianPlasticity


class BrainNetwork:
    """
    The complete spiking neural network brain.

    Connects multiple NeuronClusters (brain regions) and simulates
    the full network with spike propagation and learning.
    """

    def __init__(self, timestep: float = 0.001):
        """
        Args:
            timestep: simulation timestep in seconds (1ms default, like real neural simulation)
        """
        self.timestep = timestep
        self.current_time: float = 0.0
        self.clusters: dict[str, NeuronCluster] = {}
        self.liquid_clusters: dict[str, LiquidCluster] = {}
        
        self.synapses: list[Synapse] = []
        self.neuron_map: dict[str, SpikingNeuron] = {}
        self.stdp = SynapticPlasticity()
        self.hebbian = HebbianPlasticity()
        self._neurotransmitter_levels: dict[str, float] = {
            "dopamine": 0.5,
            "cortisol": 0.3,
            "serotonin": 0.5,
            "norepinephrine": 0.4,
        }
        self.spike_log: list[tuple[float, str]] = []  # (time, neuron_id)

    def add_cluster(self, cluster: NeuronCluster):
        """Add a spiking brain region."""
        self.clusters[cluster.name] = cluster
        for neuron in cluster.neurons:
            self.neuron_map[neuron.id] = neuron

    def add_liquid_cluster(self, cluster: LiquidCluster):
        """Add a continuous-time liquid brain region."""
        self.liquid_clusters[cluster.name] = cluster

    def connect_clusters(
        self,
        source_name: str,
        target_name: str,
        connection_probability: float = 0.1,
        weight_mean: float = 0.5,
        weight_std: float = 0.1,
        neurotransmitter: str = "glutamate",
    ):
        """
        Connect two brain regions with random synapses.

        connection_probability: fraction of possible connections to make
        (real brain has ~10% connectivity between regions)
        """
        source = self.clusters[source_name]
        target = self.clusters[target_name]

        for pre_neuron in source.neurons:
            for post_neuron in target.neurons:
                if np.random.random() < connection_probability:
                    weight = np.clip(
                        np.random.normal(weight_mean, weight_std),
                        0.01, 1.0,
                    )
                    nt = "gaba" if pre_neuron.state.is_inhibitory else neurotransmitter
                    synapse = Synapse(
                        pre_neuron_id=pre_neuron.id,
                        post_neuron_id=post_neuron.id,
                        weight=weight,
                        neurotransmitter_type=nt,
                    )
                    self.synapses.append(synapse)
                    pre_neuron.outgoing_synapses.append(synapse)
                    post_neuron.incoming_synapses.append(synapse)

    def set_neurotransmitter(self, name: str, level: float):
        """Set a neurotransmitter level (0.0 to 1.0)."""
        self._neurotransmitter_levels[name] = np.clip(level, 0.0, 1.0)

    def get_neurotransmitter_levels(self) -> dict[str, float]:
        return dict(self._neurotransmitter_levels)

    def stimulate_cluster(self, cluster_name: str, pattern: np.ndarray):
        """Send input to a specific brain region."""
        if cluster_name in self.clusters:
            self.clusters[cluster_name].stimulate(
                pattern, self._neurotransmitter_levels
            )

    def step(self) -> dict[str, np.ndarray]:
        """
        Run one timestep of the entire brain.

        1. Deliver pending spikes through synapses
        2. Advance Continuous Liquid ODEs (LNN)
        3. Step all discrete Neurons (SNN)
             - Apply Liquid Modulations to SNN Resting Potential
        4. Propagate new spikes
        5. Apply STDP learning

        Returns: dict of cluster_name -> spike_pattern
        """
        self.current_time += self.timestep
        
        # Phase 26: Advance Liquid Clusters
        liquid_states = {}
        for name, cluster in self.liquid_clusters.items():
            l_state = cluster.step(self.timestep, self._neurotransmitter_levels)
            liquid_states[name] = l_state

        # 1. Deliver spikes through synapses to post-synaptic neurons
        for synapse in self.synapses:
            current = synapse.deliver(self.current_time)
            if current != 0.0 and synapse.post_neuron_id in self.neuron_map:
                post_neuron = self.neuron_map[synapse.post_neuron_id]
                post_neuron.receive_input(current, self._neurotransmitter_levels)

        # 2. Step all neurons, collect spikes
        all_spikes: dict[str, np.ndarray] = {}
        fired_neurons: list[SpikingNeuron] = []
        
        # Calculate global liquid modulation 
        # (average LNN state shifts the SNN resting potential up or down)
        global_modulation = 0.0
        if self.liquid_clusters:
            total_l_state = sum(c.get_activity() for c in self.liquid_clusters.values())
            global_modulation = total_l_state * 0.1 # 10% modulatory strength

        for name, cluster in self.clusters.items():
            # Apply continuous liquid context to the discrete SNN architecture
            for neuron in cluster.neurons:
                # Modulate the base potential slightly, keeping it in biological 0.0-1.0 range
                neuron.state.potential = np.clip(neuron.state.potential + global_modulation * 0.05, 0.0, 1.2)

            spikes = cluster.step(self.current_time)
            all_spikes[name] = spikes

            for i, spike in enumerate(spikes):
                if spike != 0.0:
                    neuron = cluster.neurons[i]
                    fired_neurons.append(neuron)
                    self.spike_log.append((self.current_time, neuron.id))
                    
                    # Bridge: Spike to Liquid Impulse (Driving Force)
                    # Broad distribution of the impulse into the liquids
                    for l_cluster in self.liquid_clusters.values():
                        # Pick a random node to receive the spike impulse
                        idx = np.random.randint(0, len(l_cluster.nodes))
                        l_cluster.nodes[idx].add_input(0.5)

        # 3. Propagate new spikes through outgoing synapses
        for neuron in fired_neurons:
            for synapse in neuron.outgoing_synapses:
                synapse.transmit(self.current_time)

        # 4. Apply STDP learning for fired neurons
        for neuron in fired_neurons:
            for synapse in neuron.incoming_synapses:
                pre_neuron = self.neuron_map.get(synapse.pre_neuron_id)
                if pre_neuron and pre_neuron.state.last_spike_time > 0:
                    self.stdp.update(
                        synapse,
                        pre_neuron.state.last_spike_time,
                        neuron.state.last_spike_time,
                        self._neurotransmitter_levels.get("dopamine", 0.5),
                    )

        # Trim spike log
        if len(self.spike_log) > 10000:
            self.spike_log = self.spike_log[-5000:]

        return all_spikes

    def run(self, duration: float, input_fn=None) -> list[dict[str, np.ndarray]]:
        """
        Run simulation for a duration (in seconds).

        Args:
            duration: how long to simulate
            input_fn: optional function(time) -> dict of cluster_name: pattern
        """
        steps = int(duration / self.timestep)
        results = []

        for _ in range(steps):
            if input_fn:
                inputs = input_fn(self.current_time)
                if inputs:
                    for cluster_name, pattern in inputs.items():
                        self.stimulate_cluster(cluster_name, pattern)

            spikes = self.step()
            results.append(spikes)

        return results

    def get_cluster_activities(self) -> dict[str, float]:
        """Get activity level of each brain region."""
        activities = {name: cluster.get_activity() for name, cluster in self.clusters.items()}
        for name, cluster in self.liquid_clusters.items():
             activities[name] = cluster.get_activity()
        return activities

    def get_total_synapses(self) -> int:
        return len(self.synapses)

    def get_stats(self) -> dict:
        return {
            "total_neurons": len(self.neuron_map),
            "total_liquid_nodes": sum(len(c.nodes) for c in self.liquid_clusters.values()),
            "total_synapses": len(self.synapses),
            "total_snn_clusters": len(self.clusters),
            "total_lnn_clusters": len(self.liquid_clusters),
            "simulation_time": self.current_time,
            "neurotransmitters": dict(self._neurotransmitter_levels),
            "cluster_activities": self.get_cluster_activities(),
        }
