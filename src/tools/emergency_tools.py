"""
Emergency Procedures & Safety Intervention Tools for NemoDrive-AI.
"""

from typing import Dict, Any


SAFETY_PROCEDURES_DB = {
    "HAZARD_BRAKE_FADE": {
        "title": "Brake Fade & Hydraulic Failure Protocol",
        "steps": [
            "1. Shift down sequentially to lower gear or engage maximum regenerative braking (B-mode).",
            "2. DO NOT pump spongy brakes frantically; maintain steady modulated pressure.",
            "3. Scan roadway ahead for uphill runoff areas or gradual shoulder escape routes.",
            "4. Gently apply electronic parking brake (EPB) if hydraulic pressure is fully lost."
        ],
        "physics_explanation": "Brake fade occurs when kinetic energy turns into extreme thermal energy (>450°C), causing brake fluid boiling (vapor lock) and pad glazing."
    },
    "HAZARD_BATTERY_THERMAL_RUNAWAY": {
        "title": "EV High-Voltage Thermal Runaway Protocol",
        "steps": [
            "1. Signal and maneuver vehicle to the nearest open shoulder immediately.",
            "2. Put vehicle in PARK, engage hazard flashers, and switch OFF the master ignition.",
            "3. Evacuate all passengers immediately to at least 30 meters upwind from the vehicle.",
            "4. Dial emergency services (911/112) and inform them of an active lithium-ion EV battery thermal incident."
        ],
        "physics_explanation": "Thermal runaway is a self-sustaining exothermic reaction in Li-ion cells where temperatures exceed 60°C and escalate rapidly."
    },
    "HAZARD_TRACTION_LOSS_ICE": {
        "title": "Black Ice & Hydroplaning Stabilization Protocol",
        "steps": [
            "1. Do NOT slam on the brakes or make abrupt steering corrections.",
            "2. Gently ease your foot off the accelerator pedal.",
            "3. Keep steering pointed in the direction you want the vehicle to travel.",
            "4. Allow tires to naturally regain contact patch grip before applying gentle steering."
        ],
        "physics_explanation": "When water or ice separates tire rubber from pavement, friction coefficient drops below 0.2, causing directional loss."
    },
    "HAZARD_TIRE_DEPRESSURIZATION": {
        "title": "High-Speed Tire Blowout Prevention Protocol",
        "steps": [
            "1. Firmly grip steering wheel with both hands at 9 and 3 o'clock positions.",
            "2. Avoid panic braking; maintain slight throttle to keep vehicle straight against yaw pull.",
            "3. Gradually coast down speed below 40 km/h before turning onto the shoulder."
        ],
        "physics_explanation": "Sudden pressure loss induces uneven rolling resistance, generating strong asymmetric yaw moment."
    }
}


def get_accident_prevention_procedure(hazard_code: str) -> Dict[str, Any]:
    """
    Retrieves standardized automotive emergency response protocol for an active hazard.
    """
    if hazard_code in SAFETY_PROCEDURES_DB:
        return SAFETY_PROCEDURES_DB[hazard_code]
    return {
        "title": "General Vehicle Safety Protocol",
        "steps": [
            "1. Reduce vehicle speed smoothly.",
            "2. Turn on hazard warning flashers.",
            "3. Pull over to a safe location away from traffic."
        ],
        "physics_explanation": "Unclassified anomaly detected. Follow standard defensive driving procedure."
    }


def trigger_ev_safety_limp_mode(reason: str) -> Dict[str, Any]:
    """
    Simulates engaging EV Safety Limp Mode: restricts powertrain output,
    caps speed to 60 km/h, enables max regen, and preserves thermal integrity.
    """
    return {
        "action": "EV_SAFETY_LIMP_MODE_ENGAGED",
        "status": "SUCCESS",
        "power_limit_pct": 35.0,
        "max_speed_kmh_cap": 60.0,
        "regen_braking_level": "MAX_LEVEL_3",
        "reason": reason,
        "cabin_notification": "Vehicle has entered Limp-Home mode for system protection."
    }
