# SPICEPilot Pilot Prompt
# Comprehensive LLM Guide for PySpice/SPICE Code Generation
# Compatible with: ngspice 36+ through 42+ (2023–2025), PySpice >= 1.5

---

## SECTION 1: Version-Agnostic NgSpice & PySpice Setup

### Required Imports (always include all of these)
```python
from PySpice.Spice.Netlist import Circuit, SubCircuit
from PySpice.Unit import *
from PySpice.Spice.Library import SpiceLibrary
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
import numpy as np
```

### Ground Node Rule
Every circuit MUST have a ground reference. NgSpice requires node 0 (gnd) to exist.
```python
circuit = Circuit('My Circuit')
# Always use circuit.gnd for ground — never use the string '0' or 'gnd' directly
circuit.V('dd', 'vdd', circuit.gnd, 5@u_V)
```

### Unit System (PySpice @u_ notation)
```python
# Voltage
1@u_V      # 1 Volt
5@u_mV     # 5 millivolts
100@u_uV   # 100 microvolts

# Current
1@u_A      # 1 Ampere
10@u_mA    # 10 milliamperes
1@u_uA     # 1 microampere

# Resistance
1@u_Ω      # 1 Ohm  (also: 1@u_Ohm)
10@u_kΩ    # 10 kilohms
1@u_MΩ     # 1 megaohm

# Capacitance — AVAILABLE units in PySpice 1.5:
1@u_F      # 1 Farad
10@u_uF    # 10 microfarads
100@u_nF   # 100 nanofarads
1@u_pF     # 1 picofarad
# NOTE: u_fF (femtofarad) does NOT exist in PySpice 1.5
# Use: 0.1@u_pF  instead of  100@u_fF

# Inductance
1@u_H      # 1 Henry
10@u_mH    # 10 millihenries
1@u_uH     # 1 microhenry
1@u_nH     # 1 nanohenry

# Time / Frequency
1@u_s      # 1 second
1@u_ms     # 1 millisecond
1@u_us     # 1 microsecond
1@u_ns     # 1 nanosecond
1@u_ps     # 1 picosecond
1@u_Hz     # 1 Hertz
1@u_kHz    # 1 kilohertz
1@u_MHz    # 1 megahertz
1@u_GHz    # 1 gigahertz
```

### CRITICAL: PySpice 1.5 Available Units — Do NOT use u_fF, u_aF, u_fA
Always express sub-picofarad values in pF: `0.1@u_pF` not `100@u_fF`

---

## SECTION 2: Complete Component Reference

### Passive Components
```python
# Resistor
circuit.R('R1', 'node1', 'node2', 1@u_kΩ)
circuit.R('R2', 'a', 'b', 4700@u_Ω)
circuit.R('R3', 'x', 'y', 2.2@u_MΩ)
circuit.R('Rtc', 'n1', 'n2', 10@u_kΩ, tc1=0.001, tc2=0.0)  # temperature coeff

# Capacitor
circuit.C('C1', 'node1', 'node2', 100@u_pF)
circuit.C('C2', 'a', 'b', 10@u_uF, ic=0@u_V)  # initial condition

# Inductor
circuit.L('L1', 'node1', 'node2', 10@u_uH)
circuit.L('L2', 'a', 'b', 1@u_nH, ic=0@u_A)  # initial current
```

### Voltage and Current Sources
```python
# DC voltage source
circuit.V('supply', 'vdd', circuit.gnd, 5@u_V)

# Sinusoidal voltage source
circuit.SinusoidalVoltageSource('in', 'vin', circuit.gnd,
    offset=0@u_V,
    amplitude=1@u_V,
    frequency=1@u_MHz)

# Pulse voltage source
circuit.PulseVoltageSource('clk', 'clk', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=5@u_V,
    delay_time=0@u_ns,
    rise_time=1@u_ns,
    fall_time=1@u_ns,
    pulse_width=50@u_ns,
    period=100@u_ns)

# Piecewise linear source (PWL) — use raw SPICE string
circuit.V('pwl', 'vpwl', circuit.gnd, 'PWL(0 0 1n 5 2n 5 3n 0)')

# DC current source
circuit.I('ref', 'drain', circuit.gnd, 100@u_uA)
```

### Controlled Sources
```python
# Voltage-controlled voltage source (VCVS): E
circuit.VCVS('E1', 'out_p', 'out_n', 'in_p', 'in_n', voltage_gain=10)

# Voltage-controlled current source (VCCS): G
circuit.VCCS('G1', 'out_p', 'out_n', 'in_p', 'in_n', transconductance=1e-3)

# Current-controlled voltage source (CCVS): H
circuit.CCVS('H1', 'out_p', 'out_n', 'Vsense', transresistance=1e3)

# Current-controlled current source (CCCS): F
circuit.CCCS('F1', 'out_p', 'out_n', 'Vsense', current_gain=10)
```

### Diode
```python
circuit.Diode('D1', 'anode', 'cathode', model='DMOD')
circuit.model('DMOD', 'D', is_=1e-14, n=1.0, vj=0.7, cjo=1e-12)
```

### BJT Transistors
```python
# NPN BJT
circuit.BJT('Q1', 'collector', 'base', 'emitter', model='NPN_MOD')
circuit.model('NPN_MOD', 'npn', bf=100, vaf=100, is_=1e-15,
              rb=100, rc=10, re=1, cje=1e-12, cjc=1e-12)

# PNP BJT
circuit.BJT('Q2', 'collector', 'base', 'emitter', model='PNP_MOD')
circuit.model('PNP_MOD', 'pnp', bf=80, vaf=80, is_=1e-15)
```

### Switch
```python
# Voltage-controlled switch
circuit.VoltageControlledSwitch('SW1', 'drain', 'source', 'ctrl_p', 'ctrl_n', model='SWMOD')
circuit.model('SWMOD', 'sw', ron=1, roff=1e9, vt=2.5, vh=0.5)
```

---

## SECTION 3: MOSFET Models — Comprehensive

### Level 1 Model (standard, most compatible across ngspice versions)
```python
# NMOS — standard digital/analog
circuit.model('NMOS', 'nmos',
    level=1,
    kp=120e-6,      # transconductance parameter (A/V²) — 120uA/V² typical for NMOS
    vto=0.7,        # threshold voltage (positive for NMOS)
    lambda_=0.02,   # channel-length modulation (1/V)
    gamma=0.37,     # body effect coefficient (V^0.5)
    phi=0.65,       # surface potential (V)
    cbd=20e-15,     # bulk-drain junction capacitance (F)
    cbs=20e-15,     # bulk-source junction capacitance (F)
    is_=1e-14,      # bulk junction saturation current (A)
    tox=9e-9,       # gate oxide thickness (m)
    nsub=1e17,      # substrate doping (cm^-3)
    ld=0.05e-6)     # lateral diffusion (m)

# PMOS — standard digital/analog (kp ~half of NMOS, vto negative)
circuit.model('PMOS', 'pmos',
    level=1,
    kp=60e-6,       # lower mobility than NMOS
    vto=-0.7,       # threshold voltage (negative for PMOS)
    lambda_=0.02,
    gamma=0.37,
    phi=0.65,
    cbd=20e-15,
    cbs=20e-15,
    is_=1e-14,
    tox=9e-9)
```

### Width/Length Selection Guidelines
```python
# Digital gates (fast switching, balanced drive strength)
W_NMOS_DIGITAL = 10e-6   # 10 um
W_PMOS_DIGITAL = 20e-6   # 2x NMOS to compensate lower hole mobility
L_MIN = 1e-6             # 1 um minimum length

# Analog circuits (matching, low mismatch)
W_NMOS_ANALOG = 20e-6    # larger W for better matching and lower noise
W_PMOS_ANALOG = 40e-6
L_ANALOG = 2e-6          # longer L reduces lambda effect (higher ro)

# RF circuits (high fT, low parasitic)
W_RF = 50e-6             # wide for high current, multiple fingers
L_RF = 0.35e-6           # short for high fT (if process allows)

# Current mirrors (matching is critical)
W_MIRROR = 20e-6
L_MIRROR = 4e-6          # long L for high output resistance
```

### MOSFET Instantiation
```python
# NMOS: drain, gate, source, bulk
circuit.MOSFET('M1', 'drain', 'gate', circuit.gnd, circuit.gnd, model='NMOS')
# PMOS: drain, gate, source, bulk
circuit.MOSFET('M2', 'drain', 'gate', 'vdd', 'vdd', model='PMOS')

# With explicit W/L (override model defaults)
circuit.MOSFET('M3', 'out', 'in_', circuit.gnd, circuit.gnd,
               model='NMOS', w=20e-6, l=2e-6)
```

