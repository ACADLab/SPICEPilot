from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
from PySpice.Spice.Library import SpiceLibrary
import matplotlib.pyplot as plt
import numpy as np

# Create the CMOS NAND Gate circuit
circuit = Circuit('CMOS NAND Gate')

# Define power supply
circuit.V('dd', 'vdd', circuit.gnd, 5@u_V)

# Define input voltage sources
# Input A: Full period pulse
circuit.PulseVoltageSource('inA', 'inputA', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=5@u_V,
    delay_time=0@u_ns,
    rise_time=1@u_ns,
    fall_time=1@u_ns,
    pulse_width=40@u_ns,
    period=80@u_ns
)

# Input B: Half period pulse
circuit.PulseVoltageSource('inB', 'inputB', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=5@u_V,
    delay_time=0@u_ns,
    rise_time=1@u_ns,
    fall_time=1@u_ns,
    pulse_width=20@u_ns,
    period=40@u_ns
)

# Define PMOS transistors in parallel
# PMOS1: Connected to inputA
circuit.MOSFET('M1', 'output', 'inputA', 'vdd', 'vdd', model='PMOS')

# PMOS2: Connected to inputB
circuit.MOSFET('M2', 'output', 'inputB', 'vdd', 'vdd', model='PMOS')

# Define NMOS transistors in series
# NMOS1: Connected to inputA and intermediate node
circuit.MOSFET('M3', 'output', 'inputA', 'intermediate', circuit.gnd, model='NMOS')

# NMOS2: Connected to inputB and ground
circuit.MOSFET('M4', 'intermediate', 'inputB', circuit.gnd, circuit.gnd, model='NMOS')

# Define MOSFET models
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
    kp=60e-6,     # Transconductance parameter
    vto=-0.7,     # Threshold voltage
    lambda_=0.02, # Channel length modulation
    gamma=0.37,   # Body effect parameter
    phi=0.65,     # Surface potential
    w=20e-6,      # Channel width (2x NMOS width)
    l=1e-6        # Channel length
)

# Create simulator
simulator = circuit.simulator(temperature=25, nominal_temperature=25)

# Add simulation options for better convergence
simulator.options(reltol=1e-4, abstol=1e-9, vntol=1e-6)

try:
    # Run transient analysis
    analysis = simulator.transient(step_time=0.1@u_ns, end_time=160@u_ns)

    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot inputs on first subplot
    ax1.plot(analysis.time, analysis['inputA'], 
             label='Input A', linestyle='--', color='blue')
    ax1.plot(analysis.time, analysis['inputB'], 
             label='Input B', linestyle='--', color='green')
    ax1.grid(True)
    ax1.set_title('CMOS NAND Gate - Inputs')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Voltage (V)')
    ax1.legend()
    ax1.set_ylim(-0.5, 5.5)
    
    # Plot output on second subplot
    ax2.plot(analysis.time, analysis['output'], 
             label='Output', color='red')
    ax2.grid(True)
    ax2.set_title('CMOS NAND Gate - Output')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Voltage (V)')
    ax2.legend()
    ax2.set_ylim(-0.5, 5.5)
    
    # Adjust layout and display
    plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"Simulation failed: {str(e)}")
    print("Try adjusting simulation parameters or check circuit connections.")

# Optional: Add timing analysis
def analyze_timing(analysis):
    """Calculate propagation delays and transition times"""
    vdd = 5.0
    v_th = vdd / 2  # Threshold voltage for timing measurements
    
    # Find rising and falling edges
    edges = {
        'input_a': np.where(np.diff(analysis['inputA'] > v_th))[0],
        'input_b': np.where(np.diff(analysis['inputB'] > v_th))[0],
        'output': np.where(np.diff(analysis['output'] > v_th))[0]
    }
    
    # Calculate propagation delays
    prop_delays = []
    for i in range(min(len(edges['input_a']), len(edges['output']))):
        delay = abs(analysis.time[edges['output'][i]] - 
                   analysis.time[edges['input_a'][i]])
        prop_delays.append(float(delay))
    
    print(f"Average propagation delay: {np.mean(prop_delays):.2e} seconds")