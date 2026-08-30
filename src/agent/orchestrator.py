"""
NemoDrive Agent Orchestrator: Bridges Live CAN Telemetry, Hazard Detection,
NVIDIA Nemotron Reasoning, and Proactive Voice Dispatching.
"""

from typing import List, Dict, Any, Optional
from src.agent.nemotron_client import NemotronClient
from src.agent.prompts import NEMOTRON_AUTOMOTIVE_SYSTEM_PROMPT, PROACTIVE_HAZARD_PROMPT_TEMPLATE
from src.telemetry.can_bus import VehicleTelemetry, CANBusSimulator
from src.telemetry.hazard_detector import HazardDetector, HazardAlert


class AgentOrchestrator:
    """
    Central brain managing conversation, live telemetry ingestion,
    proactive hazard triggers, and voice responses.
    """

    def __init__(self, can_simulator: CANBusSimulator, hazard_detector: HazardDetector):
        self.can_sim = can_simulator
        self.hazard_det = hazard_detector
        self.nemotron = NemotronClient()
        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": NEMOTRON_AUTOMOTIVE_SYSTEM_PROMPT}
        ]
        self.last_triggered_hazard_code: Optional[str] = None

    def process_driver_query(self, query: str) -> Dict[str, Any]:
        """
        Handles explicit query spoken or typed by the driver.
        Injects live CAN telemetry context into prompt.
        """
        telemetry = self.can_sim.get_latest()

        # Telemetry context header for precise reasoning
        telemetry_context = (
            f"[LIVE TELEMETRY SNAPSHOT]\n"
            f"Speed: {telemetry.speed_kmh} km/h | Mode: {telemetry.drive_mode}\n"
            f"Brakes: FL Pad {telemetry.front_left_brake_temp_c}°C, FR Pad {telemetry.front_right_brake_temp_c}°C, Line Pressure {telemetry.brake_line_pressure_bar} bar\n"
            f"Battery: SoC {telemetry.battery_soc_pct}%, Max Cell {telemetry.battery_max_cell_temp_c}°C, Gradient {telemetry.battery_temp_gradient_c_s}°C/s\n"
            f"Tires: FL {telemetry.fl_tire_pressure_psi} PSI, FR {telemetry.fr_tire_pressure_psi} PSI, Slip Ratio {telemetry.wheel_slip_ratio_fl}, Road Friction μ={telemetry.road_friction_mu}\n"
            f"ADAS: Forward Obstacle {telemetry.forward_obstacle_dist_m}m, TTC {telemetry.time_to_collision_s}s\n"
        )

        user_content = f"{telemetry_context}\nDriver: {query}"
        self.conversation_history.append({"role": "user", "content": user_content})

        result = self.nemotron.chat_completion(self.conversation_history, telemetry)

        # Store assistant response in history
        self.conversation_history.append({"role": "assistant", "content": result["response_text"]})

        return {
            "query": query,
            "response": result["response_text"],
            "tool_calls": result["tool_calls_made"],
            "is_simulated": result["is_simulated"],
            "telemetry_snapshot": telemetry.to_dict()
        }

    def check_and_generate_proactive_alert(self) -> Optional[Dict[str, Any]]:
        """
        Evaluates current telemetry. If an unacknowledged critical hazard is detected,
        synthesizes a high-priority spoken voice intervention immediately.
        """
        telemetry = self.can_sim.step()
        alerts = self.hazard_det.evaluate(telemetry)

        if not alerts:
            self.last_triggered_hazard_code = None
            return None

        primary_alert = alerts[0]

        # Don't repeat the exact same alert indefinitely if already triggered
        if primary_alert.hazard_code == self.last_triggered_hazard_code:
            return None

        self.last_triggered_hazard_code = primary_alert.hazard_code

        # Format prompt for immediate spoken voice warning
        alert_prompt = PROACTIVE_HAZARD_PROMPT_TEMPLATE.format(
            hazard_code=primary_alert.hazard_code,
            severity=primary_alert.severity,
            title=primary_alert.title,
            description=primary_alert.description,
            recommended_action=primary_alert.recommended_action,
            metrics_snapshot=primary_alert.metrics_snapshot
        )

        temp_messages = [
            {"role": "system", "content": NEMOTRON_AUTOMOTIVE_SYSTEM_PROMPT},
            {"role": "user", "content": alert_prompt}
        ]

        result = self.nemotron.chat_completion(temp_messages, telemetry)
        spoken_warning = result["response_text"]

        # Append to main conversation history as a high-priority system intervention
        self.conversation_history.append({
            "role": "assistant",
            "content": f"🚨 [PROACTIVE INTERVENTION - {primary_alert.title}]: {spoken_warning}"
        })

        return {
            "alert": primary_alert,
            "spoken_warning": spoken_warning,
            "tool_calls": result["tool_calls_made"],
            "telemetry": telemetry.to_dict()
        }
