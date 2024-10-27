from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
from PySpice.Probe.Plot import plot

# Create the circuit
circuit = Circuit('CMOS SR Latch using NAND Gates')

# Supply voltage (Vdd)
circuit.V(1, 'Vdd', circuit.gnd, 5@u_V)

# Inputs: Set (S) and Reset (R)
circuit.PulseVoltageSource('Set', 'input_S', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=40@u_ns)
circuit.PulseVoltageSource('Reset', 'input_R', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=40@u_ns)

# Define the first NAND gate (Q output)
# PMOS transistors (parallel connection for NAND)
circuit.MOSFET('PM1', 'Q', 'input_R', 'Vdd', 'Vdd', model='PMOS')  # PMOS in parallel
circuit.MOSFET('PM2', 'Q', 'Q_bar', 'Vdd', 'Vdd', model='PMOS')

# NMOS transistors (series connection for NAND)
circuit.MOSFET('NM1', 'Q', 'input_R', circuit.gnd, circuit.gnd, model='NMOS')  # NMOS in series
circuit.MOSFET('NM2', 'Q', 'Q_bar', circuit.gnd, circuit.gnd, model='NMOS')

# Define the second NAND gate (Q_bar output)
# PMOS transistors (parallel connection for NAND)
circuit.MOSFET('PM3', 'Q_bar', 'input_S', 'Vdd', 'Vdd', model='PMOS')  # PMOS in parallel
circuit.MOSFET('PM4', 'Q_bar', 'Q', 'Vdd', 'Vdd', model='PMOS')

# NMOS transistors (series connection for NAND)
circuit.MOSFET('NM3', 'Q_bar', 'input_S', circuit.gnd, circuit.gnd, model='NMOS')  # NMOS in series
circuit.MOSFET('NM4', 'Q_bar', 'Q', circuit.gnd, circuit.gnd, model='NMOS')

# Define NMOS and PMOS models for the CMOS transistors
circuit.model('NMOS', 'nmos', kp=120e-6, vto=1, lambda_=0.02, w=10e-6, l=1e-6)
circuit.model('PMOS', 'pmos', kp=60e-6, vto=-1, lambda_=0.02, w=20e-6, l=1e-6)

# Simulation settings: Transient analysis
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=1@u_ns, end_time=100@u_ns)

# Plot output signals (Q and Q_bar)
plt.figure()
plt.plot(analysis.time, analysis['Q'], label='Q Output')
plt.plot(analysis.time, analysis['Q_bar'], label="Q' Output")
plt.plot(analysis.time, analysis['input_S'], label="Set (S)")
plt.plot(analysis.time, analysis['input_R'], label="Reset (R)")
plt.title('Transient Analysis of CMOS SR Latch using NAND Gates')
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')
plt.legend()
plt.grid()
plt.show()
