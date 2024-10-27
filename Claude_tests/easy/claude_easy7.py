from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

# Create the Ring Oscillator circuit
circuit = Circuit('3-Stage Ring Oscillator')

# Define power supply with ramp-up to improve convergence
circuit.PulseVoltageSource('dd', 'vdd', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,  # Using 3.3V for better stability
    delay_time=0@u_ns,
    rise_time=0.1@u_ns,
    fall_time=0.1@u_ns,
    pulse_width=100@u_ns,
    period=100@u_ns
)

# Add small resistor in series with Vdd for better convergence
circuit.R('Rvdd', 'vdd', 'vdd_internal', 1@u_Ω)

# First Inverter Stage
circuit.MOSFET('M1', 'node1', 'node3', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M2', 'node1', 'node3', circuit.gnd, circuit.gnd, model='NMOS')
circuit.R('R1', 'node1', 'vdd_internal', 100@u_kΩ)  # Pull-up to help start oscillation

# Second Inverter Stage
circuit.MOSFET('M3', 'node2', 'node1', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M4', 'node2', 'node1', circuit.gnd, circuit.gnd, model='NMOS')

# Third Inverter Stage
circuit.MOSFET('M5', 'node3', 'node2', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M6', 'node3', 'node2', circuit.gnd, circuit.gnd, model='NMOS')

# Add parasitic capacitance
circuit.C('C1', 'node1', circuit.gnd, 0.5@u_pF)
circuit.C('C2', 'node2', circuit.gnd, 0.5@u_pF)
circuit.C('C3', 'node3', circuit.gnd, 0.5@u_pF)

# Define MOSFET models with more realistic parameters
circuit.model('NMOS', 'nmos',
    level=1,
    kp=120e-6,
    vto=0.7,
    lambda_=0.01,
    gamma=0.4,
    phi=0.65,
    cgso=0.6e-9,
    cgdo=0.6e-9,
    cbd=0.1e-12,
    cbs=0.1e-12,
    w=2e-6,
    l=0.35e-6
)

circuit.model('PMOS', 'pmos',
    level=1,
    kp=40e-6,
    vto=-0.7,
    lambda_=0.01,
    gamma=0.4,
    phi=0.65,
    cgso=0.6e-9,
    cgdo=0.6e-9,
    cbd=0.1e-12,
    cbs=0.1e-12,
    w=6e-6,
    l=0.35e-6
)

# Create simulator with modified parameters
simulator = circuit.simulator(temperature=27, nominal_temperature=27)

# Add simulation options for better convergence
simulator.options(
    reltol=1e-3,
    abstol=1e-6,
    vntol=1e-4,
    chgtol=1e-14,
    trtol=7,
    itl1=100,
    itl2=50,
    itl4=50,
    method='gear'  # Use Gear integration method for better stability
)

try:
    # Run transient analysis with modified parameters
    analysis = simulator.transient(
        step_time=0.1@u_ns,
        end_time=50@u_ns,
        start_time=0@u_ns,
        max_time=0.2@u_ns,
        use_initial_condition=True
    )

    # Convert time and voltage data to numpy arrays
    time = np.array([float(t) for t in analysis.time])
    v1 = np.array([float(v) for v in analysis['node1']])
    v2 = np.array([float(v) for v in analysis['node2']])
    v3 = np.array([float(v) for v in analysis['node3']])

    # Create plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot node voltages
    ax1.plot(time, v1, label='Node 1', color='blue')
    ax1.plot(time, v2, label='Node 2', color='red')
    ax1.plot(time, v3, label='Node 3', color='green')
    ax1.grid(True)
    ax1.set_title('Ring Oscillator - Node Voltages')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Voltage (V)')
    ax1.legend()
    ax1.set_ylim(-0.5, 4)

    # Calculate and plot oscillation frequency
    def calculate_frequency(time, voltage, threshold=1.65):
        crossings = np.where(np.diff(voltage > threshold))[0]
        if len(crossings) >= 2:
            periods = np.diff(time[crossings])
            freq = 1.0 / np.mean(periods)
            return freq
        return None

    # Plot FFT of node3 (output)
    if len(time) > 1:
        sampling_rate = 1.0 / (time[1] - time[0])
        n = len(v3)
        freqs = np.fft.fftfreq(n, 1/sampling_rate)
        fft_v3 = np.abs(np.fft.fft(v3))
        
        # Plot only positive frequencies
        mask = freqs > 0
        ax2.plot(freqs[mask], fft_v3[mask])
        ax2.grid(True)
        ax2.set_title('Frequency Spectrum')
        ax2.set_xlabel('Frequency (Hz)')
        ax2.set_ylabel('Magnitude')
        ax2.set_xscale('log')

    plt.tight_layout()
    plt.show()

    # Calculate and display oscillation characteristics
    freq = calculate_frequency(time, v3)
    if freq is not None:
        print(f"Oscillation Frequency: {freq/1e6:.2f} MHz")
        print(f"Period: {1000/freq:.2f} ns")

except Exception as e:
    print(f"Simulation failed: {str(e)}")
    print("Detailed error information:")
    import traceback
    traceback.print_exc()

print(circuit)