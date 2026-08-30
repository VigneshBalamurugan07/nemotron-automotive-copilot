"""
Realistic Automotive Accident Prevention & Emergency Telemetry Scenarios.
Used to inject live telemetry states and demonstrate proactive voice interventions.
"""

from typing import Dict, Any


SCENARIOS: Dict[str, Dict[str, Any]] = {
    "nominal": {
        "id": "nominal",
        "name": "🟢 Nominal Highway Cruising",
        "description": "Standard safe highway driving at 85 km/h with healthy thermals and full traction.",
        "overrides": {
            "speed_kmh": 85.0,
            "brake_pedal_pct": 0.0,
            "brake_line_pressure_bar": 0.0,
            "front_left_brake_temp_c": 190.0,
            "front_right_brake_temp_c": 188.0,
            "battery_max_cell_temp_c": 35.0,
            "battery_temp_gradient_c_s": 0.01,
            "fl_tire_pressure_psi": 33.2,
            "fr_tire_pressure_psi": 33.1,
            "rl_tire_pressure_psi": 33.4,
            "rr_tire_pressure_psi": 33.3,
            "wheel_slip_ratio_fl": 0.02,
            "road_friction_mu": 0.85,
            "forward_obstacle_dist_m": 120.0,
            "time_to_collision_s": 15.0
        }
    },
    "brake_fade": {
        "id": "brake_fade",
        "name": "🔴 Mountain Pass: Severe Brake Fade & Vapor Lock",
        "description": "Downhill descent: Brake pads overheat to 510°C, causing fluid boiling and sudden 60% loss in hydraulic braking pressure.",
        "overrides": {
            "speed_kmh": 78.0,
            "brake_pedal_pct": 75.0,
            "brake_line_pressure_bar": 22.0,  # Abnormally low for 75% pedal depression
            "front_left_brake_temp_c": 512.0,
            "front_right_brake_temp_c": 505.0,
            "rear_left_brake_temp_c": 390.0,
            "rear_right_brake_temp_c": 385.0,
            "longitudinal_g": -0.15,
            "drive_mode": "Sport"
        }
    },
    "thermal_runaway": {
        "id": "thermal_runaway",
        "name": "🔥 EV Battery: Thermal Runaway & Rapid Heat Spike",
        "description": "High-voltage lithium-ion pack cell temperature spikes to 62°C with dangerous 1.8°C/s rate of rise.",
        "overrides": {
            "speed_kmh": 65.0,
            "battery_max_cell_temp_c": 62.4,
            "battery_temp_gradient_c_s": 1.85,
            "battery_soc_pct": 52.0,
            "inverter_temp_c": 78.0,
            "battery_current_a": 140.0
        }
    },
    "black_ice": {
        "id": "black_ice",
        "name": "❄️ Winter Road: Black Ice & Hydroplaning Traction Loss",
        "description": "Vehicle hits unseen black ice at 92 km/h; road friction drops to μ=0.18 with front wheel slip ratio jumping to 0.42.",
        "overrides": {
            "speed_kmh": 92.0,
            "road_friction_mu": 0.18,
            "wheel_slip_ratio_fl": 0.42,
            "wheel_slip_ratio_fr": 0.39,
            "yaw_rate_deg_s": 4.2,
            "lateral_g": 0.28,
            "ambient_temp_c": -2.0
        }
    },
    "tire_blowout": {
        "id": "tire_blowout",
        "name": "⚠️ High-Speed: Front-Left Tire Rapid Depressurization",
        "description": "Debris on highway punctures Front-Left tire; pressure drops catastrophically to 16.5 PSI at 105 km/h.",
        "overrides": {
            "speed_kmh": 105.0,
            "fl_tire_pressure_psi": 16.5,
            "fr_tire_pressure_psi": 33.0,
            "rl_tire_pressure_psi": 33.2,
            "rr_tire_pressure_psi": 33.1,
            "steering_angle_deg": -6.5,  # Driver counter-steering against pull
            "yaw_rate_deg_s": 1.8
        }
    },
    "forward_collision": {
        "id": "forward_collision",
        "name": "🚨 ADAS Emergency: Stalled Truck (TTC < 1.8s)",
        "description": "Vehicle approaches stalled vehicle around blind bend; obstacle distance shrinks to 18m with Time-to-Collision of 1.2s.",
        "overrides": {
            "speed_kmh": 82.0,
            "forward_obstacle_dist_m": 18.2,
            "time_to_collision_s": 1.2,
            "throttle_pct": 20.0
        }
    }
}
