"""
Automated Unit and Integration Tests for NemoDrive-AI.
Tests CAN Bus Telemetry, Hazard Detection, Tool Calling, and Proactive Interventions.
"""

import pytest
from src.telemetry.can_bus import CANBusSimulator, VehicleTelemetry
from src.telemetry.hazard_detector import HazardDetector
from src.agent.nemotron_client import NemotronClient
from src.agent.orchestrator import AgentOrchestrator
from src.tools.vehicle_tools import calculate_stopping_distance, diagnose_subsystem_health
from src.tools.emergency_tools import get_accident_prevention_procedure, trigger_ev_safety_limp_mode
from src.scenarios.hazard_scenarios import SCENARIOS


def test_can_bus_telemetry_generation():
    sim = CANBusSimulator()
    state = sim.step()
    assert isinstance(state, VehicleTelemetry)
    assert 0.0 <= state.speed_kmh <= 250.0
    assert 0.0 <= state.battery_soc_pct <= 100.0
    assert state.front_left_brake_temp_c > 0.0
    assert state.fl_tire_pressure_psi > 10.0


def test_stopping_distance_calculation():
    res = calculate_stopping_distance(speed_kmh=100.0, road_friction_mu=0.85)
    assert res["speed_kmh"] == 100.0
    assert res["total_stopping_distance_meters"] > 40.0
    assert "safe_following_gap_recommendation_meters" in res

    # Low friction (ice) should have much longer stopping distance
    res_ice = calculate_stopping_distance(speed_kmh=100.0, road_friction_mu=0.2)
    assert res_ice["total_stopping_distance_meters"] > res["total_stopping_distance_meters"]


def test_subsystem_health_diagnostics():
    sim = CANBusSimulator()
    telemetry = sim.get_latest()
    diag = diagnose_subsystem_health(telemetry)
    assert "overall_safety_index" in diag
    assert diag["overall_safety_index"] >= 80
    assert "braking_subsystem" in diag
    assert "ev_battery_subsystem" in diag


def test_hazard_detector_brake_fade():
    detector = HazardDetector()
    sim = CANBusSimulator()
    # Inject brake fade scenario
    sim.inject_override(SCENARIOS["brake_fade"]["overrides"])
    state = sim.get_latest()

    alerts = detector.evaluate(state)
    assert len(alerts) > 0
    brake_alerts = [a for a in alerts if a.hazard_code == "HAZARD_BRAKE_FADE"]
    assert len(brake_alerts) == 1
    assert brake_alerts[0].severity == "CRITICAL"


def test_hazard_detector_thermal_runaway():
    detector = HazardDetector()
    sim = CANBusSimulator()
    sim.inject_override(SCENARIOS["thermal_runaway"]["overrides"])
    state = sim.get_latest()

    alerts = detector.evaluate(state)
    thermal_alerts = [a for a in alerts if a.hazard_code == "HAZARD_BATTERY_THERMAL_RUNAWAY"]
    assert len(thermal_alerts) == 1


def test_hazard_detector_black_ice():
    detector = HazardDetector()
    sim = CANBusSimulator()
    sim.inject_override(SCENARIOS["black_ice"]["overrides"])
    state = sim.get_latest()

    alerts = detector.evaluate(state)
    ice_alerts = [a for a in alerts if a.hazard_code == "HAZARD_TRACTION_LOSS_ICE"]
    assert len(ice_alerts) == 1


def test_orchestrator_driver_query_and_proactive_alert():
    sim = CANBusSimulator()
    detector = HazardDetector()
    orchestrator = AgentOrchestrator(sim, detector)

    # Driver query
    res = orchestrator.process_driver_query("What is my current tire pressure and battery charge?")
    assert "response" in res
    assert len(res["response"]) > 10

    # Inject brake fade and check proactive alert
    sim.inject_override(SCENARIOS["brake_fade"]["overrides"])
    proactive = orchestrator.check_and_generate_proactive_alert()
    assert proactive is not None
    assert "spoken_warning" in proactive
    assert len(proactive["spoken_warning"]) > 10


def test_emergency_tools():
    proc = get_accident_prevention_procedure("HAZARD_BRAKE_FADE")
    assert "title" in proc
    assert len(proc["steps"]) > 0

    limp = trigger_ev_safety_limp_mode("Test thermal override")
    assert limp["action"] == "EV_SAFETY_LIMP_MODE_ENGAGED"
    assert limp["max_speed_kmh_cap"] == 60.0
