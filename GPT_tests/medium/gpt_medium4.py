from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
from PySpice.Probe.Plot import plot

# Create the circuit
circuit = Circuit('CMOS D Flip-Flop')

# Supply voltage (Vdd)
circuit.V(1, 'Vdd', circuit.gnd, 5@u_V)

# Input signals: D and Clock
circuit.PulseVoltageSource('D', 'input_D', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=40@u_ns)
circuit.PulseVoltageSource('Clock', 'clk', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=40@u_ns)

# Transmission Gate 1 (controlled by Clock and Clock-bar) for capturing the input D when Clock is high
# PMOS for Clock-bar (inverted clock)
circuit.MOSFET('PM1', 'mid1', 'input_D', 'Vdd', 'clk_bar', model='PMOS')
# NMOS for Clock
circuit.MOSFET('NM1', 'mid1', 'input_D', circuit.gnd, 'clk', model='NMOS')

# Inverter for Clock-bar
circuit.MOSFET('PM5', 'clk_bar', 'clk', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM5', 'clk_bar', 'clk', circuit.gnd, circuit.gnd, model='NMOS')

# First Inverter after Transmission Gate 1
circuit.MOSFET('PM2', 'mid2', 'mid1', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM2', 'mid2', 'mid1', circuit.gnd, circuit.gnd, model='NMOS')

# Transmission Gate 2 (for output latch, controlled by Clock)
# PMOS for Clock
circuit.MOSFET('PM3', 'Q', 'mid2', 'Vdd', 'clk_bar', model='PMOS')
# NMOS for Clock-bar
circuit.MOSFET('NM3', 'Q', 'mid2', circuit.gnd, 'clk', model='NMOS')

# Output Inverter for stability (optional, typically used for stronger output drive)
circuit.MOSFET('PM4', 'output', 'Q', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM4', 'output', 'Q', circuit.gnd, circuit.gnd, model='NMOS')

# Define MOSFET models for NMOS and PMOS transistors
circuit.model('NMOS', 'nmos', kp=120e-6, vto=1, lambda_=0.02, w=10e-6, l=1e-6)
circuit.model('PMOS', 'pmos', kp=60e-6, vto=-1, lambda_=0.02, w=20e-6, l=1e-6)

# Simulation settings: Transient analysis
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=1@u_ns, end_time=100@u_ns)

# Plot the output signals
plt.figure()
plt.plot(analysis.time, analysis['input_D'], label='D Input')
plt.plot(analysis.time, analysis['clk'], label='Clock')
plt.plot(analysis.time, analysis['output'], label='Q Output')
plt.title('Transient Analysis of CMOS D Flip-Flop')
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')
plt.legend()
plt.grid()
plt.show()
