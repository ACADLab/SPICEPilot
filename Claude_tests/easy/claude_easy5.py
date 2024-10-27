from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

# Create the CMOS Buffer circuit
circuit = Circuit('CMOS Buffer')

# Define power supply
Vdd = 5
circuit.V('dd', 'vdd', circuit.gnd, Vdd@u_V)

# Define input voltage source
circuit.PulseVoltageSource('in', 'input', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=Vdd@u_V,
    delay_time=0@u_ns,
    rise_time=5@u_ns,
    fall_time=5@u_ns,
    pulse_width=40@u_ns,
    period=80@u_ns
)

# Add noise to the input
circuit.SinusoidalVoltageSource('noise', 'input_noisy', 'input',
    amplitude=0.5@u_V,
    frequency=50@u_MHz
)

# First Inverter Stage
circuit.MOSFET('M1', 'intermediate', 'input_noisy', 'vdd', 'vdd', model='PMOS1')
circuit.MOSFET('M2', 'intermediate', 'input_noisy', circuit.gnd, circuit.gnd, model='NMOS1')

# Second Inverter Stage
circuit.MOSFET('M3', 'output', 'intermediate', 'vdd', 'vdd', model='PMOS2')
circuit.MOSFET('M4', 'output', 'intermediate', circuit.gnd, circuit.gnd, model='NMOS2')

# Define MOSFET models - first stage
circuit.model('NMOS1', 'nmos',
    level=1,
    kp=120e-6,
    vto=0.7,
    lambda_=0.02,
    gamma=0.37,
    phi=0.65,
    w=10e-6,
    l=1e-6
)

circuit.model('PMOS1', 'pmos',
    level=1,
    kp=60e-6,
    vto=-0.7,
    lambda_=0.02,
    gamma=0.37,
    phi=0.65,
    w=20e-6,
    l=1e-6
)

# Define MOSFET models - second stage
circuit.model('NMOS2', 'nmos',
    level=1,
    kp=120e-6,
    vto=0.7,
    lambda_=0.02,
    gamma=0.37,
    phi=0.65,
    w=20e-6,
    l=1e-6
)

circuit.model('PMOS2', 'pmos',
    level=1,
    kp=60e-6,
    vto=-0.7,
    lambda_=0.02,
    gamma=0.37,
    phi=0.65,
    w=40e-6,
    l=1e-6
)

# Create simulator
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
simulator.options(reltol=1e-4, abstol=1e-9, vntol=1e-6)

try:
    # Run transient analysis
    analysis = simulator.transient(step_time=0.1@u_ns, end_time=160@u_ns)
    
    # Convert analysis results to numpy arrays for easier processing
    time = np.array([float(t) for t in analysis.time])
    input_signal = np.array([float(v) for v in analysis['input']])
    input_noisy = np.array([float(v) for v in analysis['input_noisy']])
    intermediate = np.array([float(v) for v in analysis['intermediate']])
    output = np.array([float(v) for v in analysis['output']])
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot input signals
    ax1.plot(time, input_signal, label='Clean Input', linestyle='--', color='blue')
    ax1.plot(time, input_noisy, label='Noisy Input', color='red', alpha=0.7)
    ax1.grid(True)
    ax1.set_title('CMOS Buffer - Input Signals')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Voltage (V)')
    ax1.legend()
    ax1.set_ylim(-1, 6)
    
    # Plot intermediate and output signals
    ax2.plot(time, intermediate, label='Intermediate', linestyle='--', color='green')
    ax2.plot(time, output, label='Buffered Output', color='purple')
    ax2.grid(True)
    ax2.set_title('CMOS Buffer - Internal Node and Output')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Voltage (V)')
    ax2.legend()
    ax2.set_ylim(-1, 6)
    
    plt.tight_layout()
    plt.show()

    # Analyze buffer characteristics
    def analyze_buffer(time, input_signal, output, vdd=5.0):
        v_low = 0.1 * vdd
        v_high = 0.9 * vdd
        
        def find_crossings(signal, threshold, rising=True):
            crossings = []
            for i in range(1, len(signal)):
                if rising:
                    if signal[i-1] < threshold < signal[i]:
                        crossings.append(i)
                else:
                    if signal[i-1] > threshold > signal[i]:
                        crossings.append(i)
            return crossings
        
        # Find rising and falling transitions
        input_rise = find_crossings(input_signal, v_high, rising=True)
        input_fall = find_crossings(input_signal, v_low, rising=False)
        output_rise = find_crossings(output, v_high, rising=True)
        output_fall = find_crossings(output, v_low, rising=False)
        
        # Calculate delays
        rise_delays = []
        fall_delays = []
        
        for in_idx, out_idx in zip(input_rise, output_rise):
            delay = time[out_idx] - time[in_idx]
            rise_delays.append(delay)
            
        for in_idx, out_idx in zip(input_fall, output_fall):
            delay = time[out_idx] - time[in_idx]
            fall_delays.append(delay)
        
        # Print results
        if rise_delays:
            print(f"Average rise propagation delay: {np.mean(rise_delays):.2e} seconds")
        if fall_delays:
            print(f"Average fall propagation delay: {np.mean(fall_delays):.2e} seconds")
        
        # Calculate noise reduction
        input_noise = np.std(input_signal)
        output_noise = np.std(output)
        noise_reduction = (1 - output_noise/input_noise) * 100
        print(f"Noise reduction: {noise_reduction:.1f}%")
    
    analyze_buffer(time, input_noisy, output)

except Exception as e:
    print(f"Simulation failed: {str(e)}")
    print("Try adjusting simulation parameters or check circuit connections.")

print(circuit)