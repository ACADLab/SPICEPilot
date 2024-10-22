from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

# Initialize the circuit
circuit = Circuit('Common-Drain Amplifier (Source Follower)')

# Define the supply voltage Vdd = 5V
circuit.V(1, 'Vdd', circuit.gnd, 5@u_V)

# Define the input voltage signal (DC = 0V, AC = 1V, Sinusoidal at 1kHz)
circuit.SinusoidalVoltageSource('Vin', 'input', circuit.gnd, 
                                amplitude=1@u_V, frequency=1@u_kHz)

# Input coupling capacitor (C1) from input to gate
circuit.C(1, 'input', 'gate', 1@u_uF)

# Bias resistors
circuit.R(2, 'Vdd', 'gate', 100@u_kΩ)  # Resistor R2
circuit.R(3, 'gate', circuit.gnd, 100@u_kΩ)  # Resistor R3

# NMOS transistor definition
circuit.MOSFET('M1', 'Vdd', 'gate', 'output', circuit.gnd, model='NMOS')

# Load resistor at the source (R1)
circuit.R(1, 'output', circuit.gnd, 1@u_kΩ)

# Output coupling capacitor (C2)
circuit.C(2, 'output', circuit.gnd, 1@u_uF)

# NMOS transistor model
circuit.model('NMOS', 'nmos', kp=0.00012, l=1e-6, lambda_=0.02, vto=1, w=1e-5)

# Set up the AC and transient simulation
simulator = circuit.simulator(temperature=25, nominal_temperature=25)

# Run transient analysis (step time = 1 µs, end time = 5 ms)
analysis_transient = simulator.transient(step_time=1@u_us, end_time=5@u_ms)

# Run AC analysis (from 1 Hz to 1 MHz)
analysis_ac = simulator.ac(start_frequency=1@u_Hz, stop_frequency=1@u_MHz, number_of_points=1000,variation='dec')

# Plot the transient response
plt.figure()
plt.plot(analysis_transient.time, analysis_transient['input'], label='Input (Vin)')
plt.plot(analysis_transient.time, analysis_transient['output'], label='Output (Vout)')
plt.title('Transient Analysis of Common-Drain Amplifier (Source Follower)')
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')
plt.legend()
plt.grid()
plt.show()

# Plot the AC response (magnitude in dB)
plt.figure()
plt.plot(analysis_ac.frequency, 20*np.log10(np.absolute(analysis_ac['output'])))
plt.title('AC Analysis of Common-Drain Amplifier (Source Follower)')
plt.xlabel('Frequency [Hz]')
plt.ylabel('Gain [dB]')
plt.grid()
plt.show()
