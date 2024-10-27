from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt

# Initialize Circuit
circuit = Circuit('8-Bit Shift Register with Custom D Flip-Flops')

def create_nand_gate(circuit, name, a, b, out, vdd):
    """Create a NAND gate using CMOS transistors with pull-up/pull-down"""
    # Add pull-up resistor to prevent floating
    circuit.R(f'{name}_pullup', vdd, out, 100@u_kΩ)
    
    # PMOS parallel network (pull-up)
    circuit.MOSFET(f'{name}_P1', out, a, vdd, vdd, model='PMOS', w=20e-6, l=1e-6)
    circuit.MOSFET(f'{name}_P2', out, b, vdd, vdd, model='PMOS', w=20e-6, l=1e-6)
    
    # NMOS series network (pull-down)
    mid_node = f'{name}_mid'
    circuit.MOSFET(f'{name}_N1', mid_node, a, circuit.gnd, circuit.gnd, model='NMOS', w=10e-6, l=1e-6)
    circuit.MOSFET(f'{name}_N2', out, b, mid_node, circuit.gnd, model='NMOS', w=10e-6, l=1e-6)
    
    # Add stabilizing capacitor
    circuit.C(f'{name}_stab', out, circuit.gnd, 0.1@u_pF)

def create_d_flip_flop(circuit, name, d, clk, q, qb, vdd):
    """Create D Flip-Flop using NAND gates with proper interconnections"""
    # Internal nodes with pull-up resistors
    master_1 = f'{name}_master1'
    master_2 = f'{name}_master2'
    
    # Master latch
    create_nand_gate(circuit, f'{name}_NAND1', d, clk, master_1, vdd)
    create_nand_gate(circuit, f'{name}_NAND2', master_1, clk, master_2, vdd)
    
    # Slave latch
    create_nand_gate(circuit, f'{name}_NAND3', master_2, qb, q, vdd)
    create_nand_gate(circuit, f'{name}_NAND4', q, clk, qb, vdd)
    
    # Add cross-coupled stabilizing resistors
    circuit.R(f'{name}_cross1', q, qb, 1@u_MΩ)

# Power supply
circuit.V('VDD', 'vdd', circuit.gnd, 3.3@u_V)

# Clock signal (reduced frequency for better convergence)
circuit.PulseVoltageSource('CLK', 'clk', circuit.gnd, 
                          initial_value=0@u_V,
                          pulsed_value=3.3@u_V,
                          delay_time=0@u_ns,
                          rise_time=10@u_ns,
                          fall_time=10@u_ns,
                          pulse_width=5@u_us,
                          period=10@u_us)

# Data input
circuit.PulseVoltageSource('DATA', 'data_in', circuit.gnd,
                          initial_value=0@u_V,
                          pulsed_value=3.3@u_V,
                          delay_time=0@u_ns,
                          rise_time=10@u_ns,
                          fall_time=10@u_ns,
                          pulse_width=40@u_us,
                          period=80@u_us)

# Define MOSFET models with adjusted parameters for better convergence
circuit.model('NMOS', 'nmos',
             Level=1,
             Vto=0.7,
             Kp=120e-6,
             Gamma=0.4,
             Phi=0.65,
             Lambda=0.01,
             Rd=10,
             Rs=10,
             Cbd=2e-15,
             Cbs=2e-15,
             Is=1e-14,
             N=1.0,
             Tnom=27)

circuit.model('PMOS', 'pmos',
             Level=1,
             Vto=-0.7,
             Kp=40e-6,
             Gamma=0.4,
             Phi=0.65,
             Lambda=0.01,
             Rd=10,
             Rs=10,
             Cbd=2e-15,
             Cbs=2e-15,
             Is=1e-14,
             N=1.0,
             Tnom=27)

# Create 8-bit shift register with proper DC paths
for i in range(8):
    d_node = f'd_{i}'
    q_node = f'q_{i}'
    qb_node = f'qb_{i}'
    
    # Add pull-down resistors for input nodes
    circuit.R(f'R_pd_{i}', d_node, circuit.gnd, 1@u_MΩ)
    
    # Connect stages with proper buffering
    if i == 0:
        circuit.R(f'R_in_{i}', 'data_in', d_node, 1@u_kΩ)
    else:
        circuit.R(f'R_stage_{i}', f'q_{i-1}', d_node, 1@u_kΩ)
    
    # Create D Flip-Flop
    create_d_flip_flop(circuit, f'DFF_{i}', d_node, 'clk', q_node, qb_node, 'vdd')

# Simulation with adjusted parameters
simulator = circuit.simulator(temperature=27, nominal_temperature=27)
simulator.options(
    reltol=1e-3,
    abstol=1e-6,
    vntol=1e-4,
    chgtol=1e-14,
    trtol=7,
    itl1=100,
    itl2=50,
    itl4=10,
    method='gear'
)

try:
    # Run transient analysis with larger step time
    analysis = simulator.transient(
        step_time=0.1@u_us,
        end_time=200@u_us,
        use_initial_condition=True,
        max_time=0.2@u_us
    )

    # Plot results
    plt.figure(figsize=(12, 8))
    
    # Plot clock
    plt.subplot(3, 1, 1)
    plt.plot(analysis.time, analysis['clk'], label='Clock')
    plt.grid(True)
    plt.legend()
    plt.title('8-Bit Shift Register Simulation')
    
    # Plot data input
    plt.subplot(3, 1, 2)
    plt.plot(analysis.time, analysis['data_in'], label='Data Input')
    plt.grid(True)
    plt.legend()
    
    # Plot outputs
    plt.subplot(3, 1, 3)
    for i in range(8):
        plt.plot(analysis.time, analysis[f'q_{i}'], label=f'Q{i}')
    plt.grid(True)
    plt.legend()
    plt.xlabel('Time [s]')
    
    plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"Simulation failed: {e}")
    print("Try adjusting simulation parameters or circuit values")