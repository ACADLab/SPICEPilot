from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
from PySpice.Probe.Plot import plot

# Create the circuit
circuit = Circuit('CMOS Buffer')

# Supply voltage (Vdd)
circuit.V(1, 'Vdd', circuit.gnd, 5@u_V)

# Input signal
circuit.PulseVoltageSource('Vin', 'input', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=40@u_ns)

# First Inverter (Inverter 1)
# PMOS transistor
circuit.MOSFET('PM1', 'out1', 'input', 'Vdd', 'Vdd', model='PMOS')
# NMOS transistor
circuit.MOSFET('NM1', 'out1', 'input', circuit.gnd, circuit.gnd, model='NMOS')

# Second Inverter (Inverter 2, connected to the output of the first)
# PMOS transistor
circuit.MOSFET('PM2', 'output', 'out1', 'Vdd', 'Vdd', model='PMOS')
# NMOS transistor
circuit.MOSFET('NM2', 'output', 'out1', circuit.gnd, circuit.gnd, model='NMOS')

# Define MOSFET models (NMOS and PMOS)
circuit.model('NMOS', 'nmos', kp=120e-6, vto=1, lambda_=0.02, w=10e-6, l=1e-6)
circuit.model('PMOS', 'pmos', kp=60e-6, vto=-1, lambda_=0.02, w=20e-6, l=1e-6)

# Simulation settings: Transient analysis
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=1@u_ns, end_time=100@u_ns)

# Plot input and output signals
plt.figure()
plt.plot(analysis.time, analysis['input'], label='Vin (Input)')
plt.plot(analysis.time, analysis['output'], label='Vout (Buffered Output)')
plt.title('Transient Analysis of CMOS Buffer')
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')
plt.legend()
plt.grid()
plt.show()
