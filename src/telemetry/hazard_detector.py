"""
Real-time Physics Anomaly & Hazard Detector for In-Cabin Accident Prevention.
Continuously analyzes CAN-bus metrics to detect imminent vehicle dynamics & mechanical hazards.
"""

from dataclasses import dataclass
from typing import List, Optional
from src.config import config
from src.telemetry.can_bus import VehicleTelemetry


@dataclass
class HazardAlert:
    severity: str               # "CRITICAL", "WARNING", "INFO"
    hazard_code: str            # Unique identifier e.g. "HAZARD_BRAKE_FADE"
    title: str                  # Short title e.g. "Severe Brake Fade Detected"
    description: str            # Detailed physics-backed description
    recommended_action: str     # Immediate driver guidance
    metrics_snapshot: dict      # Crucial telemetry values triggering alert


class HazardDetector:
    """
    Evaluates telemetry against automotive physics rules & dynamic gradients.
    Triggers structured HazardAlerts when safety boundaries are violated.
    """

    def __init__(self):
        self.active_alerts: List[HazardAlert] = []

    def evaluate(self, t: VehicleTelemetry) -> List[HazardAlert]:
        alerts: List[HazardAlert] = []
        thresh = config.safety

        # 1. Severe Brake Fade / Vapor Lock Hazard
        # Condition: High pad temp (>450°C) AND brake pedal depressed (>40%) BUT low line pressure (<35 bar)
        if t.front_left_brake_temp_c > thresh.MAX_BRAKE_PAD_TEMP_C or t.front_right_brake_temp_c > thresh.MAX_BRAKE_PAD_TEMP_C:
            if t.brake_pedal_pct > 30.0 and t.brake_line_pressure_bar < thresh.MIN_BRAKE_LINE_PRESSURE_BAR:
                alerts.append(HazardAlert(
                    severity="CRITICAL",
                    hazard_code="HAZARD_BRAKE_FADE",
                    title="Severe Brake Fade & Hydraulic Pressure Loss",
                    description=(
                        f"Front brake pad temp reached {t.front_left_brake_temp_c}°C with hydraulic pressure "
                        f"decaying to {t.brake_line_pressure_bar} bar despite {t.brake_pedal_pct}% pedal depression."
                    ),
                    recommended_action="Downshift immediately to use regenerative/engine braking. Do not pump brakes. Seek emergency runoff if pedal is spongy.",
                    metrics_snapshot={
                        "brake_temp_fl": t.front_left_brake_temp_c,
                        "brake_pressure_bar": t.brake_line_pressure_bar,
                        "pedal_pct": t.brake_pedal_pct
                    }
                ))

        # 2. EV Battery Thermal Runaway / Rapid Gradient Spike
        if t.battery_max_cell_temp_c > thresh.MAX_BATTERY_CELL_TEMP_C or t.battery_temp_gradient_c_s > thresh.MAX_THERMAL_GRADIENT_C_PER_SEC:
            alerts.append(HazardAlert(
                severity="CRITICAL",
                hazard_code="HAZARD_BATTERY_THERMAL_RUNAWAY",
                title="EV Battery Thermal Runaway Risk",
                description=(
                    f"Battery cell maximum temperature is {t.battery_max_cell_temp_c}°C with critical "
                    f"thermal rise gradient of {t.battery_temp_gradient_c_s}°C/s."
                ),
                recommended_action="Safely pull over to the shoulder immediately, power off the high-voltage system, and exit the vehicle to a safe distance.",
                metrics_snapshot={
                    "max_cell_temp_c": t.battery_max_cell_temp_c,
                    "temp_gradient_c_s": t.battery_temp_gradient_c_s,
                    "battery_soc_pct": t.battery_soc_pct
                }
            ))

        # 3. Dynamic Hydroplaning / Black Ice Traction Loss
        if (t.wheel_slip_ratio_fl > thresh.MAX_TIRE_SLIP_RATIO_WARN or t.wheel_slip_ratio_fr > thresh.MAX_TIRE_SLIP_RATIO_WARN) and t.road_friction_mu < thresh.LOW_ROAD_FRICTION_MU:
            alerts.append(HazardAlert(
                severity="CRITICAL",
                hazard_code="HAZARD_TRACTION_LOSS_ICE",
                title="Black Ice / Hydroplaning Traction Loss",
                description=(
                    f"Road surface friction coefficient dropped to μ={t.road_friction_mu} with front wheel slip "
                    f"ratio spiking to {t.wheel_slip_ratio_fl:.2f} at {t.speed_kmh} km/h."
                ),
                recommended_action="Hold steering wheel straight. Ease off the throttle gently without abrupt braking to allow tires to regain grip.",
                metrics_snapshot={
                    "road_friction_mu": t.road_friction_mu,
                    "slip_ratio_fl": t.wheel_slip_ratio_fl,
                    "speed_kmh": t.speed_kmh
                }
            ))

        # 4. Critical Tire Depressurization / Blowout Imminent
        min_psi = min(t.fl_tire_pressure_psi, t.fr_tire_pressure_psi, t.rl_tire_pressure_psi, t.rr_tire_pressure_psi)
        if min_psi < thresh.MIN_TIRE_PRESSURE_PSI:
            low_wheel = "Front-Left" if t.fl_tire_pressure_psi == min_psi else "Front-Right" if t.fr_tire_pressure_psi == min_psi else "Rear-Left" if t.rl_tire_pressure_psi == min_psi else "Rear-Right"
            alerts.append(HazardAlert(
                severity="WARNING",
                hazard_code="HAZARD_TIRE_DEPRESSURIZATION",
                title=f"Rapid Tire Pressure Loss ({low_wheel})",
                description=f"{low_wheel} tire pressure dropped to {min_psi} PSI (nominal is 33 PSI). Severe blowout risk at high speed.",
                recommended_action="Reduce vehicle speed gradually below 50 km/h, avoid sharp steering inputs, and proceed to nearest service area.",
                metrics_snapshot={
                    "wheel": low_wheel,
                    "pressure_psi": min_psi,
                    "speed_kmh": t.speed_kmh
                }
            ))

        # 5. Imminent Forward Collision (TTC < 2.4s)
        if t.time_to_collision_s < thresh.MIN_TIME_TO_COLLISION_SEC and t.speed_kmh > 30.0:
            alerts.append(HazardAlert(
                severity="CRITICAL",
                hazard_code="HAZARD_FORWARD_COLLISION",
                title="Imminent Forward Collision Hazard",
                description=f"Obstacle detected {t.forward_obstacle_dist_m}m ahead with Time-to-Collision of {t.time_to_collision_s}s at {t.speed_kmh} km/h.",
                recommended_action="Apply maximum brake pressure immediately. Prepare for autonomous emergency braking (AEB) intervention.",
                metrics_snapshot={
                    "obstacle_dist_m": t.forward_obstacle_dist_m,
                    "ttc_seconds": t.time_to_collision_s,
                    "speed_kmh": t.speed_kmh
                }
            ))

        self.active_alerts = alerts
        return alerts
