"""
Synapse Test Module
A simple module designed to be optimized by the PlasticityEngine.
"""

def slow_calculation(n):
    # This is a very inefficient way to sum numbers
    res = 0
    for i in range(n):
        res = res + i
    return res

def get_metadata():
    return {"version": "1.0.0", "name": "synapse_test"}
