from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.filters.eligibility import (
    CONDITIONS,
    TaskEligibilityRecord,
    load_task_eligibility,
)


ROOT = Path(__file__).resolve().parents[1]


class EligibilityContractTest(unittest.TestCase):
    def test_profile_round_trips_and_exposes_all_conditions(self) -> None:
        record = load_task_eligibility(ROOT / "src" / "profiles" / "first_pilot_eligibility.json")

        self.assertIsInstance(record, TaskEligibilityRecord)
        self.assertEqual(tuple(record.conditions), CONDITIONS)
        self.assertEqual(record.instance_id, "pytest-dev__pytest-7432")
        self.assertEqual(record.chosen_pilot_condition, "comments_docstrings")
        self.assertIn("comments_docstrings", record.eligible_conditions)

    def test_second_task_profile_round_trips(self) -> None:
        record = load_task_eligibility(ROOT / "src" / "profiles" / "psf__requests-2317_eligibility.json")

        self.assertIsInstance(record, TaskEligibilityRecord)
        self.assertEqual(tuple(record.conditions), CONDITIONS)
        self.assertEqual(record.instance_id, "psf__requests-2317")
        self.assertEqual(record.chosen_pilot_condition, "comments_docstrings")
        self.assertEqual(record.eligible_conditions, ["comments_docstrings", "remove_tests"])

    def test_schema_lists_required_condition_keys(self) -> None:
        schema_path = ROOT / "schemas" / "task_eligibility.schema.json"
        with schema_path.open(encoding="utf-8") as handle:
            schema = json.load(handle)

        required_conditions = schema["properties"]["conditions"]["required"]
        self.assertEqual(required_conditions, list(CONDITIONS))


if __name__ == "__main__":
    unittest.main()
