from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
from PySpice.Probe.Plot import plot

# Create the circuit
circuit = Circuit('CMOS 4:1 Multiplexer')

# Supply voltage (Vdd)
circuit.V(1, 'Vdd', circuit.gnd, 5@u_V)

# Input signals: I0, I1, I2, I3
circuit.PulseVoltageSource('I0', 'input_I0', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=20@u_ns, period=80@u_ns)
circuit.PulseVoltageSource('I1', 'input_I1', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=40@u_ns, period=80@u_ns)
circuit.PulseVoltageSource('I2', 'input_I2', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=60@u_ns, period=80@u_ns)
circuit.PulseVoltageSource('I3', 'input_I3', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=80@u_ns, period=80@u_ns)

# Select lines: S1 and S0
circuit.PulseVoltageSource('S1', 'select_S1', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=30@u_ns, period=60@u_ns)
circuit.PulseVoltageSource('S0', 'select_S0', circuit.gnd, initial_value=0@u_V, pulsed_value=5@u_V, rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=15@u_ns, period=30@u_ns)

# Inverters for select lines (for S1' and S0')
# Inverter for S1'
circuit.MOSFET('PM_INV1', 'select_S1_bar', 'select_S1', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM_INV1', 'select_S1_bar', 'select_S1', circuit.gnd, circuit.gnd, model='NMOS')

# Inverter for S0'
circuit.MOSFET('PM_INV2', 'select_S0_bar', 'select_S0', 'Vdd', 'Vdd', model='PMOS')
circuit.MOSFET('NM_INV2', 'select_S0_bar', 'select_S0', circuit.gnd, circuit.gnd, model='NMOS')

# Transmission gates for each input (controlled by select lines)
# Transmission gate for I0 (controlled by S1' and S0')
circuit.MOSFET('PM_TG0', 'out', 'input_I0', 'Vdd', 'select_S1_bar', model='PMOS')
circuit.MOSFET('NM_TG0', 'out', 'input_I0', circuit.gnd, 'select_S0_bar', model='NMOS')

# Transmission gate for I1 (controlled by S1' and S0)
circuit.MOSFET('PM_TG1', 'out', 'input_I1', 'Vdd', 'select_S1_bar', model='PMOS')
circuit.MOSFET('NM_TG1', 'out', 'input_I1', circuit.gnd, 'select_S0', model='NMOS')

# Transmission gate for I2 (controlled by S1 and S0')
circuit.MOSFET('PM_TG2', 'out', 'input_I2', 'Vdd', 'select_S1', model='PMOS')
circuit.MOSFET('NM_TG2', 'out', 'input_I2', circuit.gnd, 'select_S0_bar', model='NMOS')

# Transmission gate for I3 (controlled by S1 and S0)
circuit.MOSFET('PM_TG3', 'out', 'input_I3', 'Vdd', 'select_S1', model='PMOS')
circuit.MOSFET('NM_TG3', 'out', 'input_I3', circuit.gnd, 'select_S0', model='NMOS')

# Define NMOS and PMOS models with simplified parameters
circuit.model('NMOS', 'nmos', kp=120e-6, vto=1)
circuit.model('PMOS', 'pmos', kp=60e-6, vto=-1)

# Stabilize the output node
circuit.R(2, 'out', circuit.gnd, 1@u_MΩ)

# Simulation settings: Transient analysis with extended end time
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=1@u_ns, end_time=200@u_ns)

# Plot the output signal
plt.figure()
plt.plot(analysis.time, analysis['out'], label='MUX Output (Selected Input)')
plt.plot(analysis.time, analysis['input_I0'], label='Input I0')
plt.plot(analysis.time, analysis['input_I1'], label='Input I1')
plt.plot(analysis.time, analysis['input_I2'], label='Input I2')
plt.plot(analysis.time, analysis['input_I3'], label='Input I3')
plt.plot(analysis.time, analysis['select_S1'], label='Select Line S1')
plt.plot(analysis.time, analysis['select_S0'], label='Select Line S0')
plt.title('Transient Analysis of CMOS 4:1 Multiplexer')
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')
plt.legend()
plt.grid()
plt.show()
