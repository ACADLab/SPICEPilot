"""
SPICEPilot Web Application
AI-powered SPICE/PySpice circuit simulation with bring-your-own-key support.
"""

import os
import re
import sys
import json
import tempfile
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Load system prompt once at startup
_prompt_path = Path(__file__).parent / "Pilot_prompt.md"
if not _prompt_path.exists():
    raise FileNotFoundError(f"Pilot_prompt.md not found at {_prompt_path}")
SYSTEM_PROMPT = _prompt_path.read_text(encoding="utf-8")

# ── Locate ngspice executable ────────────────────────────────────────────────
def _find_ngspice() -> str | None:
    """Return path to ngspice executable or None."""
    import shutil

    # 1. Standard PATH lookup
    found = shutil.which('ngspice')
    if found:
        return found

    # 2. Common Windows install locations
    candidates = [
        os.path.expanduser('~/ngspice46/Spice64/bin/ngspice.exe'),
        os.path.expanduser('~/ngspice/Spice64/bin/ngspice.exe'),
        r'C:\ngspice\bin\ngspice.exe',
        r'C:\Program Files\ngspice\bin\ngspice.exe',
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path

    return None


NGSPICE_EXE = _find_ngspice()
NGSPICE_AVAILABLE = NGSPICE_EXE is not None
NGSPICE_METHOD = 'ngspice-subprocess' if NGSPICE_AVAILABLE else 'none'

# Add ngspice directory to PATH so PySpice subprocess mode can find it
if NGSPICE_EXE:
    ngspice_bin_dir = str(Path(NGSPICE_EXE).parent)
    os.environ['PATH'] = ngspice_bin_dir + os.pathsep + os.environ.get('PATH', '')

# ── Execution preamble injected before user code ──────────────────────────────
# Use __NGSPICE_BIN__ as placeholder to avoid .format() collisions with f-strings
_PREAMBLE_TEMPLATE = r"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io
import json as _json
import sys
import os

# Ensure ngspice is on PATH for subprocess simulator
_ngspice_bin = __NGSPICE_BIN__
if _ngspice_bin and _ngspice_bin not in os.environ.get('PATH', ''):
    os.environ['PATH'] = _ngspice_bin + os.pathsep + os.environ.get('PATH', '')

# Setup SPICEPilot batch-mode runner (patches Circuit.simulator)
import sys as _sys
_sys.path.insert(0, __PROJECT_DIR__)
import spicepilot_runner as _runner
_runner.setup(__NGSPICE_EXE__)

# Add missing PySpice units (femto/atto scale not in PySpice 1.5)
try:
    from PySpice.Unit import u_pF, u_nH
    u_fF = 1e-3 @ u_pF    # 1 femtofarad = 0.001 pF
    u_aF = 1e-6 @ u_pF    # 1 attofarad = 1e-6 pF
    u_pH = 1e-3 @ u_nH    # 1 picohenry = 0.001 nH
    u_fA = None            # femtoampere placeholder (rarely used)
except Exception:
    pass

_captured_figures = []
_original_show = plt.show

def _patched_show(*args, **kwargs):
    for fig_num in plt.get_fignums():
        fig = plt.figure(fig_num)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        _captured_figures.append('data:image/png;base64,' + b64)
        buf.close()
    plt.close('all')

plt.show = _patched_show

# ── USER CODE BEGIN ──
"""

# ── Execution postamble injected after user code ──────────────────────────────
EXECUTION_POSTAMBLE = r"""
# ── USER CODE END ──

# Capture any figures that were never explicitly shown
try:
    for _fig_num in plt.get_fignums():
        _fig = plt.figure(_fig_num)
        _buf = io.BytesIO()
        _fig.savefig(_buf, format='png', dpi=150, bbox_inches='tight')
        _buf.seek(0)
        _b64 = base64.b64encode(_buf.read()).decode('utf-8')
        _captured_figures.append('data:image/png;base64,' + _b64)
        _buf.close()
    plt.close('all')
except Exception:
    pass

# Capture circuit netlist (search all locals/globals for Circuit instance)
_netlist = None
try:
    from PySpice.Spice.Netlist import Circuit as _CircuitClass
    _all_vars = list(globals().values())
    for _v in _all_vars:
        if isinstance(_v, _CircuitClass):
            _netlist = str(_v)
            break
except Exception:
    pass

# Emit results marker to stdout
print('__SPICEPILOT_RESULTS__' + _json.dumps({
    'plots': _captured_figures,
    'netlist': _netlist
}))
"""


# ── LLM integration ───────────────────────────────────────────────────────────

def call_anthropic(api_key: str, model: str, user_prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return message.content[0].text


def call_openai(api_key: str, model: str, user_prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content


# ── Code extraction ───────────────────────────────────────────────────────────

def extract_python_code(llm_response: str) -> str:
    """Extract Python code block from LLM response."""
    bt = '`' * 3  # build backtick fence without confusing static analysis

    # Case 1: ```python ... ```
    match = re.search(bt + r'python\s+(.*?)' + bt, llm_response, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Case 2: plain ``` ... ```
    match = re.search(bt + r'\s*(.*?)' + bt, llm_response, re.DOTALL)
    if match:
        code = match.group(1).strip()
        if 'PySpice' in code or 'circuit' in code.lower():
            return code

    # Case 3: response starts with Python code
    stripped = llm_response.strip()
    if stripped.startswith(('from PySpice', 'import PySpice', 'from pyspice',
                             'import matplotlib', 'from PySpice.Spice')):
        return stripped

    raise ValueError("No Python code block found in LLM response. "
                     "Try rephrasing your prompt to be more specific.")


# ── Safe subprocess execution ─────────────────────────────────────────────────

def run_pyspice_code(code: str, timeout: int = 90) -> dict:
    """Execute PySpice code safely in a subprocess with timeout."""
    ngspice_bin = str(Path(NGSPICE_EXE).parent) if NGSPICE_EXE else ''
    ngspice_exe = NGSPICE_EXE or ''
    project_dir = str(Path(__file__).parent)
    preamble = (_PREAMBLE_TEMPLATE
                .replace('__NGSPICE_BIN__', repr(ngspice_bin))
                .replace('__NGSPICE_EXE__', repr(ngspice_exe))
                .replace('__PROJECT_DIR__', repr(project_dir)))
    full_code = preamble + "\n" + code + "\n" + EXECUTION_POSTAMBLE

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(full_code)
            tmp_path = f.name

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(Path(__file__).parent)
        )

        stdout = result.stdout
        stderr = result.stderr
        plots = []
        netlist = None

        marker = '__SPICEPILOT_RESULTS__'
        if marker in stdout:
            normal_stdout, _, json_part = stdout.partition(marker)
            try:
                data = json.loads(json_part)
                plots = data.get('plots', [])
                netlist = data.get('netlist')
            except json.JSONDecodeError:
                pass
            stdout = normal_stdout

        return {
            'success': result.returncode == 0,
            'stdout': stdout.strip(),
            'stderr': stderr.strip(),
            'plots': plots,
            'netlist': netlist,
            'error': None if result.returncode == 0 else
                     f"Process exited with code {result.returncode}"
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': '',
            'plots': [],
            'netlist': None,
            'error': f'Simulation timed out after {timeout} seconds. '
                     'Try a simpler circuit or shorter simulation time.'
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': '',
            'plots': [],
            'netlist': None,
            'error': f'Execution error: {str(e)}'
        }
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass  # Windows may hold the handle briefly


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'prompt_loaded': bool(SYSTEM_PROMPT),
        'ngspice_available': NGSPICE_AVAILABLE,
        'ngspice_method': NGSPICE_METHOD
    })


@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.get_json(force=True)

    provider = data.get('provider', 'anthropic').strip().lower()
    api_key = data.get('api_key', '').strip()
    model = data.get('model', '').strip()
    user_prompt = data.get('prompt', '').strip()

    # Validation
    if not api_key:
        return jsonify({'success': False, 'error': 'API key is required'}), 400
    if not user_prompt:
        return jsonify({'success': False, 'error': 'Circuit prompt is required'}), 400
    if provider not in ('anthropic', 'openai'):
        return jsonify({'success': False, 'error': f'Unknown provider: {provider}'}), 400

    # Default models (cheapest capable options)
    if not model:
        model = 'claude-haiku-4-5-20251001' if provider == 'anthropic' else 'gpt-4o-mini'

    # Step 1: Call LLM
    try:
        if provider == 'anthropic':
            llm_response = call_anthropic(api_key, model, user_prompt)
        else:
            llm_response = call_openai(api_key, model, user_prompt)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LLM API error: {str(e)}'
        }), 502

    # Step 2: Extract Python code from response
    try:
        pyspice_code = extract_python_code(llm_response)
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'raw_response': llm_response[:2000]  # send partial for debugging
        }), 422

    # Step 3: Execute simulation
    sim_result = run_pyspice_code(pyspice_code, timeout=90)

    return jsonify({
        'success': sim_result['success'],
        'pyspice_code': pyspice_code,
        'spice_netlist': sim_result['netlist'],
        'plots': sim_result['plots'],
        'stdout': sim_result['stdout'],
        'stderr': sim_result['stderr'],
        'error': sim_result['error']
    })


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=False)
