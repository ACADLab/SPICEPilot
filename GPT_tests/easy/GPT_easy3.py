from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
from PySpice.Probe.Plot import plot

# Create the circuit
circuit = Circuit('CMOS NOR Gate')

# Supply voltage (Vdd)
circuit.V(1, 'Vdd', circuit.gnd, 5@u_V)

# Inputs
circuit.PulseVoltageSource('Vin1', 'input1', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=40@u_ns)
circuit.PulseVoltageSource('Vin2', 'input2', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=40@u_ns)

# Define NMOS transistors (parallel connection)
circuit.MOSFET('M1', 'output', 'input1', circuit.gnd, circuit.gnd, model='NMOS')  # NMOS1
circuit.MOSFET('M2', 'output', 'input2', circuit.gnd, circuit.gnd, model='NMOS')  # NMOS2

# Define PMOS transistors (series connection)
circuit.MOSFET('M3', 'output', 'input1', 'Vdd', 'Vdd', model='PMOS')  # PMOS1
circuit.MOSFET('M4', 'output', 'input2', 'Vdd', 'Vdd', model='PMOS')  # PMOS2

# Define MOSFET models
circuit.model('NMOS', 'nmos', kp=120e-6, vto=1, lambda_=0.02, w=10e-6, l=1e-6)
circuit.model('PMOS', 'pmos', kp=60e-6, vto=-1, lambda_=0.02, w=20e-6, l=1e-6)

# Simulation settings: Transient analysis
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=10@u_ns, end_time=100@u_ns)

# Plot output
plt.figure()
plt.plot(analysis.time, analysis['output'], label='Vout (NOR Gate Output)')
plt.plot(analysis.time, analysis['input1'], label='Vin1')
plt.plot(analysis.time, analysis['input2'], label='Vin2')
plt.title('Transient Analysis of CMOS NOR Gate')
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')
plt.legend()
plt.grid()
plt.show()
