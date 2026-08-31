"""
Application Configuration and Automotive Thresholds
"""

import os
from dataclasses import dataclass

# Safe optional load_dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass(frozen=True)
class SafetyThresholds:
    """Critical physics thresholds for proactive safety interjections."""
    # Braking system
    MAX_BRAKE_PAD_TEMP_C: float = 450.0       # Brake fade risk > 450°C
    MIN_BRAKE_LINE_PRESSURE_BAR: float = 35.0 # Normal hard braking is 60-90 bar
    BRAKE_PRESSURE_DROP_WARN_PCT: float = 30.0

    # EV Battery System
    MAX_BATTERY_CELL_TEMP_C: float = 55.0     # Critical thermal threshold
    MAX_THERMAL_GRADIENT_C_PER_SEC: float = 1.2 # Rapid heat rise
    MIN_STATE_OF_CHARGE_WARN_PCT: float = 8.0

    # Tires and Dynamics
    MIN_TIRE_PRESSURE_PSI: float = 26.0       # Dangerously low pressure
    MAX_TIRE_PRESSURE_PSI: float = 44.0       # Over-inflation / blowout risk
    MAX_TIRE_SLIP_RATIO_WARN: float = 0.25    # Hydroplaning / ice threshold (>25% slip)
    LOW_ROAD_FRICTION_MU: float = 0.35        # Wet/Icy road threshold

    # ADAS & Distance
    MIN_TIME_TO_COLLISION_SEC: float = 2.4    # Critical TTC threshold
    FORWARD_COLLISION_WARN_METERS: float = 25.0


@dataclass
class AppConfig:
    """General configuration for NemoDrive-AI."""
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    nvidia_base_url: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    # Latest active NVIDIA Nemotron generation on build.nvidia.com
    model_name: str = os.getenv("NEMOTRON_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
    enable_voice_tts: bool = os.getenv("ENABLE_VOICE_TTS", "true").lower() == "true"
    voice_language: str = os.getenv("VOICE_LANGUAGE", "en")
    safety: SafetyThresholds = SafetyThresholds()


config = AppConfig()