### Operating Region Bias Guidelines
```
Saturation (amplification): VGS > Vt, VDS > VGS - Vt
Linear/Triode (switch ON): VGS >> Vt, VDS < VGS - Vt
Cutoff (switch OFF): VGS < Vt
Subthreshold (low-power): VGS slightly below Vt
```

---

## SECTION 4: Circuit Family Templates

### 4A — CMOS Digital Gates

#### CMOS Inverter (NOT gate) — 2 transistors
```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

circuit = Circuit('CMOS Inverter')
circuit.V('dd', 'vdd', circuit.gnd, 5@u_V)
circuit.PulseVoltageSource('in', 'vin', circuit.gnd,
    initial_value=0@u_V, pulsed_value=5@u_V,
    rise_time=1@u_ns, fall_time=1@u_ns,
    pulse_width=20@u_ns, period=40@u_ns)

circuit.MOSFET('M1', 'vout', 'vin', circuit.gnd, circuit.gnd, model='NMOS')
circuit.MOSFET('M2', 'vout', 'vin', 'vdd', 'vdd', model='PMOS')

circuit.model('NMOS', 'nmos', level=1, kp=120e-6, vto=0.7, lambda_=0.02, w=10e-6, l=1e-6)
circuit.model('PMOS', 'pmos', level=1, kp=60e-6, vto=-0.7, lambda_=0.02, w=20e-6, l=1e-6)

simulator = circuit.simulator(temperature=25, nominal_temperature=25)
simulator.options(reltol=1e-5, abstol=1e-12, vntol=1e-6)
analysis = simulator.transient(step_time=0.5@u_ns, end_time=100@u_ns)

fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
axes[0].plot(np.array(analysis.time)*1e9, np.array(analysis['vin']), 'b-', label='Input')
axes[0].set_ylabel('Input (V)'); axes[0].legend(); axes[0].grid(True)
axes[1].plot(np.array(analysis.time)*1e9, np.array(analysis['vout']), 'r-', label='Output')
axes[1].set_ylabel('Output (V)'); axes[1].set_xlabel('Time (ns)'); axes[1].legend(); axes[1].grid(True)
plt.title('CMOS Inverter Transient Response')
plt.tight_layout()
plt.show()
```

#### CMOS NAND Gate — 4 transistors
```python
# PMOS in parallel (pull-up), NMOS in series (pull-down)
circuit.MOSFET('MP1', 'out', 'A', 'vdd', 'vdd', model='PMOS')  # parallel
circuit.MOSFET('MP2', 'out', 'B', 'vdd', 'vdd', model='PMOS')  # parallel
circuit.MOSFET('MN1', 'out', 'A', 'mid', circuit.gnd, model='NMOS')  # series
circuit.MOSFET('MN2', 'mid', 'B', circuit.gnd, circuit.gnd, model='NMOS')  # series
```

#### CMOS NOR Gate — 4 transistors
```python
# PMOS in series (pull-up), NMOS in parallel (pull-down)
circuit.MOSFET('MP1', 'mid', 'A', 'vdd', 'vdd', model='PMOS')   # series
circuit.MOSFET('MP2', 'out', 'B', 'mid', 'vdd', model='PMOS')   # series
circuit.MOSFET('MN1', 'out', 'A', circuit.gnd, circuit.gnd, model='NMOS')  # parallel
circuit.MOSFET('MN2', 'out', 'B', circuit.gnd, circuit.gnd, model='NMOS')  # parallel
```

#### Schmitt Trigger (with hysteresis) — 6 transistors
```python
# Standard CMOS Schmitt trigger with positive feedback transistors
circuit.MOSFET('MN1', 'out', 'in_', circuit.gnd, circuit.gnd, model='NMOS', w=10e-6, l=1e-6)
circuit.MOSFET('MN2', circuit.gnd, 'out', circuit.gnd, circuit.gnd, model='NMOS', w=5e-6, l=1e-6)  # feedback
circuit.MOSFET('MP1', 'out', 'in_', 'vdd', 'vdd', model='PMOS', w=20e-6, l=1e-6)
circuit.MOSFET('MP2', 'vdd', 'out', 'vdd', 'vdd', model='PMOS', w=10e-6, l=1e-6)  # feedback
```

---

### 4B — Sequential Digital Circuits

#### D Flip-Flop — using transmission gates
```python
from PySpice.Spice.Netlist import Circuit, SubCircuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

class DFlipFlop(SubCircuit):
    """Master-slave D flip-flop using transmission gates. Nodes: D, CLK, Q, QBAR, VDD, GND"""
    __nodes__ = ('D', 'CLK', 'CLKBAR', 'Q', 'QBAR', 'VDD', 'GND')

    def __init__(self):
        SubCircuit.__init__(self, 'DFF', *self.__nodes__)
        # Master latch (transparent when CLK=0)
        # Transmission gate TG1: CLK=0 passes D to m1
        self.MOSFET('MN_TG1', 'm1', 'D', 'CLK', 'GND', model='NMOS', w=10e-6, l=1e-6)
        self.MOSFET('MP_TG1', 'm1', 'D', 'CLKBAR', 'VDD', model='PMOS', w=20e-6, l=1e-6)
        # Master inverter pair (cross-coupled for storage)
        self.MOSFET('MNm1', 'm2', 'm1', 'GND', 'GND', model='NMOS', w=10e-6, l=1e-6)
        self.MOSFET('MPm1', 'm2', 'm1', 'VDD', 'VDD', model='PMOS', w=20e-6, l=1e-6)
        self.MOSFET('MNm2', 'm1_fb', 'm2', 'GND', 'GND', model='NMOS', w=5e-6, l=1e-6)
        self.MOSFET('MPm2', 'm1_fb', 'm2', 'VDD', 'VDD', model='PMOS', w=10e-6, l=1e-6)
        # Feedback TG (CLK=1 closes feedback)
        self.MOSFET('MN_FB', 'm1', 'm1_fb', 'CLKBAR', 'GND', model='NMOS', w=5e-6, l=1e-6)
        self.MOSFET('MP_FB', 'm1', 'm1_fb', 'CLK', 'VDD', model='PMOS', w=10e-6, l=1e-6)
        # Slave latch (transparent when CLK=1)
        self.MOSFET('MN_TG2', 's1', 'm2', 'CLKBAR', 'GND', model='NMOS', w=10e-6, l=1e-6)
        self.MOSFET('MP_TG2', 's1', 'm2', 'CLK', 'VDD', model='PMOS', w=20e-6, l=1e-6)
        self.MOSFET('MNs1', 'Q', 's1', 'GND', 'GND', model='NMOS', w=10e-6, l=1e-6)
        self.MOSFET('MPs1', 'Q', 's1', 'VDD', 'VDD', model='PMOS', w=20e-6, l=1e-6)
        self.MOSFET('MNs2', 'QBAR', 'Q', 'GND', 'GND', model='NMOS', w=10e-6, l=1e-6)
        self.MOSFET('MPs2', 'QBAR', 'Q', 'VDD', 'VDD', model='PMOS', w=20e-6, l=1e-6)
```

---

### 4C — Basic Analog Building Blocks

#### Simple Current Mirror (NMOS)
```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

circuit = Circuit('NMOS Current Mirror')
circuit.V('dd', 'vdd', circuit.gnd, 5@u_V)
# Reference current: Iref = (Vdd - Vgs_ref) / R_ref ≈ 100uA
circuit.I('ref', 'vdd', 'ref_drain', 100@u_uA)  # reference current source

# Reference transistor (diode-connected: gate tied to drain)
circuit.MOSFET('M_ref', 'ref_drain', 'ref_drain', circuit.gnd, circuit.gnd,
               model='NMOS', w=20e-6, l=4e-6)
# Mirror transistor (gate tied to ref gate = ref_drain)
circuit.MOSFET('M_out', 'out', 'ref_drain', circuit.gnd, circuit.gnd,
               model='NMOS', w=20e-6, l=4e-6)
# Load for output
circuit.R('load', 'vdd', 'out', 20@u_kΩ)

circuit.model('NMOS', 'nmos', level=1, kp=120e-6, vto=0.7, lambda_=0.02,
              w=20e-6, l=4e-6)

# DC sweep to verify mirror output current vs Vout
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.dc(Vdd=slice(0, 5, 0.1))
# Also do operating point
op = simulator.operating_point()
plt.figure(figsize=(8, 5))
plt.plot(np.array(analysis['vdd']), np.array(analysis['out']), 'b-')
plt.xlabel('Vdd (V)'); plt.ylabel('Output Node Voltage (V)')
plt.title('Current Mirror DC Sweep'); plt.grid(True)
plt.show()
```

