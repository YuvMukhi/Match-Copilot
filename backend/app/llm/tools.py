"""Anthropic tool calling definitions for Match Copilot."""

from typing import Any

ANTHROPIC_TOOLS: list[dict[str, Any]] = [
    {
        "name": "explain_points_change",
        "description": (
            "Compares fantasy team points between two match moments (e.g. over N vs over M) "
            "and returns exact player point deltas, wickets, boundaries, dot balls, economy, and duck penalties."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "compare_over": {
                    "type": "integer",
                    "description": "The earlier over to compare against. Defaults to previous over (over - 1).",
                }
            },
            "required": [],
        },
    },
    {
        "name": "suggest_changes",
        "description": (
            "Deterministically ranks players by projected rest-of-match points, identifies risks "
            "(batter already dismissed, bowler quota completed), and recommends captaincy/vice-captaincy fixes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "simulate_reduced_overs",
        "description": (
            "Simulates match interruption due to rain, providing approximate DLS-style revised target "
            "and projected player fantasy points strictly as low/expected/high ranges."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reduced_overs": {
                    "type": "integer",
                    "description": "Total revised match overs (e.g. 15 overs).",
                    "default": 15,
                }
            },
            "required": [],
        },
    },
]
