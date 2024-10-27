from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
from PySpice.Probe.Plot import plot

# Create the circuit
circuit = Circuit('CMOS Voltage-Controlled Oscillator (VCO)')

# Supply voltage (Vdd)
circuit.V(1, 'Vdd', circuit.gnd, 5@u_V)

# Control Voltage (Vcontrol)
circuit.PulseVoltageSource(2, 'Vcontrol', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, 
                           rise_time=10@u_ns, fall_time=10@u_ns, pulse_width=50@u_ns, period=100@u_ns)

# MOSFET acting as a variable resistor (controlled by Vcontrol)
circuit.MOSFET('M1', 'drain', 'node1', 'Vcontrol', 'Vcontrol', model='NMOS')  # NMOS controlled by Vcontrol

# Capacitor (part of the timing network)
circuit.C(1, 'node1', circuit.gnd, 1@u_nF)

# Inverter (to form the oscillator)
circuit.MOSFET('PM1', 'output', 'node1', 'Vdd', 'Vdd', model='PMOS')  # PMOS transistor
circuit.MOSFET('NM2', 'output', 'node1', circuit.gnd, circuit.gnd, model='NMOS')  # NMOS transistor

# Resistor in the feedback loop
circuit.R(1, 'output', 'node1', 10@u_kΩ)

# Define MOSFET models for NMOS and PMOS transistors
circuit.model('NMOS', 'nmos', kp=120e-6, vto=1, lambda_=0.02, w=10e-6, l=1e-6)
circuit.model('PMOS', 'pmos', kp=60e-6, vto=-1, lambda_=0.02, w=20e-6, l=1e-6)

# Simulation settings: Transient analysis to observe oscillations
simulator = circuit.simulator(temperature=25, nominal_temperature=25)

# Perform transient analysis to simulate VCO behavior
analysis = simulator.transient(step_time=1@u_ns, end_time=200@u_ns)  # Increased time to allow oscillation to settle
print(circuit)
# The connections and other aspects are good but the plotting is failed
# Plot the output signal (oscillating signal) and control voltage
plt.figure()
plot(analysis['output'], label='Oscillating Output (VCO)')
plot(analysis['Vcontrol'], label='Control Voltage (Vcontrol)')
plt.title('Transient Analysis of CMOS Voltage-Controlled Oscillator')
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')
plt.legend()
plt.grid()
plt.show()
