"""Dependency-free smoke tests for Jev observer sidecar."""
import unittest
from jev_adapter import validate, handoff

class JevAdapterTests(unittest.TestCase):
    def test_handoff(self):
        observations = [
            {"turn_id": "1", "states": {"curiosity": .8}, "triggers": ["new_idea"], "direction": "exploring", "evidence": ["Could we try it?"], "observer": "mock-v1"},
            {"turn_id": "2", "states": {"caution": .6}, "triggers": ["uncertainty"], "direction": "checking", "evidence": ["Need to verify first"], "observer": "mock-v1"}
        ]
        result = handoff(observations)
        self.assertEqual(result["latest_states"], {"caution": .6})
        self.assertEqual(result["source_turns"], ["1", "2"])
        self.assertEqual(result["recent_triggers"], ["new_idea", "uncertainty"])

    def test_rejects_bad_probability(self):
        with self.assertRaises(ValueError):
            validate([{"turn_id": "1", "states": {"curiosity": 1.5}}])

    def test_empty(self):
        self.assertEqual(handoff([])["direction"], "unknown")

if __name__ == "__main__":
    unittest.main()
