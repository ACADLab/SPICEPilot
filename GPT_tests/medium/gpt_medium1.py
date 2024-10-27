from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
from PySpice.Probe.Plot import plot

# Create the circuit
circuit = Circuit('CMOS Full Adder')

# Supply voltage (Vdd)
circuit.V(1, 'Vdd', circuit.gnd, 5@u_V)

# Input signals: A, B, Cin
circuit.PulseVoltageSource('A', 'input_A', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=40@u_ns)
circuit.PulseVoltageSource('B', 'input_B', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=40@u_ns)
circuit.PulseVoltageSource('Cin', 'input_Cin', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=40@u_ns)

# XOR gate for A ⊕ B
# First XOR gate: A ⊕ B
circuit.MOSFET('PM1', 'xor_ab', 'input_A', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('PM2', 'xor_ab', 'input_B', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM1', 'xor_ab', 'input_A', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('NM2', 'xor_ab', 'input_B', circuit.gnd, circuit.gnd, model='NMOS')

# Second XOR gate: (A ⊕ B) ⊕ Cin for Sum
circuit.MOSFET('PM3', 'Sum', 'xor_ab', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('PM4', 'Sum', 'input_Cin', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM3', 'Sum', 'xor_ab', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('NM4', 'Sum', 'input_Cin', circuit.gnd, circuit.gnd, model='NMOS')

# AND gate: A AND B
circuit.MOSFET('PM5', 'and_ab', 'input_A', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('PM6', 'and_ab', 'input_B', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM5', 'and_ab', 'input_A', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('NM6', 'and_ab', 'input_B', circuit.gnd, circuit.gnd, model='NMOS')

# AND gate: Cin AND (A ⊕ B)
circuit.MOSFET('PM7', 'and_cin_xor_ab', 'input_Cin', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('PM8', 'and_cin_xor_ab', 'xor_ab', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM7', 'and_cin_xor_ab', 'input_Cin', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('NM8', 'and_cin_xor_ab', 'xor_ab', circuit.gnd, circuit.gnd, model='NMOS')

# OR gate for Cout: (A AND B) OR (Cin AND (A ⊕ B))
circuit.MOSFET('PM9', 'Cout', 'and_ab', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('PM10', 'Cout', 'and_cin_xor_ab', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM9', 'Cout', 'and_ab', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('NM10', 'Cout', 'and_cin_xor_ab', circuit.gnd, circuit.gnd, model='NMOS')

# Define MOSFET models (NMOS and PMOS)
circuit.model('NMOS', 'nmos', kp=120e-6, vto=1, lambda_=0.02, w=10e-6, l=1e-6)
circuit.model('PMOS', 'pmos', kp=60e-6, vto=-1, lambda_=0.02, w=20e-6, l=1e-6)

# Simulation settings: Transient analysis
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=1@u_ns, end_time=100@u_ns)

# Plot the outputs Sum and Cout
plt.figure()
plt.plot(analysis.time, analysis['Sum'], label='Sum Output')
plt.plot(analysis.time, analysis['Cout'], label='Cout (Carry) Output')
plt.plot(analysis.time, analysis['input_A'], label='A Input')
plt.plot(analysis.time, analysis['input_B'], label='B Input')
plt.plot(analysis.time, analysis['input_Cin'], label='Cin Input')
plt.title('Transient Analysis of CMOS Full Adder')
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')
plt.legend()
plt.grid()
plt.show()
