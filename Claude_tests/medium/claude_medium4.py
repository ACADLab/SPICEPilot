from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

# Create the D Flip-Flop circuit
circuit = Circuit('D Flip-Flop')

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
# Clock signal
circuit.PulseVoltageSource('clk', 'clock', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,
    delay_time=2@u_ns,
    rise_time=0.1@u_ns,
    fall_time=0.1@u_ns,
    pulse_width=20@u_ns,
    period=40@u_ns
)

# Data input
circuit.PulseVoltageSource('din', 'D', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=3.3@u_V,
    delay_time=5@u_ns,
    rise_time=0.1@u_ns,
    fall_time=0.1@u_ns,
    pulse_width=30@u_ns,
    period=60@u_ns
)

# Add input protection and parasitic capacitance
for node in ['clock', 'D']:
    circuit.R(f'Rin_{node}', node, f'{node}_int', 100@u_Ω)
    circuit.C(f'Cin_{node}', f'{node}_int', circuit.gnd, 0.1@u_pF)

# Create clock inverter
circuit.MOSFET('M1', 'clock_inv', 'clock_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M2', 'clock_inv', 'clock_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('Cclk_inv', 'clock_inv', circuit.gnd, 0.1@u_pF)

# Master stage
# Input inverter
circuit.MOSFET('M3', 'D_inv', 'D_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M4', 'D_inv', 'D_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('CD_inv', 'D_inv', circuit.gnd, 0.1@u_pF)

# Master latch
circuit.MOSFET('M5', 'master_int', 'D_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M6', 'master_int', 'clock_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('M7', 'master_out', 'master_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M8', 'master_out', 'master_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('Cmaster', 'master_out', circuit.gnd, 0.1@u_pF)

# Slave stage
circuit.MOSFET('M9', 'slave_int', 'master_out', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M10', 'slave_int', 'clock_inv', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('M11', 'Q', 'slave_int', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M12', 'Q', 'slave_int', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('CQ', 'Q', circuit.gnd, 0.1@u_pF)

# Output inverter for Q_bar
circuit.MOSFET('M13', 'Q_bar', 'Q', 'vdd_internal', 'vdd_internal', model='PMOS')
circuit.MOSFET('M14', 'Q_bar', 'Q', circuit.gnd, circuit.gnd, model='NMOS')
circuit.C('CQbar', 'Q_bar', circuit.gnd, 0.1@u_pF)

# Add weak pull-up/pull-down for initialization
circuit.R('Rpd_master', 'master_int', circuit.gnd, 1@u_MΩ)
circuit.R('Rpd_slave', 'slave_int', circuit.gnd, 1@u_MΩ)

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
    vclk = np.array([float(v) for v in analysis['clock']])
    vd = np.array([float(v) for v in analysis['D']])
    vq = np.array([float(v) for v in analysis['Q']])
    vqbar = np.array([float(v) for v in analysis['Q_bar']])
    vmaster = np.array([float(v) for v in analysis['master_out']])

    # Create plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot inputs
    ax1.plot(time, vclk, label='Clock', color='blue')
    ax1.plot(time, vd, label='D', linestyle='--', color='red')
    ax1.grid(True)
    ax1.set_title('D Flip-Flop - Inputs')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Voltage (V)')
    ax1.legend()
    ax1.set_ylim(-0.5, 4)

    # Plot outputs and internal nodes
    ax2.plot(time, vmaster, label='Master', color='green', alpha=0.5)
    ax2.plot(time, vq, label='Q', color='purple')
    ax2.plot(time, vqbar, label='Q_bar', color='orange')
    ax2.grid(True)
    ax2.set_title('D Flip-Flop - Internal Nodes and Outputs')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Voltage (V)')
    ax2.legend()
    ax2.set_ylim(-0.5, 4)

    plt.tight_layout()
    plt.show()

    # Analyze timing characteristics
    def analyze_timing(time, vclk, vd, vq, vth=1.65):
        """Calculate setup time, hold time, and clock-to-Q delay"""
        def find_edges(time, signal, rising=True):
            edges = []
            for i in range(1, len(signal)):
                if rising and signal[i-1] < vth < signal[i]:
                    edges.append(i)
                elif not rising and signal[i-1] > vth > signal[i]:
                    edges.append(i)
            return edges

        # Find edges
        clk_edges = find_edges(time, vclk, rising=True)
        d_edges = find_edges(time, vd)
        q_edges = find_edges(time, vq)

        # Calculate delays
        clk_q_delays = []
        setup_times = []
        hold_times = []

        for clk_edge in clk_edges:
            # Clock-to-Q delay
            for q_edge in q_edges:
                if q_edge > clk_edge:
                    delay = time[q_edge] - time[clk_edge]
                    if delay < 10e-9:  # Reasonable delay window
                        clk_q_delays.append(delay)
                    break

            # Setup and hold times
            for d_edge in d_edges:
                if abs(time[d_edge] - time[clk_edge]) < 10e-9:
                    if d_edge < clk_edge:
                        setup_times.append(time[clk_edge] - time[d_edge])
                    else:
                        hold_times.append(time[d_edge] - time[clk_edge])

        if clk_q_delays:
            print(f"Average Clock-to-Q delay: {np.mean(clk_q_delays):.2e} seconds")
        if setup_times:
            print(f"Average setup time: {np.mean(setup_times):.2e} seconds")
        if hold_times:
            print(f"Average hold time: {np.mean(hold_times):.2e} seconds")

    analyze_timing(time, vclk, vd, vq)

except Exception as e:
    print(f"Simulation failed: {str(e)}")
    print("Detailed error information:")
    import traceback
    traceback.print_exc()

print(circuit)