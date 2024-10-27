from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

# Create the Full Adder circuit
circuit = Circuit('CMOS Full Adder')

# Define power supply with ramp-up
circuit.PulseVoltageSource('dd', 'vdd', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,  # Using 3.3V for better stability
    delay_time=0@u_ns,
    rise_time=0.5@u_ns,
    fall_time=0.5@u_ns,
    pulse_width=200@u_ns,
    period=200@u_ns
)

# Add supply resistor and decoupling capacitor
circuit.R('Rvdd', 'vdd', 'vdd_internal', 1@u_Ω)
circuit.C('Cvdd', 'vdd_internal', circuit.gnd, 1@u_pF)

# Define input voltage sources with delays to ensure power-up completes first
# Input A
circuit.PulseVoltageSource('inA', 'A', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,
    delay_time=1@u_ns,
    rise_time=0.1@u_ns,
    fall_time=0.1@u_ns,
    pulse_width=40@u_ns,
    period=80@u_ns
)

# Input B
circuit.PulseVoltageSource('inB', 'B', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,
    delay_time=1@u_ns,
    rise_time=0.1@u_ns,
    fall_time=0.1@u_ns,
    pulse_width=20@u_ns,
    period=40@u_ns
)

# Carry In
circuit.PulseVoltageSource('inCin', 'Cin', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,
    delay_time=1@u_ns,
    rise_time=0.1@u_ns,
    fall_time=0.1@u_ns,
    pulse_width=10@u_ns,
    period=20@u_ns
)

# Add input protection and parasitic capacitance
for node in ['A', 'B', 'Cin']:
    circuit.R(f'Rin_{node}', node, f'{node}_int', 100@u_Ω)
    circuit.C(f'Cin_{node}', f'{node}_int', circuit.gnd, 0.1@u_pF)

# XOR gate for A ⊕ B
# NAND1
circuit.MOSFET('M1', 'nand1_out', 'A_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M2', 'nand1_out', 'B_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M3', 'nand1_out', 'A_int', 'nand1_n', circuit.gnd, model='NMOS')
circuit.MOSFET('M4', 'nand1_n', 'B_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C1', 'nand1_out', circuit.gnd, 0.1@u_pF)

# Additional NANDs for XOR implementation
circuit.MOSFET('M5', 'xor_out', 'nand1_out', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M6', 'xor_out', 'A_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M7', 'xor_out', 'nand1_out', 'xor_n', circuit.gnd, model='NMOS')
circuit.MOSFET('M8', 'xor_n', 'A_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C2', 'xor_out', circuit.gnd, 0.1@u_pF)

# Second XOR for Sum (XOR with Cin)
circuit.MOSFET('M9', 'sum_int', 'xor_out', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M10', 'sum_int', 'Cin_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M11', 'sum_int', 'xor_out', 'sum_n', circuit.gnd, model='NMOS')
circuit.MOSFET('M12', 'sum_n', 'Cin_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C3', 'sum_int', circuit.gnd, 0.1@u_pF)

# Carry Out logic
circuit.MOSFET('M13', 'cout_int', 'A_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M14', 'cout_int', 'B_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M15', 'cout_int', 'Cin_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M16', 'cout_int', 'A_int', 'cout_n1', circuit.gnd, model='NMOS')
circuit.MOSFET('M17', 'cout_n1', 'B_int', 'cout_n2', circuit.gnd, model='NMOS')
circuit.MOSFET('M18', 'cout_n2', 'Cin_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C4', 'cout_int', circuit.gnd, 0.1@u_pF)

# Output buffers
circuit.MOSFET('M19', 'Sum', 'sum_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M20', 'Sum', 'sum_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C5', 'Sum', circuit.gnd, 0.1@u_pF)

circuit.MOSFET('M21', 'Cout', 'cout_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M22', 'Cout', 'cout_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('C6', 'Cout', circuit.gnd, 0.1@u_pF)

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
        step_time=10@u_ns,
        end_time=100@u_ns,
        start_time=0@u_ns,
        max_time=0.2@u_ns,
        use_initial_condition=True
    )

    # Convert time and voltage data
    time = np.array([float(t) for t in analysis.time])
    va = np.array([float(v) for v in analysis['A']])
    vb = np.array([float(v) for v in analysis['B']])
    vcin = np.array([float(v) for v in analysis['Cin']])
    vsum = np.array([float(v) for v in analysis['Sum']])
    vcout = np.array([float(v) for v in analysis['Cout']])

    # Create plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot inputs
    ax1.plot(time, va, label='A', linestyle='--')
    ax1.plot(time, vb, label='B', linestyle='--')
    ax1.plot(time, vcin, label='Cin', linestyle='--')
    ax1.grid(True)
    ax1.set_title('Full Adder - Inputs')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Voltage (V)')
    ax1.legend()
    ax1.set_ylim(-0.5, 4)

    # Plot outputs
    ax2.plot(time, vsum, label='Sum')
    ax2.plot(time, vcout, label='Cout')
    ax2.grid(True)
    ax2.set_title('Full Adder - Outputs')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Voltage (V)')
    ax2.legend()
    ax2.set_ylim(-0.5, 4)

    plt.tight_layout()
    plt.show()

    # Verify functionality
    def analyze_full_adder(time, va, vb, vcin, vsum, vcout, vth=1.65):
        """Verify full adder logic and calculate delays"""
        def to_binary(v):
            return 1 if v > vth else 0
        
        def find_transitions(time, signal):
            binary = [to_binary(v) for v in signal]
            transitions = []
            for i in range(1, len(binary)):
                if binary[i] != binary[i-1]:
                    transitions.append(time[i])
            return transitions
        
        # Calculate propagation delays
        a_trans = find_transitions(time, va)
        sum_trans = find_transitions(time, vsum)
        cout_trans = find_transitions(time, vcout)
        
        if a_trans and sum_trans:
            sum_delay = min(abs(st - at) for st in sum_trans for at in a_trans)
            print(f"Average Sum propagation delay: {sum_delay:.2e} seconds")
        
        if a_trans and cout_trans:
            cout_delay = min(abs(ct - at) for ct in cout_trans for at in a_trans)
            print(f"Average Cout propagation delay: {cout_delay:.2e} seconds")

    analyze_full_adder(time, va, vb, vcin, vsum, vcout)

except Exception as e:
    print(f"Simulation failed: {str(e)}")
    print("Detailed error information:")
    import traceback
    traceback.print_exc()

print(circuit)