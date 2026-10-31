"""Deterministic DLS (Duckworth-Lewis-Stern) style match estimator and what-if simulation.

Clearly labelled: Approximate DLS-style Revised Target (Prototype model).
Projects remaining runs, wickets, revised target, and fantasy points per player
as strict RANGES (low / expected / high), never fake-precise numbers.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from app.services.projection_engine import (
    project_player_rest_of_match,
)
from app.services.scoring_engine import load_scoring_rules

# Standard T20 Resource Percentage Table: Resource% remaining based on (overs_left, wickets_lost)
# Based on standard published T20 resource curves
DLS_RESOURCE_TABLE_T20: dict[int, list[float]] = {
    # overs_left: [0 wkt, 1 wkt, 2 wkt, 3 wkt, 4 wkt, 5 wkt, 6 wkt, 7 wkt, 8 wkt, 9 wkt]
    20: [100.0, 93.4, 85.1, 74.9, 62.7, 49.0, 34.9, 22.0, 11.9, 4.7],
    18: [93.6,  87.8, 80.5, 71.4, 60.3, 47.6, 34.2, 21.8, 11.8, 4.7],
    16: [86.8,  81.8, 75.5, 67.5, 57.5, 45.9, 33.3, 21.5, 11.7, 4.7],
    15: [82.5,  78.5, 72.8, 65.4, 56.1, 45.2, 33.1, 21.4, 11.7, 4.7],
    14: [78.5,  74.8, 69.8, 63.0, 54.3, 44.0, 32.5, 21.2, 11.6, 4.7],
    12: [70.1,  67.2, 63.2, 57.7, 50.3, 41.3, 31.0, 20.6, 11.4, 4.6],
    10: [60.9,  58.8, 55.8, 51.5, 45.5, 37.9, 28.9, 19.6, 11.1, 4.6],
    8:  [50.6,  49.2, 47.1, 44.0, 39.4, 33.4, 26.0, 18.0, 10.4, 4.5],
    6:  [39.5,  38.6, 37.3, 35.2, 32.0, 27.6, 22.0, 15.6,  9.3, 4.2],
    5:  [33.6,  33.0, 32.0, 30.4, 27.8, 24.2, 19.6, 14.1,  8.6, 4.0],
    4:  [27.5,  27.1, 26.4, 25.2, 23.3, 20.6, 16.9, 12.4,  7.7, 3.7],
    2:  [14.4,  14.3, 14.1, 13.7, 12.9, 11.7, 10.0,  7.8,  5.2, 2.7],
    1:  [7.4,    7.4,  7.3,  7.2,  6.9,  6.4,  5.6,  4.5,  3.2, 1.8],
    0:  [0.0,    0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, 0.0],
}


def get_resource_percentage(overs_left: int, wickets_lost: int) -> float:
    """Returns approximate resource percentage left for given overs and wickets."""
    w = max(0, min(9, wickets_lost))
    u = max(0, min(20, overs_left))

    if u in DLS_RESOURCE_TABLE_T20:
        return DLS_RESOURCE_TABLE_T20[u][w]

    # Linear interpolation between nearest available over keys
    keys = sorted(DLS_RESOURCE_TABLE_T20.keys())
    lower_k = max([k for k in keys if k <= u], default=0)
    upper_k = min([k for k in keys if k >= u], default=20)

    if lower_k == upper_k:
        return DLS_RESOURCE_TABLE_T20[lower_k][w]

    r_lower = DLS_RESOURCE_TABLE_T20[lower_k][w]
    r_upper = DLS_RESOURCE_TABLE_T20[upper_k][w]
    fraction = (u - lower_k) / (upper_k - lower_k)
    return round(r_lower + fraction * (r_upper - r_lower), 2)


@dataclass
class PlayerReducedOverProjection:
    player_id: str
    player_name: str
    role: str
    current_points: float
    projected_low: float
    projected_expected: float
    projected_high: float
    confidence_note: str
    notes: str


@dataclass
class DlsSimulationResult:
    original_overs: int
    reduced_overs: int
    current_over: int
    overs_lost: int
    runs_scored_so_far: int
    wickets_lost_so_far: int

    # Clearly labelled approximate DLS values
    model_name: str = "Approximate DLS-style Revised Target (Prototype Engine)"
    dls_resource_available_pct: float = 0.0
    projected_innings1_total_low: int = 0
    projected_innings1_total_expected: int = 0
    projected_innings1_total_high: int = 0
    approximate_revised_target: int = 0

    player_projections: list[PlayerReducedOverProjection] = field(default_factory=list)
    confidence_note: str = ""
    summary: str = ""


def simulate_reduced_overs(
    team_players: list[dict[str, Any]],
    deliveries: list[dict[str, Any]],
    current_over: int,
    reduced_overs: int = 15,
    original_overs: int = 20,
    rules: Optional[dict[str, Any]] = None,
) -> DlsSimulationResult:
    """Simulates rain delay cutting match to reduced_overs (e.g. 15 overs)."""
    if rules is None:
        rules = load_scoring_rules()

    # Active deliveries up to current_over
    active_deliveries = [d for d in deliveries if d.get("over_number", 0) <= current_over] if current_over > 0 else []

    # Current match tally
    runs_so_far = sum(d.get("runs_batter", 0) + d.get("runs_extras", 0) for d in active_deliveries)
    wickets_so_far = sum(1 for d in active_deliveries if d.get("is_wicket", False))

    overs_lost = max(0, original_overs - reduced_overs)
    rem_overs = max(0, reduced_overs - current_over)

    # Resource calculations
    r_initial = get_resource_percentage(original_overs, 0)  # 100%
    r_at_interruption = get_resource_percentage(original_overs - current_over, wickets_so_far)
    r_on_resumption = get_resource_percentage(rem_overs, wickets_so_far)

    # Lost resources due to overs deduction
    r_lost = max(0.0, r_at_interruption - r_on_resumption)
    r_available = max(0.0, r_initial - r_lost)

    # Deterministic projection of Innings 1 score
    current_rr = (runs_so_far / current_over) if current_over > 0 else 8.0

    # In remaining overs, accelerated death rate
    death_rr = max(current_rr, 8.5)
    exp_rem_runs = round(rem_overs * death_rr)
    low_rem_runs = round(rem_overs * max(5.0, current_rr * 0.7))
    high_rem_runs = round(rem_overs * 12.0)

    proj_total_exp = runs_so_far + exp_rem_runs
    proj_total_low = runs_so_far + low_rem_runs
    proj_total_high = runs_so_far + high_rem_runs

    # DLS Revised Target for Team 2 (if Innings 2 also reduced to same overs)
    # Target = (S1 * R2 / R1) + 1 where R2 is resource of full reduced innings
    r_innings2 = get_resource_percentage(reduced_overs, 0)
    revised_target = round((proj_total_exp * (r_innings2 / 100.0))) + 1 if proj_total_exp > 0 else 0

    # Calculate player point ranges for the reduced match
    player_projections: list[PlayerReducedOverProjection] = []
    scale_factor = (rem_overs / max(1, original_overs - current_over)) if (original_overs - current_over) > 0 else 0.0

    for p in team_players:
        full_proj = project_player_rest_of_match(
            player=p,
            deliveries=deliveries,
            current_over=current_over,
            total_overs=original_overs,
            rules=rules,
        )

        curr_pts = full_proj.current_points
        # Scale remaining points by the reduction in remaining overs
        scaled_low = round(curr_pts + (full_proj.remaining_low * scale_factor * (2.0 if p.get("is_captain") else 1.5 if p.get("is_vice_captain") else 1.0)), 1)
        scaled_exp = round(curr_pts + (full_proj.remaining_expected * scale_factor * (2.0 if p.get("is_captain") else 1.5 if p.get("is_vice_captain") else 1.0)), 1)
        scaled_high = round(curr_pts + (full_proj.remaining_high * scale_factor * (2.0 if p.get("is_captain") else 1.5 if p.get("is_vice_captain") else 1.0)), 1)

        note = "Projected based on shortened match quota."
        if full_proj.is_out:
            note = "Out: no further batting points possible."
        elif full_proj.quota_exhausted:
            note = "Quota done: no further bowling points possible."

        player_projections.append(
            PlayerReducedOverProjection(
                player_id=p["id"],
                player_name=p["name"],
                role=p["role"],
                current_points=curr_pts,
                projected_low=scaled_low,
                projected_expected=scaled_exp,
                projected_high=scaled_high,
                confidence_note=f"Range: {scaled_low} to {scaled_high} pts (confidence: Medium)",
                notes=note,
            )
        )

    summary = (
        f"Rain reduction to {reduced_overs} overs ({overs_lost} overs lost). "
        f"Current score: {runs_so_far}/{wickets_so_far} after {current_over} overs. "
        f"Projected Innings 1 score: {proj_total_low}-{proj_total_high} runs (expected: {proj_total_exp}). "
        f"Approximate DLS target for Team 2: {revised_target} runs in {reduced_overs} overs."
    )

    return DlsSimulationResult(
        original_overs=original_overs,
        reduced_overs=reduced_overs,
        current_over=current_over,
        overs_lost=overs_lost,
        runs_scored_so_far=runs_so_far,
        wickets_lost_so_far=wickets_so_far,
        dls_resource_available_pct=round(r_available, 1),
        projected_innings1_total_low=proj_total_low,
        projected_innings1_total_expected=proj_total_exp,
        projected_innings1_total_high=proj_total_high,
        approximate_revised_target=revised_target,
        player_projections=player_projections,
        confidence_note="Estimates provided as ranges. Real-world DLS target may vary with proprietary ICC software.",
        summary=summary,
    )
