"""
NemoDrive-AI: In-Cabin Proactive Safety & Accident Prevention Voice Copilot
Powered by NVIDIA Nemotron (nvidia/llama-3.1-nemotron-70b-instruct)
"""

import time
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from src.config import config
from src.telemetry.can_bus import CANBusSimulator, VehicleTelemetry
from src.telemetry.hazard_detector import HazardDetector
from src.agent.orchestrator import AgentOrchestrator
from src.scenarios.hazard_scenarios import SCENARIOS
from src.voice.tts_engine import TTSEngine

# Set Streamlit Page Config
st.set_page_config(
    page_title="NemoDrive-AI | NVIDIA Nemotron Voice Copilot",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Cyber-Cockpit CSS Theme
st.markdown("""
<style>
    /* Dark Cyber-Cockpit Aesthetic */
    .stApp {
        background-color: #070B14;
        color: #E2E8F0;
    }
    
    /* Header styling */
    .hud-title {
        font-family: 'Inter', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #76B900 0%, #00F0FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .hud-subtitle {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-bottom: 15px;
    }

    /* Gauge / Metric Cards */
    .hud-card {
        background: #0E1626;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .hud-metric-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        color: #64748B;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .hud-metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .hud-metric-unit {
        font-size: 0.85rem;
        color: #76B900;
        margin-left: 4px;
    }

    /* Emergency Alert Banner */
    .emergency-banner {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(185, 28, 28, 0.35) 100%);
        border: 2px solid #EF4444;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 20px;
        animation: pulse-glow 2s infinite ease-in-out;
    }
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); }
        50% { box-shadow: 0 0 30px rgba(239, 68, 68, 0.8); }
    }

    /* Chat styling */
    .chat-bubble-user {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
        border-left: 4px solid #00F0FF;
    }
    .chat-bubble-ai {
        background-color: #0E1E2E;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
        border-left: 4px solid #76B900;
    }
    .chat-bubble-alert {
        background-color: #2D151B;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
        border-left: 4px solid #EF4444;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "can_simulator" not in st.session_state:
    st.session_state.can_simulator = CANBusSimulator()
if "hazard_detector" not in st.session_state:
    st.session_state.hazard_detector = HazardDetector()
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AgentOrchestrator(
        st.session_state.can_simulator,
        st.session_state.hazard_detector
    )
if "tts_engine" not in st.session_state:
    st.session_state.tts_engine = TTSEngine()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "telemetry_history" not in st.session_state:
    st.session_state.telemetry_history = []
if "active_scenario" not in st.session_state:
    st.session_state.active_scenario = "nominal"
if "latest_audio_html" not in st.session_state:
    st.session_state.latest_audio_html = ""


# Update simulation state tick
current_telemetry = st.session_state.can_simulator.step()

# Keep last 30 telemetry points for live plotting
st.session_state.telemetry_history.append({
    "time": time.strftime("%H:%M:%S"),
    "speed": current_telemetry.speed_kmh,
    "fl_brake_temp": current_telemetry.front_left_brake_temp_c,
    "battery_temp": current_telemetry.battery_max_cell_temp_c,
    "friction": current_telemetry.road_friction_mu,
    "line_pressure": current_telemetry.brake_line_pressure_bar
})
if len(st.session_state.telemetry_history) > 30:
    st.session_state.telemetry_history.pop(0)

# Evaluate for proactive hazard
proactive_alert = st.session_state.orchestrator.check_and_generate_proactive_alert()
if proactive_alert:
    audio_tag = st.session_state.tts_engine.get_audio_html_tag(proactive_alert["spoken_warning"], auto_play=True)
    st.session_state.latest_audio_html = audio_tag
    st.session_state.chat_history.append({
        "role": "alert",
        "title": proactive_alert["alert"].title,
        "content": proactive_alert["spoken_warning"],
        "audio_html": audio_tag,
        "tools": proactive_alert.get("tool_calls", [])
    })


# -----------------------------------------------------------------------------
# SIDEBAR: Cockpit Controls & Scenario Injection
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1617814076367-b759c7d7e738?w=600&auto=format&fit=crop&q=80", use_container_width=True)
    
    st.markdown("### 🏎️ **NemoDrive Scenario Injector**")
    st.caption("Simulate critical vehicle hazards in real time:")

    for sc_key, sc in SCENARIOS.items():
        is_current = (st.session_state.active_scenario == sc_key)
        btn_type = "primary" if is_current else "secondary"
        if st.button(sc["name"], key=f"btn_{sc_key}", use_container_width=True, type=btn_type):
            st.session_state.active_scenario = sc_key
            if sc_key == "nominal":
                st.session_state.can_simulator.clear_overrides()
            else:
                st.session_state.can_simulator.inject_override(sc["overrides"])
            st.rerun()

    st.markdown("---")
    st.markdown("### 🧠 **AI Intelligence Core**")
    st.markdown("""
    <div style="background: #0E1626; border: 1px solid #76B900; border-radius: 8px; padding: 10px;">
        <div style="color: #76B900; font-weight: 700; font-size: 0.88rem;">NVIDIA Llama-3.1-Nemotron-70B</div>
        <div style="color: #94A3B8; font-size: 0.78rem;">Deep Reasoning & Multi-Step Tool Calling</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"**Endpoint:** `build.nvidia.com (NIM)`")
    api_status = "🟢 Connected (Live API)" if config.nvidia_api_key and config.nvidia_api_key != "your_nvidia_api_key_here" else "🟡 High-Fidelity Physics Engine Active"
    st.markdown(f"**Status:** {api_status}")
    st.markdown(f"**Voice TTS:** `Enabled (English)`")
    
    if st.button("🔄 Clear Chat & Telemetry Log", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.can_simulator.clear_overrides()
        st.session_state.active_scenario = "nominal"
        st.session_state.latest_audio_html = ""
        st.rerun()


# -----------------------------------------------------------------------------
# MAIN VIEW: Cockpit HUD & Telemetry Dashboard
# -----------------------------------------------------------------------------

col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.markdown('<p class="hud-title">NemoDrive-AI Cockpit</p>', unsafe_allow_html=True)
    st.markdown('<p class="hud-subtitle">In-Cabin Safety & Accident Prevention Copilot powered by NVIDIA Nemotron-70B</p>', unsafe_allow_html=True)
with col_header2:
    st.markdown(f"""
    <div style="text-align: right; padding-top: 10px;">
        <span style="background: rgba(118, 185, 0, 0.2); border: 1px solid #76B900; color: #76B900; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 0.85rem;">
            ● VSS CAN STREAM ACTIVE
        </span>
    </div>
    """, unsafe_allow_html=True)

# Personalized Driver Greeting Banner
st.markdown("""
<div style="background: linear-gradient(90deg, rgba(14, 22, 38, 0.9) 0%, rgba(14, 30, 46, 0.9) 100%); border-left: 4px solid #76B900; border-radius: 8px; padding: 10px 16px; margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between;">
    <div>
        <span style="color: #76B900; font-weight: 700; font-size: 0.95rem;">👋 Welcome, Driver Vignesh Balamurugan!</span>
        <span style="color: #94A3B8; font-size: 0.85rem; margin-left: 8px;">NemoDrive Safety Shield is online. Have a safe and smooth drive! 🛡️✨</span>
    </div>
    <div style="color: #00F0FF; font-size: 0.8rem; font-weight: 600;">
        🌤️ Clear Highway • Physics Guardrails Nominal
    </div>
</div>
""", unsafe_allow_html=True)


# Show Active Proactive Hazard Banner if alert exists
active_hazards = st.session_state.hazard_detector.active_alerts
if active_hazards:
    h = active_hazards[0]
    st.markdown(f"""
    <div class="emergency-banner">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <span style="background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 800;">
                    {h.severity} HAZARD
                </span>
                <span style="color: #F8FAFC; font-weight: 800; font-size: 1.2rem; margin-left: 10px;">
                    {h.title}
                </span>
            </div>
            <span style="color: #FCA5A5; font-size: 0.85rem; font-weight: 600;">{h.hazard_code}</span>
        </div>
        <p style="margin: 8px 0 4px 0; color: #FEE2E2; font-size: 0.95rem;"><strong>Trigger:</strong> {h.description}</p>
        <p style="margin: 0; color: #FEF08A; font-size: 0.95rem;"><strong>Immediate Action:</strong> {h.recommended_action}</p>
    </div>
    """, unsafe_allow_html=True)


# Audio Output for Latest Spoken Warning
if st.session_state.latest_audio_html:
    st.markdown("🔊 **Voice Interjection Speaker (Nemotron TTS):**")
    st.components.v1.html(st.session_state.latest_audio_html, height=50)


# Telemetry Gauges Grid
c1, c2, c3, c4 = st.columns(4)

with c1:
    speed_color = "#76B900" if current_telemetry.speed_kmh < 120 else "#EF4444"
    st.markdown(f"""
    <div class="hud-card">
        <div class="hud-metric-label">Vehicle Velocity</div>
        <div class="hud-metric-value" style="color: {speed_color};">{current_telemetry.speed_kmh}<span class="hud-metric-unit">km/h</span></div>
        <div style="font-size: 0.8rem; color: #94A3B8;">RPM: {int(current_telemetry.motor_rpm)} | Mode: {current_telemetry.drive_mode}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    brake_color = "#EF4444" if current_telemetry.front_left_brake_temp_c > 450 else "#F59E0B" if current_telemetry.front_left_brake_temp_c > 300 else "#00F0FF"
    st.markdown(f"""
    <div class="hud-card">
        <div class="hud-metric-label">FL Brake Pad Temp</div>
        <div class="hud-metric-value" style="color: {brake_color};">{current_telemetry.front_left_brake_temp_c}<span class="hud-metric-unit">°C</span></div>
        <div style="font-size: 0.8rem; color: #94A3B8;">Line Press: {current_telemetry.brake_line_pressure_bar} bar | Pedal: {current_telemetry.brake_pedal_pct}%</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    batt_color = "#EF4444" if current_telemetry.battery_max_cell_temp_c > 55 else "#76B900"
    st.markdown(f"""
    <div class="hud-card">
        <div class="hud-metric-label">EV Battery Cell Temp</div>
        <div class="hud-metric-value" style="color: {batt_color};">{current_telemetry.battery_max_cell_temp_c}<span class="hud-metric-unit">°C</span></div>
        <div style="font-size: 0.8rem; color: #94A3B8;">SoC: {current_telemetry.battery_soc_pct}% | dT/dt: {current_telemetry.battery_temp_gradient_c_s}°C/s</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    grip_color = "#EF4444" if current_telemetry.road_friction_mu < 0.35 else "#76B900"
    st.markdown(f"""
    <div class="hud-card">
        <div class="hud-metric-label">Road Grip (μ) & Tires</div>
        <div class="hud-metric-value" style="color: {grip_color};">μ {current_telemetry.road_friction_mu}<span class="hud-metric-unit">FL: {current_telemetry.fl_tire_pressure_psi} psi</span></div>
        <div style="font-size: 0.8rem; color: #94A3B8;">Slip: {current_telemetry.wheel_slip_ratio_fl:.2f} | TTC: {current_telemetry.time_to_collision_s}s</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# TWO COLUMNS: LIVE CHARTS vs VOICE COPILOT INTERACTION
# -----------------------------------------------------------------------------
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("### 📊 **Live Telemetry Streams (VSS)**")
    
    if st.session_state.telemetry_history:
        df = pd.DataFrame(st.session_state.telemetry_history)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["time"], y=df["speed"], mode="lines+markers", name="Speed (km/h)", line=dict(color="#76B900", width=2)))
        fig.add_trace(go.Scatter(x=df["time"], y=df["fl_brake_temp"], mode="lines", name="FL Brake Temp (°C)", line=dict(color="#EF4444", width=2)))
        fig.add_trace(go.Scatter(x=df["time"], y=df["battery_temp"], mode="lines", name="Battery Temp (°C)", line=dict(color="#F59E0B", width=2)))
        fig.add_trace(go.Scatter(x=df["time"], y=df["line_pressure"], mode="lines", name="Brake Press (bar)", line=dict(color="#00F0FF", dash="dot")))
        
        fig.update_layout(
            paper_bgcolor="#0E1626",
            plot_bgcolor="#0B111E",
            font=dict(color="#94A3B8"),
            height=290,
            margin=dict(l=10, r=10, t=25, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Quick Telemetry Matrix
    st.markdown("#### 🔍 **Individual Tire & ADAS Matrix**")
    t_c1, t_c2, t_c3, t_c4 = st.columns(4)
    t_c1.metric("Front-Left Tire", f"{current_telemetry.fl_tire_pressure_psi} PSI")
    t_c2.metric("Front-Right Tire", f"{current_telemetry.fr_tire_pressure_psi} PSI")
    t_c3.metric("Rear-Left Tire", f"{current_telemetry.rl_tire_pressure_psi} PSI")
    t_c4.metric("Rear-Right Tire", f"{current_telemetry.rr_tire_pressure_psi} PSI")


with col_right:
    st.markdown("### 🎙️ **NemoDrive In-Cabin Voice Assistant**")
    st.caption("Talk to your Nemotron-70B copilot using quick voice commands or custom questions:")

    # Quick Voice Command Buttons
    q_col1, q_col2 = st.columns(2)
    with q_col1:
        if st.button("🛑 Calculate Stopping Distance", use_container_width=True):
            user_q = "Calculate my theoretical stopping distance and safe gap at current speed and road grip."
            res = st.session_state.orchestrator.process_driver_query(user_q)
            audio = st.session_state.tts_engine.get_audio_html_tag(res["response"], auto_play=True)
            st.session_state.latest_audio_html = audio
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            st.session_state.chat_history.append({"role": "ai", "content": res["response"], "tools": res["tool_calls"], "audio_html": audio})
            st.rerun()

        if st.button("🌡️ Check Brake & Battery Health", use_container_width=True):
            user_q = "Run a comprehensive health diagnostic on my brakes, battery pack, and tires."
            res = st.session_state.orchestrator.process_driver_query(user_q)
            audio = st.session_state.tts_engine.get_audio_html_tag(res["response"], auto_play=True)
            st.session_state.latest_audio_html = audio
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            st.session_state.chat_history.append({"role": "ai", "content": res["response"], "tools": res["tool_calls"], "audio_html": audio})
            st.rerun()

    with q_col2:
        if st.button("🛡️ Emergency Recovery Protocol", use_container_width=True):
            user_q = "What is the emergency safety protocol if I experience severe brake fade or hydraulic loss?"
            res = st.session_state.orchestrator.process_driver_query(user_q)
            audio = st.session_state.tts_engine.get_audio_html_tag(res["response"], auto_play=True)
            st.session_state.latest_audio_html = audio
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            st.session_state.chat_history.append({"role": "ai", "content": res["response"], "tools": res["tool_calls"], "audio_html": audio})
            st.rerun()

        if st.button("⚡ Trigger EV Limp-Home Mode", use_container_width=True):
            user_q = "Engage EV safety limp mode to protect the vehicle powertrain."
            res = st.session_state.orchestrator.process_driver_query(user_q)
            audio = st.session_state.tts_engine.get_audio_html_tag(res["response"], auto_play=True)
            st.session_state.latest_audio_html = audio
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            st.session_state.chat_history.append({"role": "ai", "content": res["response"], "tools": res["tool_calls"], "audio_html": audio})
            st.rerun()

    # Driver Text/Speech Input
    user_input = st.chat_input("Speak or ask your Nemotron Voice Copilot (e.g. 'How is my traction?', 'Check brake pressure')...")
    if user_input:
        res = st.session_state.orchestrator.process_driver_query(user_input)
        audio = st.session_state.tts_engine.get_audio_html_tag(res["response"], auto_play=True)
        st.session_state.latest_audio_html = audio
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({
            "role": "ai",
            "content": res["response"],
            "tools": res["tool_calls"],
            "audio_html": audio
        })
        st.rerun()

    # Chat Transcript Container
    st.markdown("#### 💬 **Conversation & Interjection Log**")
    chat_container = st.container(height=280)
    with chat_container:
        if not st.session_state.chat_history:
            st.caption("No queries yet. Click a quick command button above or type a question to interact.")
        for msg in reversed(st.session_state.chat_history):
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-bubble-user"><strong>Driver:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
            elif msg["role"] == "alert":
                st.markdown(f'<div class="chat-bubble-alert"><strong>🚨 NemoDrive Proactive Alert ({msg.get("title", "")}):</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble-ai"><strong>🏎️ NemoDrive Copilot:</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
                if msg.get("tools"):
                    with st.expander("🛠️ Nemotron Tool Calls Executed", expanded=False):
                        st.json(msg["tools"])
