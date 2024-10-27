from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
from PySpice.Spice.Library import SpiceLibrary
import matplotlib.pyplot as plt
import numpy as np

# Create the CMOS NOR Gate circuit
circuit = Circuit('CMOS NOR Gate')

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

# Define PMOS transistors in series
# PMOS1: Connected to inputA and VDD
circuit.MOSFET('M1', 'intermediate', 'inputA', 'vdd', 'vdd', model='PMOS')

# PMOS2: Connected to inputB and intermediate node
circuit.MOSFET('M2', 'output', 'inputB', 'intermediate', 'vdd', model='PMOS')

# Define NMOS transistors in parallel
# NMOS1: Connected to inputA
circuit.MOSFET('M3', 'output', 'inputA', circuit.gnd, circuit.gnd, model='NMOS')

# NMOS2: Connected to inputB
circuit.MOSFET('M4', 'output', 'inputB', circuit.gnd, circuit.gnd, model='NMOS')

# Define MOSFET models
# PMOS width is increased to 40µm (4x NMOS) because they're in series
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
    w=40e-6,      # Channel width (4x NMOS width due to series connection)
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
    ax1.set_title('CMOS NOR Gate - Inputs')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Voltage (V)')
    ax1.legend()
    ax1.set_ylim(-0.5, 5.5)
    
    # Plot output on second subplot
    ax2.plot(analysis.time, analysis['output'], 
             label='Output', color='red')
    ax2.grid(True)
    ax2.set_title('CMOS NOR Gate - Output')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Voltage (V)')
    ax2.legend()
    ax2.set_ylim(-0.5, 5.5)
    
    # Add truth table annotation
    truth_table = """
    NOR Truth Table
    A B | Out
    0 0 | 1
    0 1 | 0
    1 0 | 0
    1 1 | 0
    """
    plt.figtext(1.02, 0.5, truth_table, fontfamily='monospace')
    
    # Adjust layout and display
    plt.tight_layout()
    plt.show()

    # Calculate and display timing characteristics
    def analyze_timing(analysis):
        """Calculate rise time, fall time, and propagation delay"""
        vdd = 5.0
        v_low = 0.1 * vdd
        v_high = 0.9 * vdd
        
        # Find transitions
        output = analysis['output']
        time = analysis.time
        
        # Find rising and falling edges
        rising_edges = []
        falling_edges = []
        
        for i in range(1, len(output)):
            if output[i-1] < v_low and output[i] > v_high:
                rising_edges.append(i)
            elif output[i-1] > v_high and output[i] < v_low:
                falling_edges.append(i)
        
        # Calculate average rise and fall times
        rise_times = []
        fall_times = []
        
        for edge in rising_edges:
            rise_time = float(time[edge] - time[edge-1])
            rise_times.append(rise_time)
            
        for edge in falling_edges:
            fall_time = float(time[edge] - time[edge-1])
            fall_times.append(fall_time)
            
        if rise_times:
            print(f"Average rise time: {np.mean(rise_times):.2e} seconds")
        if fall_times:
            print(f"Average fall time: {np.mean(fall_times):.2e} seconds")
    
    analyze_timing(analysis)

except Exception as e:
    print(f"Simulation failed: {str(e)}")
    print("Try adjusting simulation parameters or check circuit connections.")