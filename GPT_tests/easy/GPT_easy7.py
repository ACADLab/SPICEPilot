from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
from PySpice.Probe.Plot import plot

# Create the circuit
circuit = Circuit('3-Stage CMOS Ring Oscillator')

# Supply voltage (Vdd)
circuit.V(1, 'Vdd', circuit.gnd, 5@u_V)

# First Inverter
# PMOS transistor
circuit.MOSFET('PM1', 'out1', 'input', 'Vdd', 'Vdd', model='PMOS')
# NMOS transistor
circuit.MOSFET('NM1', 'out1', 'input', circuit.gnd, circuit.gnd, model='NMOS')

# Second Inverter (input comes from the first inverter's output)
# PMOS transistor
circuit.MOSFET('PM2', 'out2', 'out1', 'Vdd', 'Vdd', model='PMOS')
# NMOS transistor
circuit.MOSFET('NM2', 'out2', 'out1', circuit.gnd, circuit.gnd, model='NMOS')

# Third Inverter (input comes from the second inverter's output)
# PMOS transistor
circuit.MOSFET('PM3', 'output', 'out2', 'Vdd', 'Vdd', model='PMOS')
# NMOS transistor
circuit.MOSFET('NM3', 'output', 'out2', circuit.gnd, circuit.gnd, model='NMOS')

# Feedback from the third inverter output to the first inverter input
circuit.R(1, 'output', 'input', 1@u_kΩ)  # Small resistor to stabilize feedback

# Define MOSFET models (NMOS and PMOS)
circuit.model('NMOS', 'nmos', kp=120e-6, vto=1, lambda_=0.02, w=10e-6, l=1e-6)
circuit.model('PMOS', 'pmos', kp=60e-6, vto=-1, lambda_=0.02, w=20e-6, l=1e-6)

# Simulation settings: Transient analysis for a sufficient time to observe oscillation
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=1@u_ps, end_time=50@u_ns)  # Increased simulation time

print(circuit)
