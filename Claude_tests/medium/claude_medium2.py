from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

# Create the 2-to-4 Decoder circuit
circuit = Circuit('2-to-4 Decoder')

# Define power supply with ramp-up
circuit.PulseVoltageSource('dd', 'vdd', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,  # Using 3.3V for better stability
    delay_time=0@u_ns,
    rise_time=0.5@u_ns,
    fall_time=0.5@u_ns,
    pulse_width=400@u_ns,
    period=400@u_ns
)

# Add supply resistor and decoupling capacitor
circuit.R('Rvdd', 'vdd', 'vdd_internal', 1@u_Ω)
circuit.C('Cvdd', 'vdd_internal', circuit.gnd, 1@u_pF)

# Define input voltage sources with delayed start
# Input A (LSB)
circuit.PulseVoltageSource('inA', 'A', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,
    delay_time=1@u_ns,
    rise_time=0.1@u_ns,
    fall_time=0.1@u_ns,
    pulse_width=40@u_ns,
    period=80@u_ns
)

# Input B (MSB)
circuit.PulseVoltageSource('inB', 'B', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,
    delay_time=1@u_ns,
    rise_time=0.1@u_ns,
    fall_time=0.1@u_ns,
    pulse_width=80@u_ns,
    period=160@u_ns
)

# Add input protection and parasitic capacitance
for node in ['A', 'B']:
    circuit.R(f'Rin_{node}', node, f'{node}_int', 100@u_Ω)
    circuit.C(f'Cin_{node}', f'{node}_int', circuit.gnd, 0.1@u_pF)

# Inverters for input signals
# Inverter for A
circuit.MOSFET('M1', 'A_inv', 'A_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M2', 'A_inv', 'A_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C1', 'A_inv', circuit.gnd, 0.1@u_pF)

# Inverter for B
circuit.MOSFET('M3', 'B_inv', 'B_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M4', 'B_inv', 'B_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C2', 'B_inv', circuit.gnd, 0.1@u_pF)

# Output 0 decoder (B'A')
circuit.MOSFET('M5', 'Y0_int', 'B_inv', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M6', 'Y0_int', 'A_inv', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M7', 'Y0_int', 'B_inv', 'Y0_n', circuit.gnd, model='NMOS')
circuit.MOSFET('M8', 'Y0_n', 'A_inv', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C3', 'Y0_int', circuit.gnd, 0.1@u_pF)

# Output buffer for Y0
circuit.MOSFET('M9', 'Y0', 'Y0_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M10', 'Y0', 'Y0_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C4', 'Y0', circuit.gnd, 0.1@u_pF)

# Output 1 decoder (B'A)
circuit.MOSFET('M11', 'Y1_int', 'B_inv', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M12', 'Y1_int', 'A_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M13', 'Y1_int', 'B_inv', 'Y1_n', circuit.gnd, model='NMOS')
circuit.MOSFET('M14', 'Y1_n', 'A_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C5', 'Y1_int', circuit.gnd, 0.1@u_pF)

# Output buffer for Y1
circuit.MOSFET('M15', 'Y1', 'Y1_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M16', 'Y1', 'Y1_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C6', 'Y1', circuit.gnd, 0.1@u_pF)

# Output 2 decoder (BA')
circuit.MOSFET('M17', 'Y2_int', 'B_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M18', 'Y2_int', 'A_inv', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M19', 'Y2_int', 'B_int', 'Y2_n', circuit.gnd, model='NMOS')
circuit.MOSFET('M20', 'Y2_n', 'A_inv', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C7', 'Y2_int', circuit.gnd, 0.1@u_pF)

# Output buffer for Y2
circuit.MOSFET('M21', 'Y2', 'Y2_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M22', 'Y2', 'Y2_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C8', 'Y2', circuit.gnd, 0.1@u_pF)

# Output 3 decoder (BA)
circuit.MOSFET('M23', 'Y3_int', 'B_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M24', 'Y3_int', 'A_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M25', 'Y3_int', 'B_int', 'Y3_n', circuit.gnd, model='NMOS')
circuit.MOSFET('M26', 'Y3_n', 'A_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C9', 'Y3_int', circuit.gnd, 0.1@u_pF)

# Output buffer for Y3
circuit.MOSFET('M27', 'Y3', 'Y3_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M28', 'Y3', 'Y3_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C10', 'Y3', circuit.gnd, 0.1@u_pF)

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
    method='gear'
)

try:
    # Run transient analysis
    analysis = simulator.transient(
        step_time=0.1@u_ns,
        end_time=200@u_ns,
        start_time=0@u_ns,
        max_time=0.2@u_ns,
        use_initial_condition=True
    )

    # Convert time and voltage data to numpy arrays
    time = np.array([float(t) for t in analysis.time])
    va = np.array([float(v) for v in analysis['A']])
    vb = np.array([float(v) for v in analysis['B']])
    vy0 = np.array([float(v) for v in analysis['Y0']])
    vy1 = np.array([float(v) for v in analysis['Y1']])
    vy2 = np.array([float(v) for v in analysis['Y2']])
    vy3 = np.array([float(v) for v in analysis['Y3']])

    # Create plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot inputs
    ax1.plot(time, vb, label='B (MSB)', linestyle='--', color='blue')
    ax1.plot(time, va, label='A (LSB)', linestyle='--', color='red')
    ax1.grid(True)
    ax1.set_title('2-to-4 Decoder - Inputs')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Voltage (V)')
    ax1.legend()
    ax1.set_ylim(-0.5, 4)

    # Plot outputs
    ax2.plot(time, vy0, label='Y0 (00)', color='purple')
    ax2.plot(time, vy1, label='Y1 (01)', color='orange')
    ax2.plot(time, vy2, label='Y2 (10)', color='green')
    ax2.plot(time, vy3, label='Y3 (11)', color='brown')
    ax2.grid(True)
    ax2.set_title('2-to-4 Decoder - Outputs')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Voltage (V)')
    ax2.legend()
    ax2.set_ylim(-0.5, 4)

    plt.tight_layout()
    plt.show()

    # Analyze decoder characteristics
    def analyze_decoder(time, va, vb, vy0, vy1, vy2, vy3, vth=1.65):
        """Verify decoder functionality and calculate delays"""
        def to_binary(v):
            return 1 if v > vth else 0
        
        def find_transitions(time, signal):
            binary = [to_binary(v) for v in signal]
            transitions = []
            for i in range(1, len(binary)):
                if binary[i] != binary[i-1]:
                    transitions.append(i)
            return transitions
        
        # Calculate propagation delays
        a_trans = find_transitions(time, va)
        output_delays = []
        
        for t_in in a_trans:
            for signal in [vy0, vy1, vy2, vy3]:
                out_trans = find_transitions(time, signal)
                for t_out in out_trans:
                    if t_out > t_in:
                        delay = time[t_out] - time[t_in]
                        output_delays.append(delay)
                        break
        
        if output_delays:
            print(f"Average propagation delay: {np.mean(output_delays):.2e} seconds")
            print(f"Maximum propagation delay: {np.max(output_delays):.2e} seconds")
            print(f"Minimum propagation delay: {np.min(output_delays):.2e} seconds")

    analyze_decoder(time, va, vb, vy0, vy1, vy2, vy3)

except Exception as e:
    print(f"Simulation failed: {str(e)}")
    print("Detailed error information:")
    import traceback
    traceback.print_exc()

print(circuit)