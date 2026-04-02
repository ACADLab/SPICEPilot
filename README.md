# SPICEPilot: AI-Powered SPICE Circuit Simulation Web App

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![ngspice 36+](https://img.shields.io/badge/ngspice-36%2B-orange.svg)](https://ngspice.sourceforge.io)

**SPICEPilot** is an AI-driven circuit simulation framework with a bring-your-own-key web interface. Describe a circuit in plain English, and SPICEPilot uses an LLM (Anthropic Claude or OpenAI GPT) to generate PySpice code, runs it through ngspice, and returns waveform plots, PySpice source code, and the raw SPICE netlist — all in your browser.

---

## Table of Contents

- [What It Does](#what-it-does)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Using the Web UI](#using-the-web-ui)
- [Project Structure](#project-structure)
- [How It Works Internally](#how-it-works-internally)
- [Modifying & Extending](#modifying--extending)
- [Benchmarking Framework](#benchmarking-framework)
- [Troubleshooting](#troubleshooting)
- [Citation](#citation)
- [License](#license)

---

## What It Does

1. You type a circuit description into the web UI (e.g., *"Design a CMOS inverter with 1.8V supply and transient analysis"*).
2. Your API key is sent with the request and used to call Claude or GPT — **it is never stored**.
3. The LLM generates PySpice Python code guided by a comprehensive system prompt (`Pilot_prompt.md`).
4. The backend executes that code in an isolated subprocess against the local ngspice simulator.
5. Results are returned to the browser: **waveform plots** (PNG), **PySpice code**, **raw SPICE netlist**, and simulation stdout/stderr.

---

## Architecture Overview

```
Browser (index.html)
       │  POST /simulate  {provider, api_key, model, prompt}
       ▼
Flask Backend (app.py)
       │
       ├─► call_anthropic() / call_openai()   ← LLM API call using your key
       │        │  returns LLM response text
       │
       ├─► extract_python_code()              ← parse ```python block from response
       │        │  returns PySpice code string
       │
       └─► run_pyspice_code()                 ← isolated subprocess execution
                │
                ├─ Injects preamble (matplotlib Agg, plt.show patch, spicepilot_runner)
                ├─ Appends postamble (captures figures + netlist, emits JSON marker)
                ├─ Writes to tempfile → subprocess.run([python, tmpfile])
                └─ Parses __SPICEPILOT_RESULTS__ JSON from stdout
                         │
                         └─► spicepilot_runner.py
                                  │
                                  ├─ BatchSimulator patches Circuit.simulator()
                                  ├─ Runs: ngspice -b -r circuit.raw circuit.sp
                                  └─ parse_ascii_raw() → SpicePilotAnalysis object
```

**Key design decisions:**
- **ngspice batch mode** (`-b -r`) is used instead of PySpice's built-in subprocess server mode, which hangs on Windows. This is handled transparently by monkey-patching `Circuit.simulator`.
- **Subprocess isolation**: LLM-generated code runs in a fresh Python process with a 90-second timeout. The main Flask process is never exposed to arbitrary execution.
- **Bring-your-own-key**: API keys live only in the HTTP request and in-memory during the LLM call. Never logged, never written to disk.

---

## Prerequisites

### 1. Python 3.8+
Download from [python.org](https://python.org). Verify: `python --version`

### 2. ngspice 36 or later (required for simulation)

**Windows:**
```
Download: https://sourceforge.net/projects/ngspice/files/ng-spice-rework/
Recommended: ngspice-46_64.exe or ngspice-46_64.7z
Install to: C:\ngspice\  or  %USERPROFILE%\ngspice46\
```
The app will automatically find ngspice in common locations. You can also add it to your system `PATH`.

**macOS:**
```bash
brew install ngspice
```

**Linux / Ubuntu WSL:**
```bash
sudo apt-get install ngspice
```

### 3. An API key
- **Anthropic Claude**: Get a key at [console.anthropic.com](https://console.anthropic.com)
- **OpenAI GPT**: Get a key at [platform.openai.com](https://platform.openai.com)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/ACADLab/SPICEPilot.git
cd SPICEPilot

# 2. (Recommended) Create a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt
```

**`requirements.txt` contents:**
```
flask>=3.0.0
anthropic>=0.25.0
openai>=1.30.0
PySpice>=1.5
matplotlib>=3.8.0
numpy>=1.24.0
```

---

## Running the App

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5001
```

Open [http://127.0.0.1:5001](http://127.0.0.1:5001) in your browser.

To verify everything is configured correctly before running a simulation, check:
```
http://127.0.0.1:5001/health
```
Expected response:
```json
{
  "status": "ok",
  "prompt_loaded": true,
  "ngspice_available": true,
  "ngspice_method": "ngspice-subprocess"
}
```
If `ngspice_available` is `false`, ngspice is not on your PATH or in the expected install locations — see [Troubleshooting](#troubleshooting).

---

## Using the Web UI

1. **Select provider** — Anthropic or OpenAI (toggle buttons at the top)
2. **Enter your API key** — paste your key (eye icon to show/hide). It is used once per request and never stored.
3. **Select a model** — faster/cheaper options are listed first:
   - Anthropic: Claude Haiku 4.5 (default), Claude Sonnet 4.6, Claude Opus 4.6
   - OpenAI: GPT-4o Mini (default), GPT-4o
4. **Describe your circuit** — be specific about topology, supply voltage, device sizes, and desired analysis type. Example prompts:
   - *"Design a CMOS inverter with 1.8V supply, 180nm channel length, NMOS W=0.5um PMOS W=1um. Run transient analysis over 40ns with a 10ns pulse input."*
   - *"Design a two-stage OTA with 5V supply and 100MHz gain-bandwidth. Run AC analysis from 1Hz to 1GHz."*
   - *"Design a ring oscillator with 5 CMOS inverter stages, 5V supply, 180nm technology. Show oscillation waveform and FFT."*
5. **Click Simulate** (or press `Ctrl+Enter`) — an elapsed timer shows while the LLM and simulator run (typically 10–60 seconds).
6. **View results**:
   - **PySpice Code** — the generated Python code with a Copy button
   - **SPICE Netlist** — raw SPICE deck extracted from the circuit object, with Copy button
   - **Waveform Plots** — PNG images with individual Download buttons
   - **Simulation Output** — stdout and stderr tabs for debugging

---

## Project Structure

```
SPICEPilot/
├── app.py                  # Flask backend — routes, LLM calls, code execution
├── spicepilot_runner.py    # Windows-compatible ngspice batch runner
├── Pilot_prompt.md         # LLM system prompt — comprehensive circuit knowledge base
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Dark-themed single-page web UI (no external dependencies)
├── Claude_tests/           # Reference PySpice examples generated by Claude
│   ├── easy/
│   ├── medium/
│   ├── hard/
│   └── extreme/
├── GPT_tests/              # Reference PySpice examples generated by GPT
├── New_bench-mark.md       # 90+ circuit benchmark definitions (Easy/Medium/Hard/Extreme)
├── LICENSE
└── README.md
```

---

## How It Works Internally

### `app.py` — Flask Backend

**Startup:**
- Loads `Pilot_prompt.md` into `SYSTEM_PROMPT` (used as the LLM system message for every request)
- Locates ngspice executable by checking PATH and common install paths
- Adds ngspice's `bin/` directory to `PATH` for subprocess access

**`/simulate` endpoint (POST):**
1. Validates `api_key`, `prompt`, `provider`
2. Calls LLM with `SYSTEM_PROMPT` + user's circuit description
3. Extracts the `\`\`\`python` code block from the LLM response
4. Injects a preamble + postamble around the generated code and runs it in a subprocess
5. Parses results from a JSON marker printed to stdout

**Code execution wrapper (`run_pyspice_code`):**

The preamble injected before user code does:
- Sets `matplotlib` to `Agg` (non-interactive) backend
- Patches `plt.show()` to capture figures as base64 PNG strings instead of opening windows
- Imports and initializes `spicepilot_runner` (patches `Circuit.simulator`)
- Defines missing PySpice 1.5 units (`u_fF`, `u_pH`, etc.)

The postamble injected after user code does:
- Captures any figures not explicitly shown
- Scans `globals()` for a `Circuit` instance and calls `str(circuit)` for the SPICE netlist
- Prints `__SPICEPILOT_RESULTS__<json>` to stdout for the parent process to parse

### `spicepilot_runner.py` — ngspice Batch Runner

PySpice's built-in simulator modes (shared library, subprocess server `-s`) don't work on Windows. This module provides a drop-in replacement:

- **`BatchSimulator`** — replaces `Circuit.simulator()` via monkey-patching. Supports `.transient()`, `.ac()`, `.dc()`, `.operating_point()`, `.noise()`.
- **`run_ngspice_batch()`** — writes the SPICE netlist to a temp file, runs `ngspice -b -r output.raw input.sp`, reads the ASCII raw file.
- **`parse_ascii_raw()`** — parses ngspice's ASCII output format (the `Variables:` / `Values:` sections). PySpice's built-in parser only handles binary format.
- **`SpicePilotAnalysis`** — result object with `analysis['node_name']`, `analysis.time`, `analysis.frequency` interface — same API as PySpice's native analysis objects so LLM-generated code works unchanged.

### `Pilot_prompt.md` — LLM System Prompt

The system prompt is the brain of the LLM-side. It contains:
- **Section 1**: Setup — required imports, ground node rules, PySpice/ngspice version compatibility
- **Section 2**: Component reference — R, C, L, voltage/current sources, controlled sources, MOSFETs, BJTs, diodes
- **Section 3**: MOSFET model parameters — Level 1/2/3, biasing regions, cascode configurations
- **Section 4**: Circuit templates for 10 families — CMOS digital, sequential logic, analog amplifiers, OTA/op-amp, references, oscillators, power/LDO, mixed-signal, RF, and filters
- **Section 5**: Analysis type selection guide per circuit family
- **Section 6**: Simulation parameter reference (transient, AC, DC, noise)
- **Section 7**: Convergence troubleshooting — GMIN stepping, UIC, tolerance settings
- **Section 8**: Subcircuit/hierarchy patterns
- **Section 9**: Netlist access
- **Section 10**: Plotting best practices (Bode, FFT, eye diagrams)
- **Section 11**: Python keyword conflicts and PySpice quirks (e.g., `lambda_`, plain floats for `.model()` params, `u_fF` not available)

---

## Modifying & Extending

### Improve circuit generation quality
Edit `Pilot_prompt.md`. The LLM will follow it on every request. Good things to add:
- More worked examples for specific circuit families
- Tighter constraints for convergence-prone circuits (oscillators, switching power supplies)
- Company-specific PDK model parameters

### Add a new LLM provider
In `app.py`, add a new function alongside `call_anthropic()` / `call_openai()` and update the `provider` dispatch in `/simulate`. The function signature should be `(api_key, model, user_prompt) -> str`.

### Change the default model
In `app.py`, find the `if not model:` block in `/simulate` and update the defaults. In `templates/index.html`, update the `models` object in the JavaScript config section to add/remove entries in the dropdown.

### Add simulation analysis types
In `spicepilot_runner.py`, add a method to `BatchSimulator` following the existing pattern (build netlist string, call `run_ngspice_batch`). The LLM will use it if you document it in `Pilot_prompt.md`.

### Change the timeout
`run_pyspice_code(code, timeout=90)` in `app.py`. Increase for complex circuits, decrease for faster failure on runaway simulations.

### Run on a server (not just localhost)
In `app.py`, change:
```python
app.run(host='127.0.0.1', port=5001, debug=False)
```
to:
```python
app.run(host='0.0.0.0', port=5001, debug=False)
```
For production, use a WSGI server: `pip install gunicorn && gunicorn -w 4 app:app -b 0.0.0.0:5001`

---

## Benchmarking Framework

The `New_bench-mark.md` file defines 90+ reference circuits across four difficulty tiers:

| Tier | Transistor count | Examples |
|------|-----------------|---------|
| Easy | ≤ 10 | CMOS inverter, current mirror, common-source amp, voltage divider |
| Medium | 11–25 | Differential pair, two-stage op-amp, D flip-flop, bandgap reference |
| Hard | 26–45 | Folded cascode OTA, instrumentation amp, ring oscillator, LDO |
| Extreme | > 45 | Gilbert cell, SAR ADC, switched-cap filter, fully-differential OTA |

Reference outputs from Claude and GPT are in `Claude_tests/` and `GPT_tests/`. To evaluate a model, generate code for each benchmark circuit and check:
1. Does it run without errors?
2. Does the waveform show the expected behavior?
3. Does the analysis type match the circuit?

---

## Troubleshooting

**`ngspice_available: false` in /health**
- Windows: Check that `ngspice.exe` is in one of: `~/ngspice46/Spice64/bin/`, `~/ngspice/Spice64/bin/`, `C:\ngspice\bin\`, or on your `PATH`.
- macOS/Linux: Run `which ngspice` — if not found, install via `brew install ngspice` or `sudo apt-get install ngspice`.

**`ModuleNotFoundError` on startup**
- Make sure you activated the virtualenv before running: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate`
- Re-run `pip install -r requirements.txt`

**Simulation timeout (> 90 seconds)**
- Try a simpler circuit or shorter simulation duration in your prompt
- Oscillators and switching circuits are more likely to time out — ask for fewer cycles

**LLM returns no code block**
- Rephrase your prompt to be more explicit: *"Generate PySpice Python code for..."*
- The response is shown under "Raw response" in the error panel for debugging

**`NameError: name 'u_fF' is not defined`**
- This unit doesn't exist in PySpice 1.5. The preamble defines it as `u_fF = 1e-3 @ u_pF`, so this should be caught automatically. If you see this error, the preamble may not have loaded — check that `spicepilot_runner.py` is in the same directory as `app.py`.

**ngspice `no output produced` / raw file empty**
- The SPICE netlist has a syntax error. Check the **SPICE Netlist** and **Simulation Output** panels for ngspice error messages.
- Common causes: missing `.model` statement, unsupported element syntax, convergence failure on first timestep.

---

## Citation

If you use SPICEPilot in your research, please cite:

```bibtex
@article{vungarala2024spicepilot,
  title={SPICEPilot: Navigating SPICE Code Generation and Simulation with AI Guidance},
  author={Vungarala, Deepak and Alam, Sakila and Ghosh, Arnob and Angizi, Shaahin},
  journal={arXiv preprint arXiv:2410.20553},
  year={2024}
}
```

Paper: [https://arxiv.org/pdf/2410.20553](https://arxiv.org/pdf/2410.20553)

---

## License

MIT License — see [LICENSE](LICENSE) for details.
