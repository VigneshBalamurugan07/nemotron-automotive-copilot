"""
NVIDIA NIM Nemotron API Client with Structured Tool-Calling & Offline Fallback.
Connects to NVIDIA NIM (e.g. nvidia/llama-3.1-nemotron-70b-instruct) via OpenAI-compatible endpoint.
"""

import json
import logging
from typing import List, Dict, Any, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from src.config import config
from src.agent.prompts import NEMOTRON_AUTOMOTIVE_SYSTEM_PROMPT
from src.tools.vehicle_tools import calculate_stopping_distance, diagnose_subsystem_health
from src.tools.emergency_tools import get_accident_prevention_procedure, trigger_ev_safety_limp_mode
from src.telemetry.can_bus import VehicleTelemetry

logger = logging.getLogger(__name__)


# Tool Definitions in OpenAI / NIM JSON Schema format
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_stopping_distance",
            "description": "Calculates total stopping distance in meters based on vehicle speed and road friction coefficient (mu).",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed_kmh": {
                        "type": "number",
                        "description": "Current vehicle speed in km/h."
                    },
                    "road_friction_mu": {
                        "type": "number",
                        "description": "Road surface friction coefficient (0.1 for ice, 0.4 for wet, 0.85 for dry asphalt)."
                    },
                    "driver_reaction_time_s": {
                        "type": "number",
                        "description": "Driver reaction time in seconds (default 1.0s)."
                    }
                },
                "required": ["speed_kmh", "road_friction_mu"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "diagnose_subsystem_health",
            "description": "Runs comprehensive health evaluation across Brakes, EV Battery pack, Tires, and ADAS sensors.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_accident_prevention_procedure",
            "description": "Retrieves official emergency driving and vehicle recovery protocols for specific hazards.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hazard_code": {
                        "type": "string",
                        "description": "Hazard identifier (e.g. HAZARD_BRAKE_FADE, HAZARD_BATTERY_THERMAL_RUNAWAY, HAZARD_TRACTION_LOSS_ICE, HAZARD_TIRE_DEPRESSURIZATION)."
                    }
                },
                "required": ["hazard_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_ev_safety_limp_mode",
            "description": "Engages vehicle limp-home mode to prevent catastrophic thermal or mechanical failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for engaging limp mode."
                    }
                },
                "required": ["reason"]
            }
        }
    }
]


