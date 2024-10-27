from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
from PySpice.Probe.Plot import plot

# Create the circuit
circuit = Circuit('CMOS 2-to-4 Decoder')

# Supply voltage (Vdd)
circuit.V(1, 'Vdd', circuit.gnd, 5@u_V)

# Input signals: A1, A0
circuit.PulseVoltageSource('A1', 'input_A1', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=40@u_ns)
circuit.PulseVoltageSource('A0', 'input_A0', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=40@u_ns)

# Inverters (NOT gates) to generate A1' and A0'
# Inverter for A1'
circuit.MOSFET('PM1', 'A1_not', 'input_A1', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM1', 'A1_not', 'input_A1', circuit.gnd, circuit.gnd, model='NMOS')

# Inverter for A0'
circuit.MOSFET('PM2', 'A0_not', 'input_A0', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM2', 'A0_not', 'input_A0', circuit.gnd, circuit.gnd, model='NMOS')

# AND gates to generate Y0, Y1, Y2, Y3
# Y0 = A1' AND A0'
circuit.MOSFET('PM3', 'Y0', 'A1_not', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('PM4', 'Y0', 'A0_not', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM3', 'Y0', 'A1_not', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('NM4', 'Y0', 'A0_not', circuit.gnd, circuit.gnd, model='NMOS')

# Y1 = A1' AND A0
circuit.MOSFET('PM5', 'Y1', 'A1_not', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('PM6', 'Y1', 'input_A0', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM5', 'Y1', 'A1_not', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('NM6', 'Y1', 'input_A0', circuit.gnd, circuit.gnd, model='NMOS')

# Y2 = A1 AND A0'
circuit.MOSFET('PM7', 'Y2', 'input_A1', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('PM8', 'Y2', 'A0_not', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM7', 'Y2', 'input_A1', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('NM8', 'Y2', 'A0_not', circuit.gnd, circuit.gnd, model='NMOS')

# Y3 = A1 AND A0
circuit.MOSFET('PM9', 'Y3', 'input_A1', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('PM10', 'Y3', 'input_A0', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM9', 'Y3', 'input_A1', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('NM10', 'Y3', 'input_A0', circuit.gnd, circuit.gnd, model='NMOS')

# Define NMOS and PMOS models for the CMOS transistors
circuit.model('NMOS', 'nmos', kp=120e-6, vto=1, lambda_=0.02, w=10e-6, l=1e-6)
circuit.model('PMOS', 'pmos', kp=60e-6, vto=-1, lambda_=0.02, w=20e-6, l=1e-6)

# Simulation settings: Transient analysis
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=1@u_ns, end_time=100@u_ns)
print(circuit)
# Plot the outputs Y0, Y1, Y2, Y3
plt.figure()
plt.plot(analysis.time, analysis['Y0'], label='Y0 Output')
plt.plot(analysis.time, analysis['Y1'], label='Y1 Output')
plt.plot(analysis.time, analysis['Y2'], label='Y2 Output')
plt.plot(analysis.time, analysis['Y3'], label='Y3 Output')
plt.plot(analysis.time, analysis['input_A1'], label='A1 Input')
plt.plot(analysis.time, analysis['input_A0'], label='A0 Input')
plt.title('Transient Analysis of CMOS 2-to-4 Decoder')
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')
plt.legend()
plt.grid()
plt.show()
