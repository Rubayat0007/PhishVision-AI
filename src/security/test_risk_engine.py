import unittest

from src.security.risk_engine import calculate_risk


class TestCalculateRisk(unittest.TestCase):
    def test_zero_scores_are_minimal(self):
        result = calculate_risk(0, 0, 0)

        self.assertEqual(result["overall_score"], 0.0)
        self.assertEqual(result["risk_level"], "MINIMAL")

    def test_weights_are_30_30_40(self):
        self.assertEqual(calculate_risk(100, 0, 0)["overall_score"], 30.0)
        self.assertEqual(calculate_risk(0, 100, 0)["overall_score"], 30.0)
        self.assertEqual(calculate_risk(0, 0, 100)["overall_score"], 40.0)

    def test_all_maximum_scores_produce_100(self):
        result = calculate_risk(100, 100, 100)

        self.assertEqual(result["overall_score"], 100.0)
        self.assertEqual(result["risk_level"], "HIGH")

    def test_inputs_are_clamped_to_0_100(self):
        result = calculate_risk(200, -50, 150)

        self.assertEqual(result["text_score"], 100.0)
        self.assertEqual(result["url_score"], 0.0)
        self.assertEqual(result["cnn_score"], 100.0)
        self.assertEqual(result["overall_score"], 70.0)
        self.assertEqual(result["risk_level"], "HIGH")

    def test_risk_boundaries(self):
        self.assertEqual(calculate_risk(100, 0, 0)["risk_level"], "MEDIUM")
        self.assertEqual(calculate_risk(0, 0, 70)["risk_level"], "LOW")
        self.assertEqual(calculate_risk(100, 100, 25)["risk_level"], "HIGH")
        self.assertEqual(calculate_risk(0, 0, 1)["risk_level"], "LOW")

    def test_numeric_strings_are_accepted(self):
        result = calculate_risk("50", "25", "10")

        self.assertEqual(result["overall_score"], 26.5)
        self.assertEqual(result["risk_level"], "LOW")

    def test_cnn_score_is_returned(self):
        result = calculate_risk(20, 30, 40)

        self.assertEqual(result["cnn_score"], 40.0)
        self.assertEqual(result["overall_score"], 31.0)


if __name__ == "__main__":
    unittest.main()
