"""
CAN Bus Telemetry Simulator adhering to Vehicle Signal Specification (VSS) standards.
Generates 18+ real-time vehicle parameters across dynamics, thermal, braking, and ADAS domains.
"""

import time
import random
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class VehicleTelemetry:
    # Timestamp
    timestamp: float
    
    # Dynamics
    speed_kmh: float                    # Vehicle speed (km/h)
    motor_rpm: float                    # Electric Motor / Engine RPM
    throttle_pct: float                 # Accelerator pedal position (0-100%)
    steering_angle_deg: float           # Steering angle (-540 to +540 deg)
    yaw_rate_deg_s: float               # Yaw angular velocity
    lateral_g: float                    # Lateral acceleration (G)
    longitudinal_g: float               # Longitudinal acceleration (G)

    # Braking System
    brake_pedal_pct: float              # Brake pedal depression (0-100%)
    brake_line_pressure_bar: float      # Hydraulic line pressure (0-120 bar)
    front_left_brake_temp_c: float      # Front Left Pad Temp (°C)
    front_right_brake_temp_c: float     # Front Right Pad Temp (°C)
    rear_left_brake_temp_c: float       # Rear Left Pad Temp (°C)
    rear_right_brake_temp_c: float      # Rear Right Pad Temp (°C)

    # Tires & Road Surface
    fl_tire_pressure_psi: float         # Front Left Tire Pressure
    fr_tire_pressure_psi: float         # Front Right Tire Pressure
    rl_tire_pressure_psi: float         # Rear Left Tire Pressure
    rr_tire_pressure_psi: float         # Rear Right Tire Pressure
    wheel_slip_ratio_fl: float          # Wheel slip ratio FL (0.0 to 1.0)
    wheel_slip_ratio_fr: float          # Wheel slip ratio FR (0.0 to 1.0)
    road_friction_mu: float             # Road surface friction coeff (0.1 ice to 0.9 dry)

    # EV Battery & Powertrain
    battery_soc_pct: float              # State of Charge (0-100%)
    battery_voltage_v: float            # Pack voltage
    battery_current_a: float            # Pack current draw
    battery_max_cell_temp_c: float      # Hottest cell temp (°C)
    battery_temp_gradient_c_s: float    # Rate of temp change (dT/dt in °C/s)
    inverter_temp_c: float              # Power inverter temp (°C)

    # ADAS & Vision
    forward_obstacle_dist_m: float      # Distance to forward obstacle in meters
    time_to_collision_s: float          # Time to collision (s)
    ambient_temp_c: float               # External ambient temperature (°C)
    drive_mode: str                     # "Comfort", "Sport", "Eco", "Snow", "Track"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CANBusSimulator:
    """
    Simulates real-time CAN bus telemetry broadcast for modern electric/smart vehicles.
    Supports injecting anomalies and continuous physics-based updates.
    """

    def __init__(self):
        self.current_state = self._get_default_state()
        self.injected_overrides: Dict[str, Any] = {}
        self.last_update_time = time.time()

    def _get_default_state(self) -> VehicleTelemetry:
        return VehicleTelemetry(
            timestamp=time.time(),
            speed_kmh=68.5,
            motor_rpm=3200.0,
            throttle_pct=28.0,
            steering_angle_deg=1.2,
            yaw_rate_deg_s=0.4,
            lateral_g=0.04,
            longitudinal_g=0.08,
            brake_pedal_pct=0.0,
            brake_line_pressure_bar=0.0,
            front_left_brake_temp_c=185.0,
            front_right_brake_temp_c=182.0,
            rear_left_brake_temp_c=140.0,
            rear_right_brake_temp_c=138.0,
            fl_tire_pressure_psi=33.2,
            fr_tire_pressure_psi=33.0,
            rl_tire_pressure_psi=33.5,
            rr_tire_pressure_psi=33.4,
            wheel_slip_ratio_fl=0.03,
            wheel_slip_ratio_fr=0.03,
            road_friction_mu=0.85,
            battery_soc_pct=74.5,
            battery_voltage_v=395.2,
            battery_current_a=42.0,
            battery_max_cell_temp_c=34.5,
            battery_temp_gradient_c_s=0.02,
            inverter_temp_c=48.0,
            forward_obstacle_dist_m=85.0,
            time_to_collision_s=12.0,
            ambient_temp_c=22.0,
            drive_mode="Comfort"
        )

    def inject_override(self, overrides: Dict[str, Any]):
        """Inject specific sensor overrides cleanly from nominal state."""
        self.current_state = self._get_default_state()
        self.injected_overrides = dict(overrides)
        for k, v in overrides.items():
            if hasattr(self.current_state, k):
                setattr(self.current_state, k, v)

    def clear_overrides(self):
        """Reset all sensor overrides back to nominal operation."""
        self.injected_overrides.clear()
        self.current_state = self._get_default_state()

    def step(self) -> VehicleTelemetry:
        """Advance the CAN stream simulation one tick with slight realistic noise."""
        now = time.time()
        dt = max(0.01, now - self.last_update_time)
        self.last_update_time = now

        s = self.current_state

        speed = s.speed_kmh + random.uniform(-0.4, 0.4)
        speed = max(0.0, min(220.0, speed))

        fl_temp = s.front_left_brake_temp_c + (0.5 if s.brake_pedal_pct > 20 else -0.2)
        fl_temp = max(40.0, min(800.0, fl_temp))

        state = VehicleTelemetry(
            timestamp=now,
            speed_kmh=round(speed, 1),
            motor_rpm=round(speed * 46.5, 0),
            throttle_pct=round(max(0.0, min(100.0, s.throttle_pct + random.uniform(-1.0, 1.0))), 1),
            steering_angle_deg=round(s.steering_angle_deg + random.uniform(-0.5, 0.5), 1),
            yaw_rate_deg_s=round(s.yaw_rate_deg_s + random.uniform(-0.1, 0.1), 2),
            lateral_g=round(s.lateral_g + random.uniform(-0.01, 0.01), 3),
            longitudinal_g=round(s.longitudinal_g + random.uniform(-0.01, 0.01), 3),
            brake_pedal_pct=s.brake_pedal_pct,
            brake_line_pressure_bar=s.brake_line_pressure_bar,
            front_left_brake_temp_c=round(fl_temp, 1),
            front_right_brake_temp_c=round(fl_temp * 0.98, 1),
            rear_left_brake_temp_c=round(s.rear_left_brake_temp_c, 1),
            rear_right_brake_temp_c=round(s.rear_right_brake_temp_c, 1),
            fl_tire_pressure_psi=round(s.fl_tire_pressure_psi, 1),
            fr_tire_pressure_psi=round(s.fr_tire_pressure_psi, 1),
            rl_tire_pressure_psi=round(s.rl_tire_pressure_psi, 1),
            rr_tire_pressure_psi=round(s.rr_tire_pressure_psi, 1),
            wheel_slip_ratio_fl=round(s.wheel_slip_ratio_fl, 3),
            wheel_slip_ratio_fr=round(s.wheel_slip_ratio_fr, 3),
            road_friction_mu=round(s.road_friction_mu, 2),
            battery_soc_pct=round(max(0.0, s.battery_soc_pct - (0.001 * dt)), 1),
            battery_voltage_v=round(s.battery_voltage_v + random.uniform(-0.2, 0.2), 1),
            battery_current_a=round(s.battery_current_a + random.uniform(-1.0, 1.0), 1),
            battery_max_cell_temp_c=round(s.battery_max_cell_temp_c, 1),
            battery_temp_gradient_c_s=round(s.battery_temp_gradient_c_s, 2),
            inverter_temp_c=round(s.inverter_temp_c, 1),
            forward_obstacle_dist_m=round(max(2.0, s.forward_obstacle_dist_m + random.uniform(-0.5, 0.5)), 1),
            time_to_collision_s=round(max(0.5, s.time_to_collision_s), 1),
            ambient_temp_c=s.ambient_temp_c,
            drive_mode=s.drive_mode
        )

        # Apply overrides
        for k, v in self.injected_overrides.items():
            if hasattr(state, k):
                setattr(state, k, v)

        self.current_state = state
        return self.current_state

    def get_latest(self) -> VehicleTelemetry:
        return self.current_state
