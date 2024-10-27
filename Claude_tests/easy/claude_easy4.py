from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

# Create the SR Latch circuit
circuit = Circuit('SR Latch')

# Define power supply with ramp-up
circuit.PulseVoltageSource('dd', 'vdd', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,  # Using 3.3V for better stability
    delay_time=0@u_ns,
    rise_time=0.5@u_ns,
    fall_time=0.5@u_ns,
    pulse_width=250@u_ns,
    period=250@u_ns
)

# Add supply resistor and decoupling capacitor
circuit.R('Rvdd', 'vdd', 'vdd_internal', 1@u_Ω)
circuit.C('Cvdd', 'vdd_internal', circuit.gnd, 1@u_pF)

# Define input voltage sources with delayed start
# Set input pulse
circuit.PulseVoltageSource('set', 'S', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,
    delay_time=10@u_ns,
    rise_time=0.1@u_ns,
    fall_time=0.1@u_ns,
    pulse_width=30@u_ns,
    period=100@u_ns
)

# Reset input pulse
circuit.PulseVoltageSource('reset', 'R', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,
    delay_time=60@u_ns,
    rise_time=0.1@u_ns,
    fall_time=0.1@u_ns,
    pulse_width=30@u_ns,
    period=100@u_ns
)

# Add input protection and parasitic capacitance
for node in ['S', 'R']:
    circuit.R(f'Rin_{node}', node, f'{node}_int', 100@u_Ω)
    circuit.C(f'Cin_{node}', f'{node}_int', circuit.gnd, 0.1@u_pF)

# NOR Gate 1 (Set side)
# PMOS transistors in series
circuit.MOSFET('M1', 'int1', 'S_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M2', 'Q', 'Qbar', 'int1', 'vdd_internal', model='PMOS')
circuit.C('CQ', 'Q', circuit.gnd, 0.1@u_pF)

# NMOS transistors in parallel
circuit.MOSFET('M3', 'Q', 'S_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('M4', 'Q', 'Qbar', circuit.gnd, circuit.gnd, model='NMOS')

# NOR Gate 2 (Reset side)
# PMOS transistors in series
circuit.MOSFET('M5', 'int2', 'R_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M6', 'Qbar', 'Q', 'int2', 'vdd_internal', model='PMOS')
circuit.C('CQbar', 'Qbar', circuit.gnd, 0.1@u_pF)

# NMOS transistors in parallel
circuit.MOSFET('M7', 'Qbar', 'R_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('M8', 'Qbar', 'Q', circuit.gnd, circuit.gnd, model='NMOS')

# Add weak pull-up/pull-down resistors for initial state
circuit.R('RQ_pu', 'Q', 'vdd_internal', 1@u_MΩ)
circuit.R('RQbar_pd', 'Qbar', circuit.gnd, 1@u_MΩ)

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
    vs = np.array([float(v) for v in analysis['S']])
    vr = np.array([float(v) for v in analysis['R']])
    vq = np.array([float(v) for v in analysis['Q']])
    vqbar = np.array([float(v) for v in analysis['Qbar']])

    # Create plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot inputs
    ax1.plot(time, vs, label='Set', linestyle='--', color='blue')
    ax1.plot(time, vr, label='Reset', linestyle='--', color='red')
    ax1.grid(True)
    ax1.set_title('SR Latch - Inputs')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Voltage (V)')
    ax1.legend()
    ax1.set_ylim(-0.5, 4)

    # Plot outputs
    ax2.plot(time, vq, label='Q', color='green')
    ax2.plot(time, vqbar, label='Qbar', color='orange')
    ax2.grid(True)
    ax2.set_title('SR Latch - Outputs')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Voltage (V)')
    ax2.legend()
    ax2.set_ylim(-0.5, 4)

    plt.tight_layout()
    plt.show()

    # Analyze timing characteristics
    def analyze_timing(time, vs, vr, vq, vqbar, vth=1.65):
        """Calculate propagation delays and verify functionality"""
        def find_edges(time, signal, rising=True):
            edges = []
            for i in range(1, len(signal)):
                if rising and signal[i-1] < vth < signal[i]:
                    edges.append(i)
                elif not rising and signal[i-1] > vth > signal[i]:
                    edges.append(i)
            return edges

        # Find rising and falling edges
        s_edges = find_edges(time, vs, rising=True)
        r_edges = find_edges(time, vr, rising=True)
        q_edges_r = find_edges(time, vq, rising=True)
        q_edges_f = find_edges(time, vq, rising=False)

        # Calculate delays
        set_delays = []
        reset_delays = []

        for s_edge in s_edges:
            for q_edge in q_edges_r:
                if q_edge > s_edge:
                    delay = time[q_edge] - time[s_edge]
                    set_delays.append(delay)
                    break

        for r_edge in r_edges:
            for q_edge in q_edges_f:
                if q_edge > r_edge:
                    delay = time[q_edge] - time[r_edge]
                    reset_delays.append(delay)
                    break

        if set_delays:
            print(f"Average Set-to-Q delay: {np.mean(set_delays):.2e} seconds")
        if reset_delays:
            print(f"Average Reset-to-Q delay: {np.mean(reset_delays):.2e} seconds")

    analyze_timing(time, vs, vr, vq, vqbar)

except Exception as e:
    print(f"Simulation failed: {str(e)}")
    print("Detailed error information:")
    import traceback
    traceback.print_exc()

print(circuit)