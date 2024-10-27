from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

# Create the VCO circuit
circuit = Circuit('Voltage Controlled Oscillator')

# Define power supply with ramp-up
circuit.PulseVoltageSource('dd', 'vdd', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,  # Using 3.3V for better stability
    delay_time=0@u_ns,
    rise_time=1@u_ns,
    fall_time=1@u_ns,
    pulse_width=2500@u_ns,
    period=2500@u_ns
)

# Add supply resistor and decoupling capacitor
circuit.R('Rvdd', 'vdd', 'vdd_internal', 1@u_Ω)
circuit.C('Cvdd', 'vdd_internal', circuit.gnd, 1@u_pF)

# Control voltage source (sweep from 0V to 3.3V)
circuit.PulseVoltageSource('ctrl', 'v_control', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,
    delay_time=5@u_ns,
    rise_time=500@u_ns,
    fall_time=500@u_ns,
    pulse_width=1000@u_ns,
    period=2000@u_ns
)

# Add control voltage protection and filtering
circuit.R('Rctrl', 'v_control', 'v_control_int', 100@u_Ω)
circuit.C('Cctrl', 'v_control_int', circuit.gnd, 0.1@u_pF)

# Current mirror bias circuit
circuit.MOSFET('M1', 'bias', 'bias', circuit.gnd, circuit.gnd, model='NMOS')
circuit.R('Rbias', 'vdd_internal', 'bias', 10@u_kΩ)
circuit.C('Cbias', 'bias', circuit.gnd, 0.1@u_pF)

# Voltage-controlled current source
circuit.MOSFET('M2', 'i_ctrl', 'v_control_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('M3', 'i_ctrl', 'bias', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('Ci_ctrl', 'i_ctrl', circuit.gnd, 0.1@u_pF)

# Ring oscillator stages with parasitic capacitance
for i in range(1, 4):
    prev_stage = f'stage{3 if i == 1 else i-1}'
    curr_stage = f'stage{i}'
    
    # PMOS
    circuit.MOSFET(f'Mp{i}', curr_stage, prev_stage, 'vdd_internal', 'vdd_internal', model='PMOS')
    # NMOS
    circuit.MOSFET(f'Mn{i}', curr_stage, prev_stage, 'i_ctrl', circuit.gnd, model='NMOS')
    # Load capacitance
    circuit.C(f'C{i}', curr_stage, circuit.gnd, 0.1@u_pF)
    # Weak pull-up for initialization
    circuit.R(f'Rpu{i}', curr_stage, 'vdd_internal', 1@u_MΩ)

# Output buffer
circuit.MOSFET('M10', 'vco_out', 'stage3', 'vdd_internal', 'vdd_internal', model='PMOS_BUF')
circuit.MOSFET('M11', 'vco_out', 'stage3', circuit.gnd, circuit.gnd, model='NMOS_BUF')
circuit.C('Cout', 'vco_out', circuit.gnd, 0.1@u_pF)

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
    w=4e-6,
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
    w=12e-6,
    l=0.35e-6
)

# Buffer transistors (larger size for driving output load)
circuit.model('NMOS_BUF', 'nmos',
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
    w=8e-6,
    l=0.35e-6
)

circuit.model('PMOS_BUF', 'pmos',
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
    w=24e-6,
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
    method='gear'
)

try:
    # Run transient analysis
    analysis = simulator.transient(
        step_time=0.1@u_ns,
        end_time=2000@u_ns,
        start_time=0@u_ns,
        max_time=0.2@u_ns,
        use_initial_condition=True
    )

    # Convert time and voltage data to numpy arrays
    time = np.array([float(t) for t in analysis.time])
    vctrl = np.array([float(v) for v in analysis['v_control']])
    vout = np.array([float(v) for v in analysis['vco_out']])

    # Create figure with multiple subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))

    # Plot control voltage
    ax1.plot(time, vctrl, label='Control Voltage', color='blue')
    ax1.grid(True)
    ax1.set_title('VCO Control Voltage')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Voltage (V)')
    ax1.legend()
    ax1.set_ylim(-0.5, 4)

    # Plot output waveform
    ax2.plot(time, vout, label='VCO Output', color='red')
    ax2.grid(True)
    ax2.set_title('VCO Output Waveform')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Voltage (V)')
    ax2.legend()
    ax2.set_ylim(-0.5, 4)

    # Calculate and plot instantaneous frequency
    def calculate_frequency(time, signal, window_size=100):
        frequencies = []
        times = []
        control_voltages = []
        
        for i in range(0, len(time)-window_size, window_size//2):
            window = signal[i:i+window_size]
            t_window = time[i:i+window_size]
            
            # Count zero crossings
            crossings = np.where(np.diff(window > np.mean(window)))[0]
            if len(crossings) >= 2:
                period = 2 * np.mean(np.diff(t_window[crossings]))
                freq = 1.0 / period if period > 0 else 0
                frequencies.append(freq)
                times.append(np.mean(t_window))
                control_voltages.append(np.mean(vctrl[i:i+window_size]))
        
        return np.array(times), np.array(frequencies), np.array(control_voltages)

    # Calculate frequencies and plot
    t_freq, freqs, v_ctrl = calculate_frequency(time, vout)
    
    if len(t_freq) > 0:
        # Plot frequency vs control voltage
        ax3.plot(v_ctrl, freqs/1e6, 'o-', label='Tuning Characteristic', color='green')
        ax3.grid(True)
        ax3.set_title('VCO Tuning Characteristic')
        ax3.set_xlabel('Control Voltage (V)')
        ax3.set_ylabel('Frequency (MHz)')
        ax3.legend()

        # Print VCO characteristics
        if len(freqs) > 1:
            freq_range = np.ptp(freqs)
            voltage_range = np.ptp(v_ctrl)
            kvco = freq_range / voltage_range if voltage_range > 0 else 0
            print(f"VCO Characteristics:")
            print(f"Frequency Range: {np.min(freqs)/1e6:.2f} MHz to {np.max(freqs)/1e6:.2f} MHz")
            print(f"Average Kvco: {kvco/1e6:.2f} MHz/V")

    plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"Simulation failed: {str(e)}")
    print("Detailed error information:")
    import traceback
    traceback.print_exc()

print(circuit)