#### Differential Pair with Tail Current Source
```python
circuit = Circuit('Differential Pair')
circuit.V('dd', 'vdd', circuit.gnd, 5@u_V)
circuit.V('ss', circuit.gnd, 'vss', 5@u_V)  # negative supply

# Tail current source: NMOS with gate bias
circuit.V('bias', 'vbias', circuit.gnd, 1.5@u_V)
circuit.MOSFET('M_tail', 'tail', 'vbias', 'vss', 'vss', model='NMOS', w=40e-6, l=4e-6)

# Differential pair transistors
circuit.MOSFET('M1', 'vout_p', 'vip', 'tail', 'vss', model='NMOS', w=20e-6, l=2e-6)
circuit.MOSFET('M2', 'vout_n', 'vin_', 'tail', 'vss', model='NMOS', w=20e-6, l=2e-6)

# Resistive loads
circuit.R('RD1', 'vdd', 'vout_p', 10@u_kΩ)
circuit.R('RD2', 'vdd', 'vout_n', 10@u_kΩ)

# Differential input signals
circuit.SinusoidalVoltageSource('vip', 'vip', circuit.gnd, amplitude=100@u_mV, frequency=100@u_kHz)
circuit.SinusoidalVoltageSource('vin', 'vin_', circuit.gnd, amplitude=100@u_mV, frequency=100@u_kHz,
                                 phase=180)  # 180° phase shift

circuit.model('NMOS', 'nmos', level=1, kp=120e-6, vto=0.7, lambda_=0.02)
circuit.model('PMOS', 'pmos', level=1, kp=60e-6, vto=-0.7, lambda_=0.02)

simulator = circuit.simulator(temperature=25, nominal_temperature=25)
# AC analysis for gain and bandwidth
analysis = simulator.ac(start_frequency=1@u_Hz, stop_frequency=1@u_GHz,
                        number_of_points=100, variation='dec')

plt.figure(figsize=(10, 6))
# Differential gain = Vout_p - Vout_n (approx as single-ended here)
gain_db = 20 * np.log10(np.abs(np.array(analysis['vout_p'])))
plt.semilogx(np.array(analysis.frequency), gain_db, 'b-')
plt.xlabel('Frequency (Hz)'); plt.ylabel('Gain (dB)')
plt.title('Differential Pair AC Response'); plt.grid(True)
plt.show()
```

#### Cascode Current Mirror (for high output resistance)
```python
# Cascode improves output resistance: Rout ≈ gm*ro²
# Regular mirror: M_ref (diode) + M_out (mirror)
# Cascode mirror: adds MN_cas_ref and MN_cas_out above
circuit.MOSFET('M_ref',     'vb',    'vb',    circuit.gnd, circuit.gnd, model='NMOS', w=20e-6, l=4e-6)
circuit.MOSFET('M_out',     'vout_b','vb',    circuit.gnd, circuit.gnd, model='NMOS', w=20e-6, l=4e-6)
circuit.MOSFET('M_cas_ref', 'iref',  'vcas',  'vb',        circuit.gnd, model='NMOS', w=20e-6, l=4e-6)
circuit.MOSFET('M_cas_out', 'out',   'vcas',  'vout_b',    circuit.gnd, model='NMOS', w=20e-6, l=4e-6)
# vcas bias = ~2*Vt above gnd for proper cascode operation
circuit.V('cas_bias', 'vcas', circuit.gnd, 1.5@u_V)
```

#### Source Follower (Voltage Follower / Common Drain)
```python
# Unity gain buffer, high Rin, moderate Rout ≈ 1/gm
circuit.MOSFET('M1', 'out', 'in_', 'out', circuit.gnd, model='NMOS', w=50e-6, l=1e-6)
# Bias current source at output
circuit.I('bias', 'out', circuit.gnd, 1@u_mA)
```

---

### 4D — Amplifiers

#### Two-Stage CMOS Op-Amp (Miller Compensated)
```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

circuit = Circuit('Two-Stage Op-Amp')
circuit.V('dd',  'vdd', circuit.gnd, 5@u_V)
circuit.V('ss',  circuit.gnd, 'vss', 5@u_V)

# Stage 1: Differential pair with current mirror load
# Tail current source
circuit.V('vbias', 'vbias', circuit.gnd, -3@u_V)
circuit.MOSFET('M_tail', 'tail', 'vbias', 'vss', 'vss', model='NMOS', w=40e-6, l=4e-6)

# Input differential pair (NMOS)
circuit.MOSFET('M1', 'd1', 'vip', 'tail', 'vss', model='NMOS', w=20e-6, l=2e-6)
circuit.MOSFET('M2', 'd2', 'vin_', 'tail', 'vss', model='NMOS', w=20e-6, l=2e-6)

# PMOS current mirror load
circuit.MOSFET('M3', 'd1', 'd1', 'vdd', 'vdd', model='PMOS', w=40e-6, l=4e-6)  # diode-conn
circuit.MOSFET('M4', 'vout1', 'd1', 'vdd', 'vdd', model='PMOS', w=40e-6, l=4e-6)

# Stage 2: Common source (NMOS gain stage)
circuit.MOSFET('M5', 'vout', 'vout1', 'vss', 'vss', model='NMOS', w=80e-6, l=2e-6)
# PMOS load for stage 2
circuit.MOSFET('M6', 'vout', 'vbias2', 'vdd', 'vdd', model='PMOS', w=20e-6, l=4e-6)
circuit.V('vbias2', 'vbias2', circuit.gnd, 3@u_V)

# Miller compensation capacitor (frequency stability)
circuit.C('Cm', 'vout1', 'vout', 2@u_pF)
# Nulling resistor (to push RHP zero to infinity)
circuit.R('Rm', 'vout1', 'vout1_r', 5@u_kΩ)
circuit.C('Cm2', 'vout1_r', 'vout', 2@u_pF)

# Input: small-signal AC at non-inverting input, inverting grounded (open-loop test)
circuit.V('vip_src', 'vip', circuit.gnd, 'DC 0 AC 1')
circuit.V('vin_src', 'vin_', circuit.gnd, 0@u_V)

circuit.model('NMOS', 'nmos', level=1, kp=120e-6, vto=0.7, lambda_=0.02)
circuit.model('PMOS', 'pmos', level=1, kp=60e-6, vto=-0.7, lambda_=0.02)

simulator = circuit.simulator(temperature=25, nominal_temperature=25)
simulator.options(reltol=1e-5, abstol=1e-12)
analysis = simulator.ac(start_frequency=1@u_Hz, stop_frequency=1@u_GHz,
                        number_of_points=100, variation='dec')

vout = np.array(analysis['vout'])
gain_db = 20 * np.log10(np.abs(vout))
phase_deg = np.angle(vout, deg=True)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
ax1.semilogx(np.array(analysis.frequency), gain_db, 'b-')
ax1.set_ylabel('Gain (dB)'); ax1.grid(True); ax1.set_title('Op-Amp Open-Loop Bode Plot')
ax2.semilogx(np.array(analysis.frequency), phase_deg, 'r-')
ax2.set_ylabel('Phase (°)'); ax2.set_xlabel('Frequency (Hz)'); ax2.grid(True)
plt.tight_layout()
plt.show()
```

#### OTA (Operational Transconductance Amplifier)
```python
# OTA: current output proportional to differential input voltage
# Iout = Gm * (Vip - Vin)
# Structure: diff pair + current mirror load (no output stage)
# Same as Stage 1 of two-stage op-amp, output taken as current

# Key parameter: Gm = sqrt(2 * kp * (W/L) * Ibias)
# For NMOS: kp=120uA/V², W/L=20, Ibias=100uA → Gm ≈ 693 uA/V

# Typical OTA topology — 5-transistor OTA:
circuit.MOSFET('M1', 'd1', 'vip', 'tail', 'vss', model='NMOS', w=20e-6, l=2e-6)
circuit.MOSFET('M2', 'iout', 'vin_', 'tail', 'vss', model='NMOS', w=20e-6, l=2e-6)
circuit.MOSFET('M3', 'd1', 'd1', 'vdd', 'vdd', model='PMOS', w=40e-6, l=4e-6)  # mirror ref
circuit.MOSFET('M4', 'iout', 'd1', 'vdd', 'vdd', model='PMOS', w=40e-6, l=4e-6)  # mirror
circuit.MOSFET('M5', 'tail', 'vbias', 'vss', 'vss', model='NMOS', w=40e-6, l=4e-6)
```

