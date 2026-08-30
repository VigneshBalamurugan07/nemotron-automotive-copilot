"""
Standalone test runner for NemoDrive-AI using Python unittest standard library.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from src.telemetry.can_bus import CANBusSimulator, VehicleTelemetry
from src.telemetry.hazard_detector import HazardDetector
from src.agent.nemotron_client import NemotronClient
from src.agent.orchestrator import AgentOrchestrator
from src.tools.vehicle_tools import calculate_stopping_distance, diagnose_subsystem_health
from src.tools.emergency_tools import get_accident_prevention_procedure, trigger_ev_safety_limp_mode
from src.scenarios.hazard_scenarios import SCENARIOS


class TestNemoDrive(unittest.TestCase):

    def test_can_bus_telemetry_generation(self):
        sim = CANBusSimulator()
        state = sim.step()
        self.assertIsInstance(state, VehicleTelemetry)
        self.assertTrue(0.0 <= state.speed_kmh <= 250.0)
        self.assertTrue(0.0 <= state.battery_soc_pct <= 100.0)
        self.assertTrue(state.front_left_brake_temp_c > 0.0)
        self.assertTrue(state.fl_tire_pressure_psi > 10.0)

    def test_stopping_distance_calculation(self):
        res = calculate_stopping_distance(speed_kmh=100.0, road_friction_mu=0.85)
        self.assertEqual(res["speed_kmh"], 100.0)
        self.assertTrue(res["total_stopping_distance_meters"] > 40.0)
        self.assertIn("safe_following_gap_recommendation_meters", res)

        res_ice = calculate_stopping_distance(speed_kmh=100.0, road_friction_mu=0.2)
        self.assertTrue(res_ice["total_stopping_distance_meters"] > res["total_stopping_distance_meters"])

    def test_subsystem_health_diagnostics(self):
        sim = CANBusSimulator()
        telemetry = sim.get_latest()
        diag = diagnose_subsystem_health(telemetry)
        self.assertIn("overall_safety_index", diag)
        self.assertTrue(diag["overall_safety_index"] >= 80)
        self.assertIn("braking_subsystem", diag)
        self.assertIn("ev_battery_subsystem", diag)

    def test_hazard_detector_brake_fade(self):
        detector = HazardDetector()
        sim = CANBusSimulator()
        sim.inject_override(SCENARIOS["brake_fade"]["overrides"])
        state = sim.get_latest()

        alerts = detector.evaluate(state)
        self.assertTrue(len(alerts) > 0)
        brake_alerts = [a for a in alerts if a.hazard_code == "HAZARD_BRAKE_FADE"]
        self.assertEqual(len(brake_alerts), 1)
        self.assertEqual(brake_alerts[0].severity, "CRITICAL")

    def test_hazard_detector_thermal_runaway(self):
        detector = HazardDetector()
        sim = CANBusSimulator()
        sim.inject_override(SCENARIOS["thermal_runaway"]["overrides"])
        state = sim.get_latest()

        alerts = detector.evaluate(state)
        thermal_alerts = [a for a in alerts if a.hazard_code == "HAZARD_BATTERY_THERMAL_RUNAWAY"]
        self.assertEqual(len(thermal_alerts), 1)

    def test_hazard_detector_black_ice(self):
        detector = HazardDetector()
        sim = CANBusSimulator()
        sim.inject_override(SCENARIOS["black_ice"]["overrides"])
        state = sim.get_latest()

        alerts = detector.evaluate(state)
        ice_alerts = [a for a in alerts if a.hazard_code == "HAZARD_TRACTION_LOSS_ICE"]
        self.assertEqual(len(ice_alerts), 1)

    def test_orchestrator_driver_query_and_proactive_alert(self):
        sim = CANBusSimulator()
        detector = HazardDetector()
        orchestrator = AgentOrchestrator(sim, detector)

        # Driver query
        res = orchestrator.process_driver_query("What is my current tire pressure and battery charge?")
        self.assertIn("response", res)
        self.assertTrue(len(res["response"]) > 10)

        # Inject brake fade and check proactive alert
        sim.inject_override(SCENARIOS["brake_fade"]["overrides"])
        proactive = orchestrator.check_and_generate_proactive_alert()
        self.assertIsNotNone(proactive)
        self.assertIn("spoken_warning", proactive)
        self.assertTrue(len(proactive["spoken_warning"]) > 10)

    def test_emergency_tools(self):
        proc = get_accident_prevention_procedure("HAZARD_BRAKE_FADE")
        self.assertIn("title", proc)
        self.assertTrue(len(proc["steps"]) > 0)

        limp = trigger_ev_safety_limp_mode("Test thermal override")
        self.assertEqual(limp["action"], "EV_SAFETY_LIMP_MODE_ENGAGED")
        self.assertEqual(limp["max_speed_kmh_cap"], 60.0)


if __name__ == "__main__":
    unittest.main()
