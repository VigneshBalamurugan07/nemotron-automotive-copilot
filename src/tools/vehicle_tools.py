"""
Automotive Physics & Telemetry Diagnostic Tools for NVIDIA Nemotron Agent.
"""

import math
from typing import Dict, Any
from src.telemetry.can_bus import VehicleTelemetry


def calculate_stopping_distance(speed_kmh: float, road_friction_mu: float, driver_reaction_time_s: float = 1.0) -> Dict[str, Any]:
    """
    Calculates the theoretical stopping distance based on Newtonian vehicle dynamics.
    Formula: d_stop = d_reaction + d_braking = (v * t_rxn) + (v^2 / (2 * mu * g))
    """
    v_ms = speed_kmh / 3.6
    g = 9.81
    mu = max(0.05, min(1.2, road_friction_mu))

    reaction_dist_m = v_ms * driver_reaction_time_s
    braking_dist_m = (v_ms ** 2) / (2 * mu * g)
    total_dist_m = reaction_dist_m + braking_dist_m

    return {
        "speed_kmh": speed_kmh,
        "road_friction_mu": mu,
        "road_condition": "Dry Asphalt" if mu > 0.7 else "Wet Road" if mu > 0.4 else "Icy / Snow Surface",
        "reaction_distance_meters": round(reaction_dist_m, 2),
        "braking_distance_meters": round(braking_dist_m, 2),
        "total_stopping_distance_meters": round(total_dist_m, 2),
        "safe_following_gap_recommendation_meters": round(total_dist_m * 1.25, 2)
    }


def diagnose_subsystem_health(telemetry: VehicleTelemetry) -> Dict[str, Any]:
    """
    Performs multi-point subsystem health evaluation across Brakes, Battery, Tires, and ADAS.
    """
    # 1. Braking
    max_brake_temp = max(telemetry.front_left_brake_temp_c, telemetry.front_right_brake_temp_c)
    brake_status = "CRITICAL (Overheating / Fade Risk)" if max_brake_temp > 450 else "ELEVATED" if max_brake_temp > 300 else "HEALTHY"

    # 2. Battery
    battery_status = "CRITICAL (Thermal Runaway Risk)" if telemetry.battery_max_cell_temp_c > 55 or telemetry.battery_temp_gradient_c_s > 1.2 else "NOMINAL"

    # 3. Tires & Traction
    min_psi = min(telemetry.fl_tire_pressure_psi, telemetry.fr_tire_pressure_psi, telemetry.rl_tire_pressure_psi, telemetry.rr_tire_pressure_psi)
    tire_status = "WARNING (Low Pressure)" if min_psi < 26 else "NOMINAL"
    traction_status = "CRITICAL (Hydroplaning / Slip)" if telemetry.wheel_slip_ratio_fl > 0.25 else "NORMAL"

    # 4. Overall Safety Index (0 to 100)
    safety_score = 100
    if brake_status.startswith("CRITICAL"):
        safety_score -= 40
    if battery_status.startswith("CRITICAL"):
        safety_score -= 45
    if traction_status.startswith("CRITICAL"):
        safety_score -= 30
    if tire_status.startswith("WARNING"):
        safety_score -= 15
    safety_score = max(0, safety_score)

    return {
        "overall_safety_index": safety_score,
        "braking_subsystem": {
            "status": brake_status,
            "max_pad_temp_c": max_brake_temp,
            "line_pressure_bar": telemetry.brake_line_pressure_bar
        },
        "ev_battery_subsystem": {
            "status": battery_status,
            "max_cell_temp_c": telemetry.battery_max_cell_temp_c,
            "thermal_gradient_c_s": telemetry.battery_temp_gradient_c_s,
            "state_of_charge_pct": telemetry.battery_soc_pct
        },
        "tires_and_traction": {
            "tire_pressure_status": tire_status,
            "min_psi_observed": min_psi,
            "traction_status": traction_status,
            "road_friction_mu": telemetry.road_friction_mu
        },
        "adas_status": {
            "time_to_collision_s": telemetry.time_to_collision_s,
            "forward_obstacle_m": telemetry.forward_obstacle_dist_m
        }
    }