#### Low Noise Amplifier (LNA) — Common Source with Inductive Degeneration
```python
# LNA topology: CS with source inductor Ls for noise matching, Lg for input match
# Typically used at RF (1-6 GHz range in ngspice AC analysis)
circuit.MOSFET('M1', 'vout', 'vg', 'vs', circuit.gnd, model='NMOS_RF', w=100e-6, l=0.18e-6)

# Gate inductor (for input impedance match)
circuit.L('Lg', 'vin_rf', 'vg', 2@u_nH)
# Source inductor (degeneration, noise match)
circuit.L('Ls', 'vs', circuit.gnd, 0.5@u_nH)
# Drain inductor (resonant load at fRF)
circuit.L('Ld', 'vdd', 'vout', 10@u_nH)
# Bypass caps
circuit.C('Cbyp', 'vdd', circuit.gnd, 10@u_pF)

# RF MOSFET model (higher fT)
circuit.model('NMOS_RF', 'nmos', level=1, kp=200e-6, vto=0.5, lambda_=0.05,
              w=100e-6, l=0.18e-6, cbd=50e-15, cbs=50e-15, cgd=10e-15, cgs=200e-15)
```

#### Transimpedance Amplifier (TIA) — for photodiode readout
```python
# TIA: converts current input to voltage output
# Vout = -Iin * Rf  (in feedback configuration)
# Uses an op-amp with resistive feedback

# Simple CMOS TIA using inverter as amplifier
circuit.MOSFET('MN_tia', 'vout', 'vout', circuit.gnd, circuit.gnd, model='NMOS', w=10e-6, l=1e-6)
circuit.MOSFET('MP_tia', 'vout', 'vout', 'vdd', 'vdd', model='PMOS', w=20e-6, l=1e-6)

# Feedback resistor (transimpedance = Rf)
circuit.R('Rf', 'vout', 'iin_node', 10@u_kΩ)
# Feedback capacitor (for stability)
circuit.C('Cf', 'vout', 'iin_node', 100@u_fF)

# Input current source (photodiode model)
circuit.I('Iin', 'iin_node', circuit.gnd, 1@u_uA)
```

---

### 4E — References and Biasing

#### Diode-Connected MOSFET Voltage Reference
```python
# Stacked diode-connected NMOS to generate reference voltage
# Vref = N * Vgs where Vgs ≈ Vt + sqrt(2*ID/(kp*(W/L)))
circuit.I('ref', 'vdd', 'vref', 100@u_uA)
circuit.MOSFET('M1', 'vref', 'vref', 'vref2', circuit.gnd, model='NMOS', w=10e-6, l=4e-6)
circuit.MOSFET('M2', 'vref2', 'vref2', circuit.gnd, circuit.gnd, model='NMOS', w=10e-6, l=4e-6)
# Vref ≈ 2 * Vgs for two stacked devices
```

#### Constant-Gm Bias Circuit
```python
# Bias circuit where Gm is set by external resistor Rext
# Gm = 1/Rext (process-independent if matched devices)
# Rext sets the reference: Ibias = 1/(Gm*Rext²) approximately
circuit.R('Rext', 'vbias_p', circuit.gnd, 10@u_kΩ)
circuit.MOSFET('M_p', 'vbias_p', 'vbias_p', 'vdd', 'vdd', model='PMOS', w=20e-6, l=4e-6)
circuit.MOSFET('M_n', 'vbias_n', 'vbias_n', circuit.gnd, circuit.gnd, model='NMOS', w=10e-6, l=4e-6)
# Cross-coupled for startup and self-biasing
```

#### Beta-Multiplier Reference (supply-independent biasing)
```python
# Ibias = (1/R) * ln(K) / sqrt(kp*(W/L))  — supply independent
# K = mirror ratio between M1 and M2
K = 4  # ratio

# Use two matched PMOS current mirrors with NMOS in series
circuit.MOSFET('MP1', 'v1', 'vbp', 'vdd', 'vdd', model='PMOS', w=20e-6, l=4e-6)  # 1x
circuit.MOSFET('MP2', 'v2', 'vbp', 'vdd', 'vdd', model='PMOS', w=20e-6*K, l=4e-6)  # Kx
circuit.MOSFET('MN1', 'v1', 'v1', circuit.gnd, circuit.gnd, model='NMOS', w=10e-6, l=4e-6)
circuit.MOSFET('MN2', 'v2', 'v1', 'rs', circuit.gnd, model='NMOS', w=10e-6, l=4e-6)
circuit.R('Rs', 'rs', circuit.gnd, 5@u_kΩ)  # sets bias current
```

---

### 4F — Oscillators

#### Ring Oscillator (3-stage)
```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

circuit = Circuit('Ring Oscillator')
circuit.V('dd', 'vdd', circuit.gnd, 5@u_V)

# 3 inverter stages in a loop
# Stage 1
circuit.MOSFET('MN1', 'v1', 'v3', circuit.gnd, circuit.gnd, model='NMOS', w=10e-6, l=1e-6)
circuit.MOSFET('MP1', 'v1', 'v3', 'vdd', 'vdd', model='PMOS', w=20e-6, l=1e-6)
# Stage 2
circuit.MOSFET('MN2', 'v2', 'v1', circuit.gnd, circuit.gnd, model='NMOS', w=10e-6, l=1e-6)
circuit.MOSFET('MP2', 'v2', 'v1', 'vdd', 'vdd', model='PMOS', w=20e-6, l=1e-6)
# Stage 3
circuit.MOSFET('MN3', 'v3', 'v2', circuit.gnd, circuit.gnd, model='NMOS', w=10e-6, l=1e-6)
circuit.MOSFET('MP3', 'v3', 'v2', 'vdd', 'vdd', model='PMOS', w=20e-6, l=1e-6)

# Parasitic capacitances to help oscillation start
circuit.C('C1', 'v1', circuit.gnd, 1@u_fF)
circuit.C('C2', 'v2', circuit.gnd, 1@u_fF)
circuit.C('C3', 'v3', circuit.gnd, 1@u_fF)

circuit.model('NMOS', 'nmos', level=1, kp=120e-6, vto=0.7, lambda_=0.02, w=10e-6, l=1e-6)
circuit.model('PMOS', 'pmos', level=1, kp=60e-6, vto=-0.7, lambda_=0.02, w=20e-6, l=1e-6)

simulator = circuit.simulator(temperature=25, nominal_temperature=25)
simulator.options(reltol=1e-5, abstol=1e-12, vntol=1e-6, method='gear')
# Use UIC (use initial conditions) and set IC to break symmetry
analysis = simulator.transient(step_time=0.1@u_ns, end_time=10@u_ns,
                               use_initial_condition=True)

plt.figure(figsize=(10, 5))
plt.plot(np.array(analysis.time)*1e9, np.array(analysis['v1']), label='Stage 1')
plt.plot(np.array(analysis.time)*1e9, np.array(analysis['v2']), label='Stage 2')
plt.plot(np.array(analysis.time)*1e9, np.array(analysis['v3']), label='Stage 3')
plt.xlabel('Time (ns)'); plt.ylabel('Voltage (V)')
plt.title('3-Stage Ring Oscillator'); plt.legend(); plt.grid(True)
plt.show()
```

#### Voltage-Controlled Oscillator (VCO) — Current-Starved Ring
```python
# VCO: control voltage adjusts bias current → changes oscillation frequency
# Higher Vctrl → more current → faster switching → higher frequency

# Control voltage
circuit.V('vctrl', 'vctrl', circuit.gnd, 2.5@u_V)  # control (0 to Vdd)

# Current starving: top PMOS and bottom NMOS set drive current
# For each inverter stage:
circuit.MOSFET('MP_cs1', 'vdd_cs1', 'vctrl', 'vdd', 'vdd', model='PMOS', w=10e-6, l=2e-6)
circuit.MOSFET('MN_inv1', 'v1', 'v3', 'vss_cs1', circuit.gnd, model='NMOS', w=10e-6, l=1e-6)
circuit.MOSFET('MP_inv1', 'v1', 'v3', 'vdd_cs1', 'vdd', model='PMOS', w=20e-6, l=1e-6)
circuit.MOSFET('MN_cs1', 'vss_cs1', 'vctrl', circuit.gnd, circuit.gnd, model='NMOS', w=10e-6, l=2e-6)
# Repeat for stages 2 and 3 with nodes v2, v3
```

