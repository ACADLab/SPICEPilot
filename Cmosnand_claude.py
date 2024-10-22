from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt

# Initialize the circuit
circuit = Circuit('CMOS NAND Gate')

# Define Supply and Inputs
circuit.V(1, 'Vdd', circuit.gnd, 5@u_V)  # Vdd = 5V
circuit.PulseVoltageSource('Vin1', 'input1', circuit.gnd, 
                           initial_value=0@u_V, pulsed_value=5@u_V,
                           rise_time=1@u_ns, fall_time=1@u_ns, 
                           pulse_width=10@u_ns, period=20@u_ns)  # Input1
circuit.PulseVoltageSource('Vin2', 'input2', circuit.gnd, 
                           initial_value=0@u_V, pulsed_value=5@u_V,
                           rise_time=1@u_ns, fall_time=1@u_ns, 
                           pulse_width=10@u_ns, period=20@u_ns)  # Input2

# Define PMOS Transistors (parallel connection)
circuit.MOSFET('P1', 'output', 'input1', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('P2', 'output', 'input2', 'Vdd', 'Vdd', model='PMOS')

# Define NMOS Transistors (series connection)
circuit.MOSFET('N1', 'output', 'input1', 'n_mid', circuit.gnd, model='NMOS')
circuit.MOSFET('N2', 'n_mid', 'input2', circuit.gnd, circuit.gnd, model='NMOS')

# Define MOSFET Models
circuit.model('PMOS', 'pmos', kp=60e-6, vto=-1, lambda_=0.02, w=20e-6, l=1e-6)
circuit.model('NMOS', 'nmos', kp=120e-6, vto=1, lambda_=0.02, w=10e-6, l=1e-6)

# Set up the transient simulation
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=1@u_ns, end_time=100@u_ns)

# Plotting the input and output signals
fig, axs = plt.subplots(3, 1, sharex=True)  # Create 3 subplots, sharing the x-axis

# Input 1
axs[0].plot(analysis.time, analysis['input1'], label='Input 1', color='blue')
axs[0].set_ylabel('Voltage [V]')
axs[0].legend()
axs[0].grid()

# Input 2
axs[1].plot(analysis.time, analysis['input2'], label='Input 2', color='orange')
axs[1].set_ylabel('Voltage [V]')
axs[1].legend()
axs[1].grid()

# Output
axs[2].plot(analysis.time, analysis['output'], label='Output (NAND)', color='green')
axs[2].set_xlabel('Time [s]')
axs[2].set_ylabel('Voltage [V]')
axs[2].legend()
axs[2].grid()

fig.suptitle('CMOS NAND Gate Transient Analysis')  # Overall title for the figure

plt.tight_layout()  # Adjust spacing to prevent overlap
plt.show()
print(circuit)