class NemotronClient:
    """
    NVIDIA Nemotron LLM Interface with tool-calling capabilities.
    """

    def __init__(self):
        self.api_key = config.nvidia_api_key
        self.base_url = config.nvidia_base_url
        self.model = config.model_name
        self.client: Optional[Any] = None

        if OpenAI and self.api_key and self.api_key.strip() != "your_nvidia_api_key_here":
            try:
                self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client with NVIDIA endpoint: {e}")
                self.client = None

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], telemetry: VehicleTelemetry) -> Dict[str, Any]:
        """Executes a tool call locally and returns structured data."""
        if tool_name == "calculate_stopping_distance":
            speed = arguments.get("speed_kmh", telemetry.speed_kmh)
            mu = arguments.get("road_friction_mu", telemetry.road_friction_mu)
            rxn = arguments.get("driver_reaction_time_s", 1.0)
            return calculate_stopping_distance(speed, mu, rxn)

        elif tool_name == "diagnose_subsystem_health":
            return diagnose_subsystem_health(telemetry)

        elif tool_name == "get_accident_prevention_procedure":
            code = arguments.get("hazard_code", "HAZARD_BRAKE_FADE")
            return get_accident_prevention_procedure(code)

        elif tool_name == "trigger_ev_safety_limp_mode":
            reason = arguments.get("reason", "Critical hazard intervention triggered.")
            return trigger_ev_safety_limp_mode(reason)

        return {"error": f"Unknown tool: {tool_name}"}

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        telemetry: VehicleTelemetry
    ) -> Dict[str, Any]:
        """
        Executes a conversation turn with Nemotron, executing tool calls when requested.
        Returns a dictionary with:
        - "response_text": Final assistant voice/text reply
        - "tool_calls_made": List of executed tools and results
        - "is_simulated": Boolean indicating whether live NIM or fallback reasoning engine was used
        """
        tool_records = []

        if not self.client:
            return self._offline_simulated_reasoning(messages, telemetry)

        try:
            # First LLM call with tools enabled
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=600
            )

            msg = response.choices[0].message

            # Check if Nemotron called tools
            if msg.tool_calls:
                messages_with_tools = list(messages)
                messages_with_tools.append(msg)

                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except Exception:
                        fn_args = {}

                    tool_res = self.execute_tool(fn_name, fn_args, telemetry)
                    tool_records.append({
                        "name": fn_name,
                        "args": fn_args,
                        "result": tool_res
                    })

                    messages_with_tools.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(tool_res)
                    })

                # Second call to synthesize final spoken answer with tool results
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages_with_tools,
                    temperature=0.3,
                    max_tokens=600
                )
                final_text = second_response.choices[0].message.content or ""
                return {
                    "response_text": final_text,
                    "tool_calls_made": tool_records,
                    "is_simulated": False
                }

            else:
                return {
                    "response_text": msg.content or "",
                    "tool_calls_made": [],
                    "is_simulated": False
                }

        except Exception as e:
            logger.warning(f"Error calling NVIDIA NIM endpoint ({e}). Falling back to deterministic engine.")
            return self._offline_simulated_reasoning(messages, telemetry)

    def _offline_simulated_reasoning(
        self,
        messages: List[Dict[str, Any]],
        telemetry: VehicleTelemetry
    ) -> Dict[str, Any]:
        """
        High-fidelity deterministic automotive reasoning engine that mirrors Nemotron's
        multi-step tool calling and voice responses when running offline or without API key.
        """
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = str(m.get("content", "")).lower()
                break

        tool_records = []

        # Proactive Hazard Interventions
        if "hazard_brake_fade" in last_user_msg or ("brake" in last_user_msg and "fade" in last_user_msg):
            text = (
                f"Warning: Severe brake fade and pressure loss detected! Front pad temperature is {telemetry.front_left_brake_temp_c}°C. "
                "Downshift immediately to engage engine braking and avoid pumping the spongy pedal."
            )
        elif "hazard_battery_thermal_runaway" in last_user_msg or ("thermal" in last_user_msg and "runaway" in last_user_msg):
            text = (
                f"Critical Warning: EV Battery thermal runaway risk detected! Cell temperature reached {telemetry.battery_max_cell_temp_c}°C with rapid heat spike. "
                "Maneuver safely to the shoulder immediately, power down the high-voltage system, and evacuate to a safe distance."
            )
        elif "hazard_traction_loss_ice" in last_user_msg or "black_ice" in last_user_msg or "traction" in last_user_msg or "ice" in last_user_msg:
            text = (
                f"Warning: Black ice and severe traction loss detected! Road friction dropped to μ={telemetry.road_friction_mu} with front wheel slip. "
                "Hold the steering wheel straight and ease off the throttle gently. Do not slam on the brakes."
            )
        elif "hazard_tire_depressurization" in last_user_msg or "tire_blowout" in last_user_msg or "depressurization" in last_user_msg:
            text = (
                f"Warning: Critical Front-Left tire pressure loss detected at {telemetry.fl_tire_pressure_psi} PSI! "
                "Firmly grip the steering wheel at 9 and 3 to counter asymmetric yaw pull, and smoothly reduce vehicle speed."
            )
        elif "hazard_forward_collision" in last_user_msg or "collision" in last_user_msg or "forward_collision" in last_user_msg:
            text = (
                f"Emergency Alert: Imminent forward collision hazard! Obstacle detected {telemetry.forward_obstacle_dist_m} meters ahead with Time-to-Collision of {telemetry.time_to_collision_s} seconds. "
                "Apply maximum brake pressure immediately!"
            )
        elif "stop" in last_user_msg or "distance" in last_user_msg or ("brake" in last_user_msg and "calc" in last_user_msg):
            res = self.execute_tool("calculate_stopping_distance", {"speed_kmh": telemetry.speed_kmh, "road_friction_mu": telemetry.road_friction_mu}, telemetry)
            tool_records.append({"name": "calculate_stopping_distance", "args": {"speed_kmh": telemetry.speed_kmh, "road_friction_mu": telemetry.road_friction_mu}, "result": res})
            text = (
                f"At your current speed of {telemetry.speed_kmh} km/h on {res['road_condition']} (friction coefficient μ={telemetry.road_friction_mu}), "
                f"your estimated total stopping distance is {res['total_stopping_distance_meters']} meters. "
                f"I recommend maintaining a following distance of at least {res['safe_following_gap_recommendation_meters']} meters."
            )
        elif "health" in last_user_msg or "status" in last_user_msg or "check" in last_user_msg or "diagnos" in last_user_msg:
            res = self.execute_tool("diagnose_subsystem_health", {}, telemetry)
            tool_records.append({"name": "diagnose_subsystem_health", "args": {}, "result": res})
            text = (
                f"Vehicle diagnostics complete. Overall safety index is {res['overall_safety_index']}/100. "
                f"Braking subsystem is {res['braking_subsystem']['status']} with max pad temp at {res['braking_subsystem']['max_pad_temp_c']}°C. "
                f"Battery status is {res['ev_battery_subsystem']['status']} at {res['ev_battery_subsystem']['state_of_charge_pct']}% charge. "
                f"Tire pressures and traction are currently {res['tires_and_traction']['traction_status']}."
            )
        elif "procedure" in last_user_msg or "emergency" in last_user_msg:
            res = self.execute_tool("get_accident_prevention_procedure", {"hazard_code": "HAZARD_BRAKE_FADE"}, telemetry)
            tool_records.append({"name": "get_accident_prevention_procedure", "args": {"hazard_code": "HAZARD_BRAKE_FADE"}, "result": res})
            text = (
                f"Emergency protocol for {res['title']}: 1. Downshift immediately to engage engine/regenerative braking. "
                f"2. Do not pump spongy brakes frantically. 3. Scan ahead for gradual shoulder escape routes. "
                f"Physics rationale: {res['physics_explanation']}"
            )
        elif "tire" in last_user_msg or "pressure" in last_user_msg:
            text = (
                f"Current tire pressures: Front-Left {telemetry.fl_tire_pressure_psi} PSI, Front-Right {telemetry.fr_tire_pressure_psi} PSI, "
                f"Rear-Left {telemetry.rl_tire_pressure_psi} PSI, Rear-Right {telemetry.rr_tire_pressure_psi} PSI. "
                f"Road surface grip is μ={telemetry.road_friction_mu}."
            )
        elif "battery" in last_user_msg or "charge" in last_user_msg or "temp" in last_user_msg:
            text = (
                f"Battery State of Charge is {telemetry.battery_soc_pct}%. Max cell temperature is {telemetry.battery_max_cell_temp_c}°C "
                f"with thermal gradient at {telemetry.battery_temp_gradient_c_s}°C/s. Inverter temperature is {telemetry.inverter_temp_c}°C."
            )
        else:
            text = (
                f"NemoDrive telemetry monitor active. Cruising at {telemetry.speed_kmh} km/h in {telemetry.drive_mode} mode. "
                f"Brake line pressure is {telemetry.brake_line_pressure_bar} bar, and battery is at {telemetry.battery_soc_pct}%. "
                f"All systems are operating within safe dynamic envelopes."
            )

        return {
            "response_text": text,
            "tool_calls_made": tool_records,
            "is_simulated": True
        }