#### LC Oscillator (Colpitts) — for RF frequency generation
```python
# Colpitts oscillator: LC tank with capacitive voltage divider
# Oscillation frequency: f = 1 / (2π * sqrt(L * Ceq))
# where Ceq = C1*C2/(C1+C2)

circuit.L('Ltank', 'vout', 'vdd', 100@u_nH)
circuit.C('C1', 'vout', 'vtap', 5@u_pF)   # capacitive divider top
circuit.C('C2', 'vtap', circuit.gnd, 5@u_pF)  # capacitive divider bottom
# NMOS amplifier
circuit.MOSFET('M1', 'vout', 'vtap', circuit.gnd, circuit.gnd, model='NMOS', w=50e-6, l=1e-6)
circuit.R('Rbias', 'vdd', 'vtap', 50@u_kΩ)
# f ≈ 1/(2π*sqrt(100nH * 2.5pF)) ≈ 318 MHz
```

---

### 4G — Power and Regulation

#### Low Dropout Regulator (LDO)
```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

circuit = Circuit('LDO Regulator')
circuit.V('in_', 'vin', circuit.gnd, 5@u_V)

# Error amplifier (simplified as VCVS for behavioral model)
# In real implementation, use diff pair with current mirror load
# Reference voltage
circuit.V('vref', 'vref', circuit.gnd, 1.2@u_V)

# Feedback resistors (set output voltage: Vout = Vref*(1 + R1/R2))
R1 = 30e3; R2 = 20e3  # Vout = 1.2*(1+30/20) = 3.0V
circuit.R('R1', 'vout', 'vfb', R1@u_Ω)
circuit.R('R2', 'vfb', circuit.gnd, R2@u_Ω)

# Error amp: Verr = A*(Vref - Vfb), A = open loop gain
circuit.VCVS('Eamp', 'vgate', circuit.gnd, 'vref', 'vfb', voltage_gain=1000)

# PMOS pass transistor
circuit.MOSFET('M_pass', 'vout', 'vgate', 'vin', 'vin', model='PMOS', w=500e-6, l=1e-6)

# Output capacitor and load
circuit.C('Cout', 'vout', circuit.gnd, 10@u_uF, ic=3@u_V)
circuit.R('Rload', 'vout', circuit.gnd, 30@u_Ω)  # 100mA load at 3V

circuit.model('PMOS', 'pmos', level=1, kp=60e-6, vto=-0.7, lambda_=0.02, w=500e-6, l=1e-6)

simulator = circuit.simulator(temperature=25, nominal_temperature=25)
simulator.options(reltol=1e-4, abstol=1e-9)
analysis = simulator.transient(step_time=1@u_us, end_time=1@u_ms,
                               use_initial_condition=True)

plt.figure(figsize=(10, 5))
plt.plot(np.array(analysis.time)*1e3, np.array(analysis['vout']), 'g-', label='Vout')
plt.axhline(y=3.0, color='r', linestyle='--', label='Target 3.0V')
plt.xlabel('Time (ms)'); plt.ylabel('Output Voltage (V)')
plt.title('LDO Regulator Startup'); plt.legend(); plt.grid(True)
plt.show()
```

#### Charge Pump (Dickson)
```python
# Dickson charge pump: generates higher voltage from lower supply
# N stages: Vout_ideal = Vdd*(N+1) - (N+2)*Vt
# Use MOSFET switches clocked alternately

circuit.V('dd', 'vdd', circuit.gnd, 3.3@u_V)
circuit.PulseVoltageSource('clk1', 'clk1', circuit.gnd,
    initial_value=0@u_V, pulsed_value=3.3@u_V,
    rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=10@u_ns, period=20@u_ns)
circuit.PulseVoltageSource('clk2', 'clk2', circuit.gnd,
    initial_value=3.3@u_V, pulsed_value=0@u_V,  # inverted
    rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=10@u_ns, period=20@u_ns)

# Stage 1
circuit.C('C1', 'clk1', 'v1', 10@u_pF)
circuit.MOSFET('M1', 'v1', 'v1', 'vdd', 'vdd', model='PMOS', w=20e-6, l=1e-6)  # diode-conn
# Stage 2
circuit.C('C2', 'clk2', 'v2', 10@u_pF)
circuit.MOSFET('M2', 'v2', 'v2', 'v1', 'vdd', model='PMOS', w=20e-6, l=1e-6)
# Output capacitor
circuit.C('Cout', 'vout_cp', circuit.gnd, 10@u_pF)
circuit.MOSFET('M3', 'vout_cp', 'vout_cp', 'v2', 'vdd', model='PMOS', w=20e-6, l=1e-6)
circuit.R('Rload', 'vout_cp', circuit.gnd, 100@u_kΩ)
```

---

### 4H — Mixed-Signal Circuits

#### Sample and Hold Circuit
```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

circuit = Circuit('Sample and Hold')
circuit.V('dd', 'vdd', circuit.gnd, 5@u_V)

# Sinusoidal input signal
circuit.SinusoidalVoltageSource('in_', 'vin', circuit.gnd,
    amplitude=2@u_V, frequency=100@u_kHz)

# Clock for sampling (1MHz sampling → 10x oversampling for 100kHz)
circuit.PulseVoltageSource('clk', 'clk', circuit.gnd,
    initial_value=0@u_V, pulsed_value=5@u_V,
    rise_time=1@u_ns, fall_time=1@u_ns,
    pulse_width=400@u_ns, period=1@u_us)

# Transmission gate switch (NMOS + PMOS in parallel for rail-to-rail)
circuit.MOSFET('MN_sw', 'vsamp', 'clk', 'vin', circuit.gnd, model='NMOS', w=20e-6, l=1e-6)
# PMOS needs complementary clock — use VCVS to invert
circuit.VCVS('Einv', 'clkbar', circuit.gnd, circuit.gnd, 'clk', voltage_gain=-1)
circuit.V('clkbar_offset', 'clkbar', 'clkbar_shifted', 5@u_V)  # add Vdd offset
circuit.MOSFET('MP_sw', 'vsamp', 'clkbar_shifted', 'vin', 'vdd', model='PMOS', w=20e-6, l=1e-6)

# Hold capacitor
circuit.C('Ch', 'vsamp', circuit.gnd, 1@u_pF)

circuit.model('NMOS', 'nmos', level=1, kp=120e-6, vto=0.7, lambda_=0.02, w=20e-6, l=1e-6)
circuit.model('PMOS', 'pmos', level=1, kp=60e-6, vto=-0.7, lambda_=0.02, w=20e-6, l=1e-6)

simulator = circuit.simulator(temperature=25, nominal_temperature=25)
simulator.options(reltol=1e-4, abstol=1e-12)
analysis = simulator.transient(step_time=5@u_ns, end_time=20@u_us,
                               use_initial_condition=True)

fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
t_us = np.array(analysis.time) * 1e6
axes[0].plot(t_us, np.array(analysis['vin']), 'b-', label='Input')
axes[0].set_ylabel('Vin (V)'); axes[0].legend(); axes[0].grid(True)
axes[1].plot(t_us, np.array(analysis['clk']), 'g-', label='Clock')
axes[1].set_ylabel('CLK (V)'); axes[1].legend(); axes[1].grid(True)
axes[2].plot(t_us, np.array(analysis['vsamp']), 'r-', label='Sampled/Held')
axes[2].set_ylabel('Vsamp (V)'); axes[2].set_xlabel('Time (us)'); axes[2].legend(); axes[2].grid(True)
plt.title('Sample and Hold Circuit'); plt.tight_layout(); plt.show()
```

#### Comparator (Simple)
```python
# Fast comparator using a differential pair with positive feedback for speed
# Non-inverting: Vip, Inverting: Vin → output goes rail-to-rail

# Pre-amp stage (diff pair)
circuit.MOSFET('M1', 'vp', 'vip', 'tail', 'vss', model='NMOS', w=20e-6, l=2e-6)
circuit.MOSFET('M2', 'vn', 'vin_', 'tail', 'vss', model='NMOS', w=20e-6, l=2e-6)
circuit.MOSFET('M_t', 'tail', 'vbias', 'vss', 'vss', model='NMOS', w=40e-6, l=4e-6)
circuit.MOSFET('M3', 'vp', 'vp', 'vdd', 'vdd', model='PMOS', w=40e-6, l=4e-6)
circuit.MOSFET('M4', 'vn', 'vp', 'vdd', 'vdd', model='PMOS', w=40e-6, l=4e-6)

# Output inverter for rail-to-rail output
circuit.MOSFET('MN_out', 'cout', 'vn', circuit.gnd, circuit.gnd, model='NMOS', w=20e-6, l=1e-6)
circuit.MOSFET('MP_out', 'cout', 'vn', 'vdd', 'vdd', model='PMOS', w=40e-6, l=1e-6)
```

