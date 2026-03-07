"""
liquid.py - Liquid Neural Network (LNN) Component for Manas.

Implements continuous-time neural ODEs where the time constant (tau) 
is dynamically dependent on the input, allowing the network to adapt
fluidly to evolving time-series data without discrete spikes.

Phase 26: Neural Architecture V2
"""

import numpy as np
from typing import Dict

class LiquidNode:
    """
    A single node in a Liquid Neural Network.
    Follows ODE: dx/dt = - [x(t)/tau_sys + f(x, I)/tau_syn] + I(t)
    where tau is dynamic.
    """
    def __init__(self, node_id: str, baseline_tau: float = 0.5):
        self.id = node_id
        self.state: float = 0.0      # Continuous state x(t)
        self.tau_sys: float = baseline_tau # Baseline time constant
        self.inputs: float = 0.0     # Accumulated inputs I(t)
        
    def add_input(self, value: float):
        self.inputs += value

    def step(self, dt: float, neurotransmitters: Dict[str, float]) -> float:
        """
        Euler integration step for the LiquidODE.
        The "liquid" property: The local time constant shifts dynamically
        based on the input and physiological state (Serotonin fluidifies, Cortisol solidifies).
        """
        # Dynamic time constant modulation
        # Serotonin -> Increases persistence/fluidity
        # Cortisol -> Decreases tau, making it sharp and reactive
        fluidity = neurotransmitters.get("serotonin", 0.5)
        sharpness = neurotransmitters.get("cortisol", 0.5)
        
        dynamic_tau = self.tau_sys * (1.0 + fluidity) / (1.0 + sharpness)
        dynamic_tau = max(0.01, dynamic_tau) # Prevent div/0

        # Liquid ODE: dx/dt = -x(t)/tau_dynamic + I(t)
        # We also model a non-linear squashing f(x, I) implicitly via tanh bounded output
        dx_dt = -(self.state / dynamic_tau) + self.inputs
        
        # Euler update
        self.state += dx_dt * dt
        
        # Apply biological bounds [-1.0, 1.0] representing continuous membrane potential
        self.state = np.tanh(self.state)
        
        # Reset input accumulator for next timestep
        self.inputs = 0.0
        
        return self.state

class LiquidCluster:
    """
    A structural brain module powered entirely by Continuous Liquid Nodes.
    """
    def __init__(self, name: str, size: int):
        self.name = name
        self.nodes = [LiquidNode(f"{name}_lnn_{i}", baseline_tau=np.random.uniform(0.1, 1.0)) for i in range(size)]
        
        # fully connected continuous adjacency matrix (weights NxN)
        self.weights = np.random.normal(0.0, 0.2, (size, size))
        np.fill_diagonal(self.weights, -0.1) # slight self-inhibition to prevent explosion
        
    def stimulate(self, pattern: np.ndarray):
        """Inject vector data into the liquid nodes."""
        assert len(pattern) == len(self.nodes)
        for i, val in enumerate(pattern):
            self.nodes[i].add_input(val)

    def step(self, dt: float, neurotransmitters: Dict[str, float]) -> np.ndarray:
        """
        Advance the entire liquid cluster by dt.
        Returns the continuous state vector.
        """
        # 1. State vector from previous step
        current_states = np.array([n.state for n in self.nodes])
        
        # 2. Liquid cross-talk (Continuous message passing within cluster)
        internal_inputs = np.dot(self.weights, current_states)
        for i, val in enumerate(internal_inputs):
             self.nodes[i].add_input(val)

        # 3. Euler step all nodes
        new_states = np.array([n.step(dt, neurotransmitters) for n in self.nodes])
        return new_states

    def get_activity(self) -> float:
        """Get the RMS continuous energy of the liquid."""
        states = np.array([n.state for n in self.nodes])
        return float(np.sqrt(np.mean(states**2)))

    def get_average_tau(self) -> float:
         # Return average baseline tau for reporting
         return float(np.mean([n.tau_sys for n in self.nodes]))

    def optimize(self, learning_rate: float = 0.01, decay: float = 0.001) -> dict:
        """
        Continuous Hebbian-like plasticity applied during sleep.
        Strengthens connections between nodes that fire together, 
        and slowly decays unused connections.
        Also optimizes baseline taus.
        """
        current_states = np.array([n.state for n in self.nodes])
        
        # Outer product of states gives the co-activation matrix
        co_activation = np.outer(current_states, current_states)
        
        # Hebbian update rule: dW = lr * (x_i * x_j) - decay * W
        weight_update = (learning_rate * co_activation) - (decay * self.weights)
        
        self.weights += weight_update
        
        # Keep diagonal negative to prevent explosion
        np.fill_diagonal(self.weights, -0.1)
        
        # Clip weights to prevent runaway
        self.weights = np.clip(self.weights, -2.0, 2.0)
        
        # Optimize baseline taus towards stability
        for n in self.nodes:
            if abs(n.state) > 0.8:
                n.tau_sys = min(2.0, n.tau_sys + 0.05)
            elif abs(n.state) < 0.1:
                n.tau_sys = max(0.1, n.tau_sys - 0.05)
                
        return {
            "mean_weight_change": float(np.mean(np.abs(weight_update))),
            "new_average_tau": self.get_average_tau()
        }
