from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
from PySpice.Spice.Library import SpiceLibrary
import matplotlib.pyplot as plt
import numpy as np

# Create the CMOS Inverter circuit
circuit = Circuit('CMOS Inverter')

# Define the power supply and input voltage source
# VDD connected between vdd and ground
circuit.V('dd', 'vdd', circuit.gnd, 5@u_V)

# Input pulse for switching behavior
# Pulse parameters: initial value, pulsed value, delay, rise time, fall time, pulse width, period
circuit.PulseVoltageSource('in', 'input', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=5@u_V,
    delay_time=0@u_ns,
    rise_time=1@u_ns,
    fall_time=1@u_ns,
    pulse_width=20@u_ns,
    period=40@u_ns
)

# Define NMOS and PMOS transistors
# PMOS: drain, gate, source, bulk
circuit.MOSFET('M1', 'output', 'input', 'vdd', 'vdd', model='PMOS')

# NMOS: drain, gate, source, bulk
circuit.MOSFET('M2', 'output', 'input', circuit.gnd, circuit.gnd, model='NMOS')

# Define MOSFET models with appropriate parameters
circuit.model('NMOS', 'nmos',
    level=1,
    kp=120e-6,    # Transconductance parameter
    vto=0.7,      # Threshold voltage
    lambda_=0.02, # Channel length modulation
    gamma=0.37,   # Body effect parameter
    phi=0.65,     # Surface potential
    w=10e-6,      # Channel width
    l=1e-6        # Channel length
)

circuit.model('PMOS', 'pmos',
    level=1,
    kp=60e-6,     # Transconductance parameter (half of NMOS due to mobility)
    vto=-0.7,     # Threshold voltage (negative for PMOS)
    lambda_=0.02, # Channel length modulation
    gamma=0.37,   # Body effect parameter
    phi=0.65,     # Surface potential
    w=20e-6,      # Channel width (2x NMOS to compensate for mobility)
    l=1e-6        # Channel length
)

print(circuit)
# Create simulator
simulator = circuit.simulator(temperature=25, nominal_temperature=25)

# Add simulation options for convergence
simulator.options(reltol=1e-4, abstol=1e-9, vntol=1e-6)

try:
    # Run transient analysis
    analysis = simulator.transient(step_time=0.1@u_ns, end_time=100@u_ns)

    # Create plot
    plt.figure(figsize=(10, 6))
    
    # Plot input voltage
    plt.plot(analysis.time, analysis['input'], 
             label='Input', linestyle='--', color='blue')
    
    # Plot output voltage
    plt.plot(analysis.time, analysis['output'], 
             label='Output', color='red')
    
    # Customize plot
    plt.grid(True)
    plt.title('CMOS Inverter Transient Analysis')
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (V)')
    plt.legend()

    plt.ylim(-0.5, 5.5)
    
    # Show plot
    plt.show()

except Exception as e:
    print(f"Simulation failed: {str(e)}")
    print("Try adjusting simulation parameters or check circuit connections.")