#### R-2R DAC (3-bit example)
```python
# R-2R ladder DAC: digital bits control switches, generates analog output
# Vout = Vref * (B2/2 + B1/4 + B0/8)

R = 10e3  # base resistor value
# Ladder network
circuit.R('R0_2R', 'b0', circuit.gnd, 2*R@u_Ω)
circuit.R('R0_R', 'b0', 'b1', R@u_Ω)
circuit.R('R1_2R', 'b1', circuit.gnd, 2*R@u_Ω)
circuit.R('R1_R', 'b1', 'b2', R@u_Ω)
circuit.R('R2_2R', 'b2', circuit.gnd, 2*R@u_Ω)
circuit.R('R2_R', 'b2', 'vout_dac', R@u_Ω)
circuit.R('Rterm', 'vout_dac', circuit.gnd, 2*R@u_Ω)

# Digital input switches (simplified as voltage sources 0V or Vref)
circuit.V('b0_sw', 'b0_in', circuit.gnd, 5@u_V)  # LSB = 1
circuit.V('b1_sw', 'b1_in', circuit.gnd, 0@u_V)  # bit 1 = 0
circuit.V('b2_sw', 'b2_in', circuit.gnd, 5@u_V)  # MSB = 1  → binary 101 = 5 → Vout=5*5/8=3.125V
```

---

### 4I — RF Circuits

#### Gilbert Cell Mixer
```python
# Gilbert cell: core RF mixer for down/up conversion
# LO input switches the RF current between two paths
# Output: IF = RF × LO (multiplication)

# RF differential pair (input transistors)
circuit.MOSFET('M_RF1', 'vrf_p', 'vrf', 'tail_rf', 'vss', model='NMOS', w=20e-6, l=0.5e-6)
circuit.MOSFET('M_RF2', 'vrf_n', circuit.gnd, 'tail_rf', 'vss', model='NMOS', w=20e-6, l=0.5e-6)
circuit.MOSFET('M_tail_rf', 'tail_rf', 'vbias', 'vss', 'vss', model='NMOS', w=40e-6, l=2e-6)

# LO switching quad (cross-coupled differential pairs)
circuit.MOSFET('M_LO1', 'vif_p', 'vlo_p', 'vrf_p', 'vss', model='NMOS', w=10e-6, l=0.5e-6)
circuit.MOSFET('M_LO2', 'vif_n', 'vlo_n', 'vrf_p', 'vss', model='NMOS', w=10e-6, l=0.5e-6)
circuit.MOSFET('M_LO3', 'vif_n', 'vlo_p', 'vrf_n', 'vss', model='NMOS', w=10e-6, l=0.5e-6)
circuit.MOSFET('M_LO4', 'vif_p', 'vlo_n', 'vrf_n', 'vss', model='NMOS', w=10e-6, l=0.5e-6)

# Load resistors (or current mirror load for active mixer)
circuit.R('RL1', 'vdd', 'vif_p', 2@u_kΩ)
circuit.R('RL2', 'vdd', 'vif_n', 2@u_kΩ)

# LO signal (local oscillator — high amplitude for good switching)
circuit.SinusoidalVoltageSource('vlo_p', 'vlo_p', circuit.gnd, amplitude=500@u_mV, frequency=2.4@u_GHz)
circuit.SinusoidalVoltageSource('vlo_n', 'vlo_n', circuit.gnd, amplitude=500@u_mV, frequency=2.4@u_GHz, phase=180)

# RF signal (smaller amplitude)
circuit.SinusoidalVoltageSource('vrf', 'vrf', circuit.gnd, amplitude=10@u_mV, frequency=2.5@u_GHz)
```

#### Phase Detector (XOR-based)
```python
# XOR phase detector: output voltage proportional to phase difference
# Use CMOS XOR gate with both inputs being the signals to compare

# Signal inputs
circuit.PulseVoltageSource('sig1', 'vsig1', circuit.gnd,
    initial_value=0@u_V, pulsed_value=5@u_V,
    rise_time=1@u_ns, fall_time=1@u_ns, pulse_width=50@u_ns, period=100@u_ns)
circuit.PulseVoltageSource('sig2', 'vsig2', circuit.gnd,
    initial_value=0@u_V, pulsed_value=5@u_V,
    rise_time=1@u_ns, fall_time=1@u_ns,
    pulse_width=50@u_ns, period=100@u_ns, delay_time=10@u_ns)  # 10ns phase offset

# XOR implementation
circuit.MOSFET('MN_xor1', 'int1', 'vsig1', circuit.gnd, circuit.gnd, model='NMOS', w=10e-6, l=1e-6)
circuit.MOSFET('MP_xor1', 'int1', 'vsig1', 'vdd', 'vdd', model='PMOS', w=20e-6, l=1e-6)
# (Full 8-transistor XOR gate needed for complete implementation)

# Low-pass filter on output gives DC proportional to phase error
circuit.R('Rlpf', 'vpd_out', 'vpd_filt', 10@u_kΩ)
circuit.C('Clpf', 'vpd_filt', circuit.gnd, 100@u_pF)
```

---

### 4J — Filters

#### Active Low-Pass Filter (using OTA)
```python
# First-order active LPF: f_-3dB = Gm / (2π * C)
# For Gm=1mA/V and C=10pF: f_-3dB ≈ 15.9 MHz

# OTA transconductor
Gm = 1e-3  # 1 mA/V
circuit.VCCS('Gm1', 'vout_lp', circuit.gnd, 'vin_lp', circuit.gnd, transconductance=Gm)
circuit.C('Cint', 'vout_lp', circuit.gnd, 10@u_pF)
circuit.R('Rout', 'vout_lp', circuit.gnd, 1@u_MΩ)  # high resistance load

# Input signal source
circuit.SinusoidalVoltageSource('vin_src', 'vin_lp', circuit.gnd,
    amplitude=1@u_V, frequency=1@u_MHz)
```

#### Sallen-Key Low-Pass Filter (2nd order)
```python
# Sallen-Key: 2nd order LPF with unity-gain buffer
# f_0 = 1/(2π*sqrt(R1*R2*C1*C2)), Q = sqrt(R1*R2*C1*C2)/(C2*(R1+R2))
import math

R1_val = 10e3; R2_val = 10e3
C1_val = 1e-9; C2_val = 1e-9
f0 = 1/(2*math.pi*math.sqrt(R1_val*R2_val*C1_val*C2_val))  # ~15.9 kHz

circuit.R('R1', 'vin_sk', 'vmid', R1_val@u_Ω)
circuit.R('R2', 'vmid', 'vout_sk', R2_val@u_Ω)
circuit.C('C1', 'vmid', circuit.gnd, C1_val@u_F)
circuit.C('C2', 'vout_sk', circuit.gnd, C2_val@u_F)
# Unity gain buffer (VCVS approximation)
circuit.VCVS('Ebuf', 'vbuf_out', circuit.gnd, 'vout_sk', circuit.gnd, voltage_gain=1)
# Feedback from buffer output to vout_sk (closed loop)
```

#### Switched-Capacitor Resistor (SC equivalent)
```python
# Switched capacitor emulates resistor: Req = 1/(f_clk * C)
# For f_clk=1MHz and C=1pF: Req = 1MΩ

# Two-phase non-overlapping clocks
circuit.PulseVoltageSource('ph1', 'phi1', circuit.gnd,
    initial_value=5@u_V, pulsed_value=0@u_V,
    rise_time=0.5@u_ns, fall_time=0.5@u_ns, pulse_width=500@u_ns, period=1@u_us)
circuit.PulseVoltageSource('ph2', 'phi2', circuit.gnd,
    initial_value=0@u_V, pulsed_value=5@u_V,
    rise_time=0.5@u_ns, fall_time=0.5@u_ns, pulse_width=500@u_ns, period=1@u_us)

# SC resistor: S1 (phi1) → C_sc → S2 (phi2)
circuit.MOSFET('S1', 'vsc', 'phi1', 'vin_sc', circuit.gnd, model='NMOS', w=5e-6, l=1e-6)
circuit.C('C_sc', 'vsc', circuit.gnd, 1@u_pF)
circuit.MOSFET('S2', 'vout_sc', 'phi2', 'vsc', circuit.gnd, model='NMOS', w=5e-6, l=1e-6)
```

