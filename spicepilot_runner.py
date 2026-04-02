"""
SPICEPilot simulation runner — injected into generated PySpice code at execution time.
Replaces PySpice's server/shared simulator with a Windows-compatible batch-mode runner.
"""

import os
import re
import subprocess
import tempfile
import numpy as np


class SpicePilotAnalysis:
    """Drop-in for PySpice analysis objects. Supports analysis['node'], analysis.time, analysis.frequency."""

    def __init__(self, variables, columns, sweep_var='time'):
        self._vars = {}
        for name, col in zip(variables, columns):
            self._vars[name.lower()] = np.array(col, dtype=float)
        self._sweep = sweep_var.lower()

    def __getitem__(self, key):
        k = key.lower()
        # Try exact match, then v(key), then strip outer v(...)
        for attempt in [k, 'v(' + k + ')', k.lstrip('v(').rstrip(')')]:
            if attempt in self._vars:
                return self._vars[attempt]
        # Partial match (e.g. 'out' matches 'v(out)')
        for varname in self._vars:
            if k in varname:
                return self._vars[varname]
        raise KeyError(f"Node '{key}' not found. Available: {list(self._vars.keys())}")

    @property
    def time(self):
        return self._vars.get(self._sweep, np.array([]))

    @property
    def frequency(self):
        return self._vars.get('frequency', np.array([]))

    @property
    def nodes(self):
        return {k: v for k, v in self._vars.items() if k != self._sweep}


def parse_ascii_raw(text):
    """Parse ngspice ASCII raw file (Values: format) into SpicePilotAnalysis."""
    lines = text.splitlines()
    variables = []
    n_vars = 0
    in_vars = False
    in_values = False
    rows = []
    current_row = []

    for line in lines:
        ls = line.strip()
        ll = ls.lower()

        if ll.startswith('no. variables:'):
            n_vars = int(ls.split(':')[1].strip())
        elif ll.startswith('no. points:'):
            # Format: "No. Points: 235     "
            n_pts_str = ls.split(':')[1].strip().split()[0]
            # n_pts = int(n_pts_str)  # not needed, rows accumulate
        elif ll == 'variables:':
            in_vars = True
            continue
        elif ll == 'values:':
            in_vars = False
            in_values = True
            continue
        elif in_vars and ls:
            # Tab-separated: index \t varname \t type
            parts = ls.split('\t')
            vname = parts[1].strip() if len(parts) > 1 else ls
            variables.append(vname)
        elif in_values and ls:
            # Each row: index \t\t value \n \t value \n ...
            # Split by tabs, try to parse each non-empty piece as float
            parts = line.split('\t')
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                try:
                    current_row.append(float(p))
                except ValueError:
                    pass  # skip row indices

            if n_vars and len(current_row) >= n_vars:
                rows.append(current_row[:n_vars])
                current_row = current_row[n_vars:]

    if not rows or not variables:
        raise RuntimeError(
            'Could not parse ngspice ASCII output. No data rows found.\n'
            f'Header variables found: {variables}\n'
            f'First 200 chars: {text[:200]}'
        )

    columns = list(zip(*rows))
    return SpicePilotAnalysis(variables, columns, sweep_var=variables[0])


def run_ngspice_batch(ngspice_exe, netlist_str, timeout=75):
    """Write netlist to temp file, run ngspice -b -r, parse ASCII output."""
    td = tempfile.mkdtemp()
    sp_f = os.path.join(td, 'circuit.sp')
    raw_f = os.path.join(td, 'circuit.raw')

    if '.save' not in netlist_str.lower():
        netlist_str = netlist_str.rstrip() + '\n.save all\n'

    with open(sp_f, 'w') as fh:
        fh.write(netlist_str)

    result = subprocess.run(
        [ngspice_exe, '-b', '-r', raw_f, sp_f],
        capture_output=True,
        timeout=timeout
    )

    if not os.path.exists(raw_f) or os.path.getsize(raw_f) == 0:
        stderr = result.stderr.decode('utf-8', errors='replace')
        raise RuntimeError(
            f'ngspice did not produce output (exit code {result.returncode}).\n{stderr[:400]}'
        )

    with open(raw_f, 'r', errors='replace') as fh:
        raw_text = fh.read()

    return parse_ascii_raw(raw_text)


def _unit_to_float(val):
    """Convert PySpice unit quantity to plain float."""
    if hasattr(val, 'convert_to_power'):
        try:
            return float(val.convert_to_power(0))
        except Exception:
            pass
    return float(val)


class BatchSimulator:
    """Replaces PySpice's CircuitSimulator with a Windows-compatible batch runner."""

    def __init__(self, circuit, ngspice_exe, temperature=25, nominal_temperature=25):
        self._circuit = circuit
        self._ngspice_exe = ngspice_exe
        self._options = {}

    def options(self, **kwargs):
        self._options.update(kwargs)

    def _build_netlist(self, analysis_line):
        base = str(self._circuit).rstrip()
        if self._options:
            opts = ' '.join(f'{k}={v}' for k, v in self._options.items())
            base += f'\n.options {opts}'
        base += f'\n{analysis_line}\n.save all\n'
        return base

    def transient(self, step_time, end_time, use_initial_condition=False, **kw):
        st = _unit_to_float(step_time)
        et = _unit_to_float(end_time)
        uic = ' UIC' if use_initial_condition else ''
        return run_ngspice_batch(
            self._ngspice_exe,
            self._build_netlist(f'.tran {st} {et}{uic}')
        )

    def ac(self, variation='dec', number_of_points=100,
           start_frequency=None, stop_frequency=None, **kw):
        sf = _unit_to_float(start_frequency)
        ef = _unit_to_float(stop_frequency)
        return run_ngspice_batch(
            self._ngspice_exe,
            self._build_netlist(f'.ac {variation} {number_of_points} {sf} {ef}')
        )

    def operating_point(self):
        return run_ngspice_batch(
            self._ngspice_exe,
            self._build_netlist('.op')
        )

    def dc(self, **kwargs):
        parts = []
        for src, val in kwargs.items():
            if isinstance(val, slice):
                parts.append(f'{src} {val.start} {val.stop} {val.step}')
        cmd = ('.dc ' + ' '.join(parts)) if parts else '.op'
        return run_ngspice_batch(self._ngspice_exe, self._build_netlist(cmd))

    def noise(self, output_node, input_source,
              variation='dec', number_of_points=100,
              start_frequency=None, stop_frequency=None, **kw):
        sf = _unit_to_float(start_frequency)
        ef = _unit_to_float(stop_frequency)
        return run_ngspice_batch(
            self._ngspice_exe,
            self._build_netlist(
                f'.noise V({output_node}) {input_source} {variation} {number_of_points} {sf} {ef}'
            )
        )


def setup(ngspice_exe):
    """Monkey-patch PySpice's Circuit.simulator to use BatchSimulator."""
    try:
        from PySpice.Spice.Netlist import Circuit

        def _patched_simulator(self, *args, **kwargs):
            return BatchSimulator(
                self,
                ngspice_exe=ngspice_exe,
                temperature=kwargs.get('temperature', 25),
                nominal_temperature=kwargs.get('nominal_temperature', 25)
            )

        Circuit.simulator = _patched_simulator
    except Exception as e:
        print(f'[SPICEPilot] Warning: could not patch simulator: {e}')
