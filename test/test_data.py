# Copyright (c) 2026 FRC Team 6907, The G.O.A.T
# Licensed under the MIT License.

from __future__ import annotations

import os
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from data.frc_json import request_frc_json


TEST_CACHE_ROOT = Path(__file__).resolve().parent / "test_cache"


class TestData(unittest.TestCase):
    def test_request_frc_json_reads_from_test_cache_without_network(self) -> None:
        with patch.dict(os.environ, {"GOAT_EVENT_CACHE_ROOT": str(TEST_CACHE_ROOT)}):
            with patch("data.frc_json.fetch_frc_json", side_effect=RuntimeError("network disabled")):
                payload = request_frc_json(
                    url="https://frc-api.firstinspires.org/v3.0/2024/teams?eventCode=AZVA",
                    key="teams",
                    season=2024,
                    eventCode="AZVA",
                )

        expectedTopLevel = {
            "teamCountTotal": 41,
            "teamCountPage": 41,
            "pageCurrent": 1,
            "pageTotal": 1,
        }
        for key, value in expectedTopLevel.items():
            self.assertEqual(payload.get(key), value, f"Unexpected value for key '{key}'")

        teamsValue: Any = payload.get("teams")
        self.assertIsInstance(teamsValue, list, "Expected 'teams' to be a list")
        self.assertEqual(len(teamsValue), 41, "Expected exactly 41 teams in cached AZVA response")

        teamValue: Any = next((team for team in teamsValue if isinstance(team, dict) and team.get("teamNumber") == 6907), None)
        self.assertIsInstance(teamValue, dict, "Expected team 6907 entry to exist in cached teams response")

        expectedTeam = {
            "teamNumber": 6907,
            "nameShort": "The G.O.A.T",
            "country": "China",
            "rookieYear": 2018,
        }
        for key, value in expectedTeam.items():
            self.assertEqual(teamValue.get(key), value, f"Unexpected value for cached team 6907 field '{key}'")


if __name__ == "__main__":
    unittest.main()