---

## SECTION 5: Analysis Selection Guide

| Circuit Type | Recommended Analysis | Notes |
|---|---|---|
| CMOS digital gates | Transient | Clock/pulse inputs; measure propagation delay, rise/fall times |
| Sequential digital (FF, counter) | Transient | Long simulation for multiple clock cycles |
| Ring oscillator | Transient with UIC | Use `method='gear'`; set IC to break symmetry |
| LC oscillator | Transient | May need long sim to reach steady state |
| Common-source amp | DC op-pt + AC | Find bias, then AC for gain/BW |
| Differential pair | DC op-pt + AC | AC gives Gm, gain, CMRR |
| Two-stage op-amp | DC op-pt + AC | Bode plot for GBW and phase margin |
| LNA | AC + Noise | S-parameters via AC; noise figure from noise analysis |
| Filters | AC (Bode) | Logarithmic frequency sweep for filter response |
| Sample and hold | Transient | Show sampling, hold, droop |
| Comparator | Transient | Ramp input to show threshold and hysteresis |
| ADC (flash/SAR) | Transient | Ramp or step input, show digital output |
| LDO regulator | Transient | Show startup and load step response |
| Charge pump | Transient | Show output voltage buildup over multiple cycles |
| VCO | Transient | Multiple Vctrl values to show frequency tuning |
| Gilbert cell mixer | Transient | Show IF output, use FFT for spectrum |
| Bandgap reference | Transient + DC temp sweep | Verify PTAT and CTAT cancellation |

---

## SECTION 6: Simulation Parameters Per Analysis Type

### Transient Analysis
```python
# Standard transient
analysis = simulator.transient(
    step_time=1@u_ns,           # time step (resolution)
    end_time=1@u_us,            # simulation duration
    max_time=10@u_ns,           # max internal step (optional, for accuracy)
    use_initial_condition=True  # use .IC values (important for oscillators)
)

# High-speed circuits (GHz range)
analysis = simulator.transient(step_time=1@u_ps, end_time=10@u_ns)

# Low-speed circuits (audio, power)
analysis = simulator.transient(step_time=1@u_us, end_time=10@u_ms)
```

### AC Analysis
```python
# Logarithmic sweep (most common for amplifiers, filters)
analysis = simulator.ac(
    start_frequency=1@u_Hz,
    stop_frequency=10@u_GHz,
    number_of_points=100,
    variation='dec'   # 'dec' = decades, 'lin' = linear, 'oct' = octaves
)

# Extract gain and phase
import numpy as np
vout = np.array(analysis['vout'])
gain_db = 20 * np.log10(np.abs(vout))
phase_deg = np.unwrap(np.angle(vout)) * 180 / np.pi
freq = np.array(analysis.frequency)
```

### DC Analysis
```python
# Single voltage sweep
analysis = simulator.dc(Vin=slice(0, 5, 0.01))   # 0V to 5V in 10mV steps

# Operating point (single DC solution)
analysis = simulator.operating_point()

# Access operating point results
for node, voltage in analysis.nodes.items():
    print(f"V({node}) = {float(voltage):.4f} V")
```

### Noise Analysis
```python
analysis = simulator.noise(
    output_node='vout',
    input_source='Vin',
    start_frequency=1@u_Hz,
    stop_frequency=1@u_GHz,
    number_of_points=100,
    variation='dec'
)
# access: analysis.spectral_density_v_squared (V²/Hz)
```

---

## SECTION 7: Convergence and Error Handling

### Tolerance Settings Per Circuit Type
```python
# Digital circuits (fast, large signals)
simulator.options(reltol=1e-4, abstol=1e-9, vntol=1e-3)

# Analog circuits (accuracy matters)
simulator.options(reltol=1e-5, abstol=1e-12, vntol=1e-6)

# RF circuits (very tight tolerances)
simulator.options(reltol=1e-6, abstol=1e-15, vntol=1e-8, chgtol=1e-15)
```

### Oscillator Convergence
```python
# Oscillators often fail to start — use these techniques:
# 1. Use initial conditions (UIC) with slightly asymmetric IC values
# 2. Use 'gear' integration method (more stable than trapezoid)
# 3. Add tiny parasitic capacitances at oscillator nodes

simulator.options(method='gear', reltol=1e-5, abstol=1e-12)
analysis = simulator.transient(step_time=0.1@u_ns, end_time=50@u_ns,
                               use_initial_condition=True)
```

### Error Handling Pattern
```python
try:
    analysis = simulator.transient(step_time=1@u_ns, end_time=1@u_us)
except Exception as e:
    print(f"Simulation failed: {e}")
    # Try with relaxed tolerances
    try:
        simulator.options(reltol=1e-3, abstol=1e-9, vntol=1e-3, gmin=1e-9)
        analysis = simulator.transient(step_time=2@u_ns, end_time=1@u_us)
    except Exception as e2:
        print(f"Retry also failed: {e2}")
        # Try even more relaxed + shorter sim
        simulator.options(reltol=1e-2, abstol=1e-6)
        analysis = simulator.transient(step_time=5@u_ns, end_time=100@u_ns)
```

### Common NgSpice Error Messages and Fixes
```
"no DC path to ground from node X"
→ Add a large resistor (1GΩ) from floating node to gnd

"Timestep too small"
→ Increase step_time or reduce simulation complexity; try method='gear'

"Singular matrix"
→ Check for floating nodes, zero-resistance loops (add small series R)

"GMIN stepping failed"
→ Add .options gmin=1e-9 or reduce circuit complexity

"MOSFET model parameter out of range"
→ Check vto sign (positive for NMOS, negative for PMOS); check kp units (A/V²)

"ngspice not found" / "simulator not found"
→ Install ngspice: Linux: apt install ngspice | Mac: brew install ngspice | Windows: download from ngspice.sourceforge.net

"convergence failure at t=..."
→ Try use_initial_condition=True; reduce step_time; add .ic statements
```

### Integration Methods
```python
# Default: trapezoidal (fast but can oscillate with stiff circuits)
simulator.options(method='trap')

# Gear (more stable for stiff circuits like oscillators and power)
simulator.options(method='gear')

# Backward Euler (most stable but least accurate, use for startup)
# Not directly settable in PySpice — use gear order=1 equivalent
```

---

## SECTION 8: Subcircuits and Hierarchy

### Reusable SubCircuit Template
```python
from PySpice.Spice.Netlist import Circuit, SubCircuit
from PySpice.Unit import *

class CMOSInverter(SubCircuit):
    """Reusable CMOS inverter subcircuit"""
    __nodes__ = ('in_', 'out', 'vdd', 'gnd')

    def __init__(self, name='INV'):
        SubCircuit.__init__(self, name, *self.__nodes__)
        self.MOSFET('MN', 'out', 'in_', 'gnd', 'gnd', model='NMOS')
        self.MOSFET('MP', 'out', 'in_', 'vdd', 'vdd', model='PMOS')

# Use in main circuit:
circuit = Circuit('Ring Oscillator using Subcircuits')
circuit.V('dd', 'vdd', circuit.gnd, 5@u_V)

# Define models at circuit level (shared by subcircuits)
circuit.model('NMOS', 'nmos', level=1, kp=120e-6, vto=0.7, lambda_=0.02, w=10e-6, l=1e-6)
circuit.model('PMOS', 'pmos', level=1, kp=60e-6, vto=-0.7, lambda_=0.02, w=20e-6, l=1e-6)

# Add subcircuit definitions
circuit.subcircuit(CMOSInverter('INV'))

# Instantiate subcircuits
circuit.X('inv1', 'INV', 'v3', 'v1', 'vdd', circuit.gnd)
circuit.X('inv2', 'INV', 'v1', 'v2', 'vdd', circuit.gnd)
circuit.X('inv3', 'INV', 'v2', 'v3', 'vdd', circuit.gnd)
```

### Parameterized Subcircuits
```python
class CurrentMirror(SubCircuit):
    """NMOS current mirror. ratio = W_out / W_ref"""
    __nodes__ = ('iref_in', 'iout', 'vss')

    def __init__(self, ratio=1, W=20e-6, L=4e-6):
        SubCircuit.__init__(self, f'CM_{ratio}x', *self.__nodes__)
        self.MOSFET('M_ref', 'iref_in', 'iref_in', 'vss', 'vss',
                    model='NMOS', w=W, l=L)
        self.MOSFET('M_out', 'iout', 'iref_in', 'vss', 'vss',
                    model='NMOS', w=W*ratio, l=L)

circuit.subcircuit(CurrentMirror(ratio=2))  # 2x mirror
circuit.X('cm1', 'CM_2x', 'iref', 'iout', circuit.gnd)
```

