from PySpice.Spice.Netlist import Circuit, SubCircuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

class DFlipFlop(SubCircuit):
    """D Flip-Flop with improved stability and convergence"""
    __nodes__ = ('D', 'CLK', 'Q', 'VDD', 'GND')
    
    def __init__(self, name):
        SubCircuit.__init__(self, name)
        
        # Input stage with protection and stability components
        self.R('Rin', 'D', 'D_int', 100@u_Ω)
        self.C('Cin', 'D_int', 'GND', 0.1@u_pF)
        
        # Clock input protection
        self.R('Rclk', 'CLK', 'CLK_int', 100@u_Ω)
        self.C('Cclk', 'CLK_int', 'GND', 0.1@u_pF)
        
        # Master stage
        self.MOSFET('M1', 'master_1', 'D_int', 'VDD', 'VDD', model='PMOS')
        self.MOSFET('M2', 'master_1', 'D_int', 'GND', 'GND', model='NMOS')
        self.C('Cm1', 'master_1', 'GND', 0.1@u_pF)
        
        self.MOSFET('M3', 'master_2', 'master_1', 'VDD', 'VDD', model='PMOS')
        self.MOSFET('M4', 'master_2', 'CLK_int', 'GND', 'GND', model='NMOS')
        self.C('Cm2', 'master_2', 'GND', 0.1@u_pF)
        
        # Slave stage
        self.MOSFET('M5', 'slave_1', 'master_2', 'VDD', 'VDD', model='PMOS')
        self.MOSFET('M6', 'slave_1', 'CLK_int', 'GND', 'GND', model='NMOS')
        self.C('Cs1', 'slave_1', 'GND', 0.1@u_pF)
        
        # Output stage with buffer
        self.MOSFET('M7', 'Q_int', 'slave_1', 'VDD', 'VDD', model='PMOS')
        self.MOSFET('M8', 'Q_int', 'slave_1', 'GND', 'GND', model='NMOS')
        self.C('Cq_int', 'Q_int', 'GND', 0.1@u_pF)
        
        # Output buffer
        self.MOSFET('M9', 'Q', 'Q_int', 'VDD', 'VDD', model='PMOS')
        self.MOSFET('M10', 'Q', 'Q_int', 'GND', 'GND', model='NMOS')
        self.C('Cq', 'Q', 'GND', 0.1@u_pF)
        
        # Weak pull-down for initialization
        self.R('Rpd', 'Q', 'GND', 1@u_MΩ)

def create_8bit_shift_register():
    """Creates an 8-bit shift register with improved stability"""
    circuit = Circuit('8-Bit Shift Register')
    
    # Power supply with ramp-up
    circuit.PulseVoltageSource('dd', 'VDD', circuit.gnd,
        initial_value=0@u_V,
        pulsed_value=3.3@u_V,
        delay_time=0@u_ns,
        rise_time=1@u_ns,
        fall_time=1@u_ns,
        pulse_width=1000@u_ns,
        period=1000@u_ns
    )
    
    # Add supply filtering
    circuit.R('Rvdd', 'VDD', 'VDD_int', 1@u_Ω)
    circuit.C('Cvdd', 'VDD_int', circuit.gnd, 10@u_pF)
    
    # Clock signal with slower edges
    circuit.PulseVoltageSource('clk', 'CLK', circuit.gnd,
        initial_value=0@u_V,
        pulsed_value=3.3@u_V,
        delay_time=5@u_ns,
        rise_time=2@u_ns,
        fall_time=2@u_ns,
        pulse_width=20@u_ns,
        period=40@u_ns
    )
    
    # Data input signal
    circuit.PulseVoltageSource('data', 'DATA', circuit.gnd,
        initial_value=0@u_V,
        pulsed_value=3.3@u_V,
        delay_time=5@u_ns,
        rise_time=2@u_ns,
        fall_time=2@u_ns,
        pulse_width=60@u_ns,
        period=120@u_ns
    )
    
    # Input protection
    circuit.R('Rclk_in', 'CLK', 'CLK_filtered', 100@u_Ω)
    circuit.C('Cclk_in', 'CLK_filtered', circuit.gnd, 0.1@u_pF)
    circuit.R('Rdata_in', 'DATA', 'DATA_filtered', 100@u_Ω)
    circuit.C('Cdata_in', 'DATA_filtered', circuit.gnd, 0.1@u_pF)
    
    # Define MOSFET models with conservative parameters
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
    
    # Create and connect D flip-flops
    for i in range(8):
        circuit.subcircuit(DFlipFlop(f'FF{i}'))
        if i == 0:
            circuit.X(f'FF{i}', f'FF{i}', 'DATA_filtered', 'CLK_filtered', 
                     f'Q{i}', 'VDD_int', circuit.gnd)
        else:
            circuit.X(f'FF{i}', f'FF{i}', f'Q{i-1}', 'CLK_filtered', 
                     f'Q{i}', 'VDD_int', circuit.gnd)
        
        # Add output load
        circuit.C(f'Cload{i}', f'Q{i}', circuit.gnd, 0.1@u_pF)
    
    return circuit

def simulate_shift_register(circuit):
    """Simulates the shift register with improved convergence parameters"""
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
            end_time=2000@u_ns,
            start_time=0@u_ns,
            max_time=0.5@u_ns,
            use_initial_condition=True
        )
        
        # Convert time and voltage data
        time = np.array([float(t) for t in analysis.time])
        vclk = np.array([float(v) for v in analysis['CLK']])
        vdata = np.array([float(v) for v in analysis['DATA']])
        vout = [np.array([float(v) for v in analysis[f'Q{i}']]) for i in range(8)]
        
        # Create plots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        
        # Plot clock
        ax1.plot(time, vclk, label='Clock')
        ax1.grid(True)
        ax1.set_title('Clock Signal')
        ax1.set_ylabel('Voltage (V)')
        ax1.legend()
        ax1.set_ylim(-0.5, 4)
        
        # Plot input data
        ax2.plot(time, vdata, label='Data Input')
        ax2.grid(True)
        ax2.set_title('Data Input')
        ax2.set_ylabel('Voltage (V)')
        ax2.legend()
        ax2.set_ylim(-0.5, 4)
        
        # Plot outputs
        for i, v_out in enumerate(vout):
            ax3.plot(time, v_out, label=f'Q{i}')
        ax3.grid(True)
        ax3.set_title('Register Outputs')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Voltage (V)')
        ax3.legend()
        ax3.set_ylim(-0.5, 4)
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"Simulation failed: {str(e)}")
        print("Detailed error information:")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    circuit = create_8bit_shift_register()
    simulate_shift_register(circuit)
    print(circuit)