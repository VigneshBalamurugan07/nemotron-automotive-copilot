# 🏎️ NemoDrive-AI: In-Cabin Proactive Safety & Accident Prevention Copilot
### *Powered by NVIDIA Nemotron (`nvidia/llama-3.1-nemotron-70b-instruct` / NIM) & Real-Time CAN-Bus Telemetry*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![NVIDIA Nemotron](https://img.shields.io/badge/NVIDIA-Nemotron--70B-76B900.svg)](https://build.nvidia.com)
[![VSS Telemetry](https://img.shields.io/badge/COVESA-VSS%20Compliant-00F0FF.svg)](https://covesa.global/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Executive Summary & Industry Problem

In modern Software-Defined Vehicles (SDVs), **over 60% of drivers ignore or disable traditional warning beeps** due to *Alert Fatigue*—cryptic dashboard lights (like "Check Engine" or amber ABS icons) fail to convey **root cause, urgency, or life-saving recovery instructions** until catastrophic failure or accidents occur.

**NemoDrive-AI** bridges the critical gap between raw vehicle sensor streams and human-safe decision making. It continuously ingests **18+ CAN-bus telemetry metrics** (brake pad thermals, hydraulic line pressure, wheel slip ratios, EV battery cell temperature gradients $\Delta T / \Delta t$, road friction $\mu$, and ADAS Time-to-Collision), applies deterministic physics guardrails, and deploys **NVIDIA Nemotron's deep multi-step reasoning** to proactively intervene with **urgent spoken voice alerts** before accidents happen.

```
                      ┌──────────────────────────────────────────┐
                      │        NemoDrive Cyber-Cockpit UI        │
                      │  - Live Telemetry Gauges & HUD Visualizer│
                      │  - Scenario Injector (Brake Fade, Ice..) │
                      │  - Voice Mic & TTS Audio Speaker         │
                      └────────────────────▲─────────────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
         ┌──────────────────────────────┐     ┌──────────────────────────────┐
         │    CAN-Bus Telemetry Stream  │     │      Audio Voice Pipeline    │
         │  - 18+ Live Vehicle Signals  │     │  - Speech-to-Text (STT)      │
         │  - Hazard Anomaly Detector   │     │  - Text-to-Speech (TTS)      │
         └──────────────┬───────────────┘     └──────────────┬───────────────┘
                        │                                    │
                        ▼                                    ▼
         ┌───────────────────────────────────────────────────────────────────┐
         │                    NemoDrive Agent Orchestrator                   │
         │  - Priority Arbiter (User Voice vs Proactive Hazard Alert)        │
         │  - Automotive Safety Tool Registry                                │
         └─────────────────────────────────┬─────────────────────────────────┘
                                           │
                                           ▼
         ┌───────────────────────────────────────────────────────────────────┐
         │                  NVIDIA Nemotron Reasoning Core                   │
         │  - Model: nvidia/llama-3.1-nemotron-70b-instruct / Nemotron-NIM   │
         │  - Multi-step Physics & Telemetry Diagnostic Reasoning            │
         └───────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Features

- 🏎️ **Proactive Voice Interventions (Accident Prevention)**: Unlike passive chatbots, NemoDrive-AI monitors the CAN stream in real-time and actively interrupts the driver with authoritative voice guidance when hazardous conditions emerge (e.g. Brake Fade downhill, EV Thermal Runaway, Black Ice).
- 🧠 **NVIDIA Nemotron Reasoning Engine**: Leverages `nvidia/llama-3.1-nemotron-70b-instruct` via NVIDIA NIM for multi-step physics correlation and tool-calling.
- 📡 **VSS-Compliant CAN-Bus Telemetry**: 18+ live signals across Vehicle Dynamics, Braking, EV Battery Pack, Tires, and ADAS.
- 🛠️ **Automotive Physics Tool Registry**:
  - `calculate_stopping_distance(speed_kmh, road_friction_mu)`: Calculates Newtonian stopping distance $d = v \cdot t_{\text{rxn}} + \frac{v^2}{2 \mu g}$.
  - `diagnose_subsystem_health()`: Multi-point safety index scoring across Brakes, EV Pack, and Tires.
  - `get_accident_prevention_procedure(hazard_code)`: Retrieves ISO/SAE recovery procedures.
  - `trigger_ev_safety_limp_mode()`: Caps speed and enables maximum regenerative braking.
- 🎛️ **Cyber-Cockpit HUD**: Futuristic dark-themed Streamlit dashboard with real-time Plotly strip charts, live gauges, emergency scenario injectors, and voice audio players.
- 🔌 **Zero-Setup Resilience**: Works out of the box with live NVIDIA NIM API or with built-in high-fidelity physics fallback simulation.

---

## 📂 Project Architecture

```
Nemotron/
├── .env.example                     # NVIDIA NIM API key & model settings
├── .gitignore                       # Clean repository exclusions
├── pyproject.toml                   # uv-compliant dependencies
├── README.md                        # Portfolio-grade documentation
├── app.py                           # Cyber-Cockpit Streamlit HUD & Voice Dashboard
├── src/
│   ├── config.py                    # App settings & automotive safety thresholds
│   ├── agent/
│   │   ├── nemotron_client.py       # NVIDIA NIM API & tool-calling integration
│   │   ├── prompts.py               # Automotive safety copilot instructions
│   │   └── orchestrator.py          # Priority arbiter & proactive dispatch loop
│   ├── telemetry/
│   │   ├── can_bus.py               # Simulated 18-signal CAN-bus stream
│   │   └── hazard_detector.py       # Physics anomaly rules (Brake Fade, Ice, etc.)
│   ├── tools/
│   │   ├── vehicle_tools.py         # Newtonian physics & diagnostic health tools
│   │   └── emergency_tools.py       # Emergency protocols & EV limp-mode triggers
│   ├── scenarios/
│   │   └── hazard_scenarios.py      # Real-world hazard injectors
│   └── voice/
│       └── tts_engine.py            # Text-to-Speech audio synthesis
└── tests/
    └── test_telemetry_and_agent.py  # Comprehensive test suite
```

---

## 🚦 Quickstart Guide

### 1. Clone & Install with `uv`
```bash
# Clone the repository
git clone https://github.com/your-username/nemodrive-ai.git
cd nemodrive-ai

# Install dependencies using uv (or standard pip)
uv sync
```

### 2. Configure Environment (Optional for Live NVIDIA NIM)
```bash
cp .env.example .env
```
Add your free NVIDIA API Key from [build.nvidia.com](https://build.nvidia.com):
```env
NVIDIA_API_KEY=nvapi-your-key-here
NEMOTRON_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
```
*(Note: If no API key is provided, NemoDrive-AI runs seamlessly using its built-in high-fidelity physics reasoning engine!)*

### 3. Launch the Cyber-Cockpit Dashboard
```bash
uv run streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧪 Injectable Real-World Scenarios

| Scenario | Injected Anomaly | Proactive Spoken Action |
| :--- | :--- | :--- |
| **🔴 Mountain Brake Fade** | Pad Temp > 510°C, Line Pressure drop to 22 bar (pedal at 75%) | *"Downshift immediately to engine braking. Do not pump spongy pedal."* |
| **🔥 EV Thermal Runaway** | Cell Temp 62.4°C with gradient $1.85^\circ\text{C/s}$ | *"Pull over to shoulder immediately, power down HV system, and evacuate 30m."* |
| **❄️ Black Ice / Hydroplaning** | Friction $\mu=0.18$, Slip Ratio 0.42 at 92 km/h | *"Ease off accelerator gently. Hold steering straight; avoid abrupt braking."* |
| **⚠️ High-Speed Tire Blowout** | Front-Left pressure drops to 16.5 PSI at 105 km/h | *"Grip wheel firmly at 9 and 3. Maintain slight throttle to counter yaw pull."* |
| **🚨 Forward Collision Risk** | Stalled obstacle at 18m, TTC 1.2s at 82 km/h | *"Apply maximum brake pressure immediately. AEB emergency override."* |

---

## 💼 LinkedIn Showcase Post Template

Ready to share your project on LinkedIn? Here is a crafted post template:

```markdown
🚀 Excited to introduce NemoDrive-AI — an In-Cabin Proactive Safety & Accident Prevention Copilot powered by NVIDIA Nemotron! 🏎️⚡

Did you know that over 60% of drivers ignore traditional dashboard warning lights due to "alert fatigue"? When critical mechanical failures occur (like brake fade on mountain roads or battery thermal runaway in EVs), generic amber lights fail to convey root cause or life-saving recovery steps.

To solve this, I built NemoDrive-AI:
✅ Ingests 18+ high-frequency CAN-bus telemetry signals (VSS-compliant)
✅ Uses NVIDIA's Llama-3.1-Nemotron-70B for deep physics-grounded multi-step reasoning
✅ Implements Proactive Voice Interventions that actively speak emergency recovery steps before accidents occur
✅ Built with modern Python tooling (uv, Streamlit Cyber-Cockpit HUD, Plotly live strip charts)

Check out the full open-source repo and interactive demo on GitHub! 👇
🔗 https://github.com/your-username/nemodrive-ai

#NVIDIA #Nemotron #GenerativeAI #Automotive #AutonomousVehicles #AI #Python #MachineLearning #SmartMobility #GenAI
```

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