---

## SECTION 9: Accessing Raw SPICE Netlist

```python
# After building circuit object, get raw SPICE netlist:
print(circuit.str())   # prints the SPICE netlist as a string

# Save to file:
with open('circuit.sp', 'w') as f:
    f.write(circuit.str())

# The netlist format follows standard SPICE syntax:
# * Title line
# .subckt / .ends for subcircuits
# M<name> drain gate source bulk <model> W=<w> L=<l>
# R<name> n1 n2 <value>
# C<name> n1 n2 <value>
# V<name> n+ n- <value>
# .model <name> <type> <params>
# .tran <step> <end> [start] [max_step]
# .ac <variation> <points> <start_freq> <stop_freq>
# .dc <source> <start> <stop> <step>
# .end
```

---

## SECTION 10: Plotting Best Practices

### Transient Plot (multiple signals, shared x-axis)
```python
fig, axes = plt.subplots(N_signals, 1, figsize=(12, 3*N_signals), sharex=True)
t_ns = np.array(analysis.time) * 1e9  # convert to nanoseconds

for i, (node, label) in enumerate(zip(nodes, labels)):
    axes[i].plot(t_ns, np.array(analysis[node]), linewidth=1.5)
    axes[i].set_ylabel(label); axes[i].grid(True, alpha=0.3)
    axes[i].legend([label], loc='upper right')

axes[-1].set_xlabel('Time (ns)')
plt.suptitle('Circuit Name — Transient Analysis')
plt.tight_layout()
plt.show()
```

### Bode Plot (AC analysis)
```python
fig, (ax_gain, ax_phase) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
freq = np.array(analysis.frequency)
vout = np.array(analysis['vout'])

# Gain (dB)
gain_db = 20 * np.log10(np.abs(vout) + 1e-300)  # avoid log(0)
ax_gain.semilogx(freq, gain_db, 'b-', linewidth=2)
ax_gain.set_ylabel('Gain (dB)'); ax_gain.grid(True, which='both', alpha=0.3)
ax_gain.axhline(y=max(gain_db)-3, color='r', linestyle='--', label='-3dB')
ax_gain.legend()

# Phase (degrees, unwrapped)
phase_deg = np.unwrap(np.angle(vout)) * 180 / np.pi
ax_phase.semilogx(freq, phase_deg, 'r-', linewidth=2)
ax_phase.set_ylabel('Phase (°)'); ax_phase.set_xlabel('Frequency (Hz)')
ax_phase.grid(True, which='both', alpha=0.3)
ax_phase.axhline(y=-180, color='k', linestyle='--', alpha=0.5)

plt.suptitle('Bode Plot'); plt.tight_layout(); plt.show()
```

### FFT for Oscillator / Mixer Output
```python
from numpy.fft import fft, fftfreq

t = np.array(analysis.time)
v = np.array(analysis['vout'])
dt = t[1] - t[0]
N = len(v)

V_fft = np.abs(fft(v))[:N//2] * 2/N
freqs = fftfreq(N, d=dt)[:N//2]

plt.figure(figsize=(10, 5))
plt.plot(freqs/1e6, 20*np.log10(V_fft + 1e-300), 'b-')
plt.xlabel('Frequency (MHz)'); plt.ylabel('Amplitude (dBV)')
plt.title('FFT Spectrum'); plt.grid(True); plt.xlim(0, freqs[-1]/1e6)
plt.show()
```

### DC Transfer Curve
```python
# For inverter or amplifier DC sweep
plt.figure(figsize=(8, 6))
plt.plot(np.array(analysis['vin']), np.array(analysis['vout']), 'b-', linewidth=2)
plt.xlabel('Input Voltage (V)'); plt.ylabel('Output Voltage (V)')
plt.title('DC Transfer Characteristic')
# Mark switching threshold
plt.plot([2.5, 2.5], [0, 5], 'r--', alpha=0.5, label='Vdd/2')
plt.legend(); plt.grid(True); plt.show()
```

---

## SECTION 11: Python Keyword Conflicts & PySpice Quirks

### Reserved Words — Always Add Underscore
```python
# WRONG → CORRECT
lambda   → lambda_      # channel-length modulation parameter
is       → is_          # junction saturation current
in       → in_          # input node name
not      → not_         # node name
and      → and_         # node name
model    → model_       # avoid if used as variable
input    → input_       # not reserved but conventional
```

### Node Naming Conventions
```python
# Good node names (alphanumeric + underscore)
'vdd', 'vss', 'vin', 'vout', 'clk', 'clkb', 'tail', 'vbias', 'ref_drain'

# Avoid: spaces, special characters, names starting with numbers
# PySpice converts to SPICE internally — stick to simple names

# Ground: ALWAYS use circuit.gnd (not '0', 'gnd', 'GND')
circuit.gnd  # correct
```

### MOSFET Model Parameters — Use Plain Floats, NOT Unit Objects
```python
# WRONG: u_uA_per_V2, u_fF, u_aF do NOT exist in PySpice 1.5
circuit.model('nmos', 'nmos', kp=120@u_uA_per_V2)  # NameError!
circuit.C('load', 'vout', circuit.gnd, 5@u_fF)      # NameError!

# CORRECT for model(): always plain Python floats (SI units)
circuit.model('nmos', 'nmos', level=1,
    kp=120e-6,      # 120 uA/V^2 — plain float in A/V^2
    vto=0.5,        # threshold voltage in V
    lambda_=0.01,   # channel-length modulation in V^-1
    gamma=0.4,      # body effect coefficient
    phi=0.65,       # surface potential in V
)
circuit.model('pmos', 'pmos', level=1,
    kp=60e-6, vto=-0.5, lambda_=0.01)

# CORRECT for sub-pF capacitors: express in pF
circuit.C('load', 'vout', circuit.gnd, 5e-3@u_pF)  # 5 fF = 0.005 pF
# Or use plain float with PySpice unit:
circuit.C('load', 'vout', circuit.gnd, 0.005@u_pF)

# Rule: ALL circuit.model() params = plain floats. NO @u_X inside model().
```

### PySpice Version Differences
```python
# PySpice 1.4 vs 1.5: unit system changed slightly
# Always use: from PySpice.Unit import *
# Then use @u_V, @u_Hz etc.

# MOSFET instantiation: use string name for first arg (PySpice 1.5+)
circuit.MOSFET('M1', ...)   # string name preferred over integer

# SinusoidalVoltageSource: keyword args vary between versions
# Safe form:
circuit.SinusoidalVoltageSource('vin', 'vin_node', circuit.gnd,
    offset=0@u_V, amplitude=1@u_V, frequency=1@u_kHz)

# PulseVoltageSource safe form:
circuit.PulseVoltageSource('vpulse', 'node', circuit.gnd,
    initial_value=0@u_V, pulsed_value=5@u_V,
    delay_time=0@u_ns, rise_time=1@u_ns, fall_time=1@u_ns,
    pulse_width=50@u_ns, period=100@u_ns)
```

### AC Source for Open-Loop Analysis
```python
# For AC analysis, set source to 'DC 0 AC 1' using raw SPICE string
circuit.V('vin_ac', 'vin_ac_node', circuit.gnd, 'DC 0 AC 1')
# PySpice alternately:
circuit.SinusoidalVoltageSource('vin_ac', 'vin_ac_node', circuit.gnd,
    offset=0@u_V, amplitude=1@u_V, frequency=1@u_kHz)
# The amplitude is not used in AC analysis — only magnitude normalization matters
```

---

## GENERATION RULES (Always Follow)

1. **Always** start with required imports (Section 1)
2. **Always** use `circuit.gnd` — never a string for ground
3. **Always** define MOSFET models with `circuit.model()` before using them
4. **Always** include at least one analysis (transient, AC, or DC)
5. **Always** plot results using matplotlib with proper labels, grid, and title
6. **Always** call `plt.show()` at the end so figures are captured
7. **Choose** analysis type based on Section 5 table
8. **Use** the `try/except` error handling pattern from Section 7 for all simulations
9. **Set** simulation options (reltol, abstol) before running analysis
10. **Include** SPICE netlist access: after building circuit, `print(circuit.str())` if asked

---
*SPICEPilot Pilot Prompt — Version 2.0 | Compatible with ngspice 36–42+, PySpice 1.4–1.5+*
*Covers: Easy, Medium, Hard, and Extreme benchmark circuits*
