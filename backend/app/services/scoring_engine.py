"""Deterministic fantasy cricket scoring engine.

Calculates fantasy points based strictly on scoring_rules.yaml.
Never computes numbers via LLM. Pure functions with full traceability.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from app.core.config import get_settings


@dataclass
class PlayerEventBreakdown:
    description: str
    points: float
    category: str  # starting_xi, batting, bowling, fielding, bonus, penalty


@dataclass
class PlayerScoreBreakdown:
    player_id: str
    player_name: str
    role: str
    team: str
    is_captain: bool = False
    is_vice_captain: bool = False
    starting_xi_points: float = 0.0
    batting_points: float = 0.0
    bowling_points: float = 0.0
    fielding_points: float = 0.0
    bonus_points: float = 0.0
    penalty_points: float = 0.0
    base_points: float = 0.0
    multiplier: float = 1.0
    total_points: float = 0.0

    # Statistical counters
    runs: int = 0
    balls_faced: int = 0
    fours: int = 0
    sixes: int = 0
    is_dismissed: bool = False
    dismissal_kind: Optional[str] = None

    balls_bowled: int = 0
    overs_bowled: float = 0.0
    runs_conceded: int = 0
    wickets: int = 0
    bowled_or_lbw_count: int = 0
    maidens: int = 0

    catches: int = 0
    stumpings: int = 0
    run_outs: int = 0

    events: list[PlayerEventBreakdown] = field(default_factory=list)


@dataclass
class TeamScoreBreakdown:
    team_id: str
    team_name: str
    over_number: int
    total_points: float = 0.0
    players: list[PlayerScoreBreakdown] = field(default_factory=list)


def load_scoring_rules(rules_path: Optional[str] = None) -> dict[str, Any]:
    if not rules_path:
        rules_path = get_settings().scoring_rules_path

    path = Path(rules_path)
    if not path.is_file():
        # Fallback to local package path
        alt_path = Path(__file__).resolve().parent.parent.parent / "scoring_rules.yaml"
        if alt_path.is_file():
            path = alt_path
        else:
            raise FileNotFoundError(f"Scoring rules file not found at {rules_path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def calculate_player_points(
    player_id: str,
    player_name: str,
    role: str,
    team: str,
    deliveries: list[dict[str, Any]],
    is_captain: bool = False,
    is_vice_captain: bool = False,
    is_playing_xi: bool = True,
    rules: Optional[dict[str, Any]] = None,
) -> PlayerScoreBreakdown:
    """Calculates deterministic points for a single player up to current deliveries."""
    if rules is None:
        rules = load_scoring_rules()

    bat_rules = rules.get("batting", {})
    bowl_rules = rules.get("bowling", {})
    field_rules = rules.get("fielding", {})
    gen_rules = rules.get("general", {})
    mult_rules = rules.get("multipliers", {})

    breakdown = PlayerScoreBreakdown(
        player_id=player_id,
        player_name=player_name,
        role=role,
        team=team,
        is_captain=is_captain,
        is_vice_captain=is_vice_captain,
    )

    if is_playing_xi:
        s_xi_pts = float(gen_rules.get("starting_xi", 4.0))
        breakdown.starting_xi_points += s_xi_pts
        breakdown.events.append(
            PlayerEventBreakdown(description="In Starting XI", points=s_xi_pts, category="starting_xi")
        )

    # 1. Batting statistics
    # Filter deliveries where this player was on strike
    overs_seen: set[tuple[int, int]] = set()
    maiden_over_runs: dict[int, int] = {}
    maiden_over_balls: dict[int, int] = {}

    for d in deliveries:
        # Batting
        if d.get("batter_id") == player_id:
            r = d.get("runs_batter", 0)
            breakdown.runs += r
            # Only count legal deliveries or no-balls as balls faced
            if d.get("extra_type") != "wide":
                breakdown.balls_faced += 1

            if r == 4:
                breakdown.fours += 1
            elif r == 6:
                breakdown.sixes += 1

        # Check dismissal
        if d.get("dismissed_player_id") == player_id and d.get("is_wicket"):
            breakdown.is_dismissed = True
            breakdown.dismissal_kind = d.get("dismissal_kind")

        # Bowling
        if d.get("bowler_id") == player_id:
            over_num = d.get("over_number", 0)
            overs_seen.add(over_num)
            xtype = d.get("extra_type")
            r_bat = d.get("runs_batter", 0)
            r_ext = d.get("runs_extras", 0)

            # Wides and no-balls add to bowler runs conceded
            bowler_runs = r_bat
            if xtype in ("wide", "noball"):
                bowler_runs += r_ext

            breakdown.runs_conceded += bowler_runs
            maiden_over_runs[over_num] = maiden_over_runs.get(over_num, 0) + bowler_runs

            # Legal balls count
            if xtype not in ("wide", "noball"):
                breakdown.balls_bowled += 1
                maiden_over_balls[over_num] = maiden_over_balls.get(over_num, 0) + 1

            # Check wickets
            if d.get("is_wicket") and d.get("dismissal_kind") != "run out":
                breakdown.wickets += 1
                if d.get("dismissal_kind") in ("bowled", "lbw"):
                    breakdown.bowled_or_lbw_count += 1

        # Fielding
        if d.get("fielder_id") == player_id and d.get("is_wicket"):
            kind = d.get("dismissal_kind")
            if kind == "caught":
                breakdown.catches += 1
            elif kind == "stumped":
                breakdown.stumpings += 1
            elif kind == "run out":
                breakdown.run_outs += 1

    # --- Batting Points Calculation ---
    if breakdown.runs > 0:
        run_pts = breakdown.runs * float(bat_rules.get("run", 1.0))
        breakdown.batting_points += run_pts
        breakdown.events.append(
            PlayerEventBreakdown(description=f"{breakdown.runs} runs scored", points=run_pts, category="batting")
        )

    if breakdown.fours > 0:
        four_pts = breakdown.fours * float(bat_rules.get("boundary_four", 1.0))
        breakdown.batting_points += four_pts
        breakdown.events.append(
            PlayerEventBreakdown(description=f"{breakdown.fours} boundaries (4s)", points=four_pts, category="batting")
        )

    if breakdown.sixes > 0:
        six_pts = breakdown.sixes * float(bat_rules.get("boundary_six", 2.0))
        breakdown.batting_points += six_pts
        breakdown.events.append(
            PlayerEventBreakdown(description=f"{breakdown.sixes} sixes (6s)", points=six_pts, category="batting")
        )

    # Milestone bonuses
    if breakdown.runs >= 100:
        c_pts = float(bat_rules.get("century_bonus", 16.0))
        breakdown.bonus_points += c_pts
        breakdown.events.append(PlayerEventBreakdown(description="Century bonus (100+)", points=c_pts, category="bonus"))
    elif breakdown.runs >= 50:
        hc_pts = float(bat_rules.get("half_century_bonus", 8.0))
        breakdown.bonus_points += hc_pts
        breakdown.events.append(PlayerEventBreakdown(description="Half-century bonus (50+)", points=hc_pts, category="bonus"))
    elif breakdown.runs >= 30:
        t_pts = float(bat_rules.get("thirty_run_bonus", 4.0))
        breakdown.bonus_points += t_pts
        breakdown.events.append(PlayerEventBreakdown(description="30-run bonus", points=t_pts, category="bonus"))

    # Duck penalty (dismissed for 0 runs, applies to BAT, AR, WK)
    if breakdown.is_dismissed and breakdown.runs == 0 and breakdown.role in ("BAT", "AR", "WK"):
        d_pen = float(bat_rules.get("duck_penalty", -2.0))
        breakdown.penalty_points += d_pen
        breakdown.events.append(
            PlayerEventBreakdown(description=f"Dismissed for duck ({breakdown.dismissal_kind})", points=d_pen, category="penalty")
        )

    # Strike rate bonus / penalty
    sr_rules = bat_rules.get("strike_rate", {})
    min_balls_sr = sr_rules.get("min_balls_faced", 10)
    if breakdown.balls_faced >= min_balls_sr:
        sr = (breakdown.runs / breakdown.balls_faced) * 100.0
        for tier in sr_rules.get("tiers", []):
            min_r = tier.get("min_rate", float("-inf"))
            max_r = tier.get("max_rate", float("inf"))
            if min_r <= sr <= max_r or (tier.get("min_rate") is not None and sr >= min_r and "max_rate" not in tier):
                tier_pts = float(tier["bonus"])
                if tier_pts > 0:
                    breakdown.bonus_points += tier_pts
                    breakdown.events.append(
                        PlayerEventBreakdown(description=f"High strike rate bonus ({sr:.1f} SR)", points=tier_pts, category="bonus")
                    )
                elif tier_pts < 0:
                    breakdown.penalty_points += tier_pts
                    breakdown.events.append(
                        PlayerEventBreakdown(description=f"Low strike rate penalty ({sr:.1f} SR)", points=tier_pts, category="penalty")
                    )
                break

    # --- Bowling Points Calculation ---
    # Overs bowled
    complete_overs = breakdown.balls_bowled // 6
    partial_balls = breakdown.balls_bowled % 6
    breakdown.overs_bowled = float(f"{complete_overs}.{partial_balls}")

    # Maidens: over with 6 legal balls and 0 runs conceded
    for o_num, b_count in maiden_over_balls.items():
        if b_count >= 6 and maiden_over_runs.get(o_num, 0) == 0:
            breakdown.maidens += 1

    if breakdown.maidens > 0:
        m_pts = breakdown.maidens * float(bowl_rules.get("maiden_over", 12.0))
        breakdown.bowling_points += m_pts
        breakdown.events.append(
            PlayerEventBreakdown(description=f"{breakdown.maidens} maiden over(s)", points=m_pts, category="bowling")
        )

    if breakdown.wickets > 0:
        w_pts = breakdown.wickets * float(bowl_rules.get("wicket_excluding_runout", 25.0))
        breakdown.bowling_points += w_pts
        breakdown.events.append(
            PlayerEventBreakdown(description=f"{breakdown.wickets} wicket(s)", points=w_pts, category="bowling")
        )

    if breakdown.bowled_or_lbw_count > 0:
        blbw_pts = breakdown.bowled_or_lbw_count * float(bowl_rules.get("bowled_or_lbw_bonus", 8.0))
        breakdown.bonus_points += blbw_pts
        breakdown.events.append(
            PlayerEventBreakdown(
                description=f"{breakdown.bowled_or_lbw_count} bowled/LBW bonus", points=blbw_pts, category="bonus"
            )
        )

    # Bowling milestones
    if breakdown.wickets >= 5:
        w5_pts = float(bowl_rules.get("five_wicket_bonus", 16.0))
        breakdown.bonus_points += w5_pts
        breakdown.events.append(PlayerEventBreakdown(description="5-wicket haul bonus", points=w5_pts, category="bonus"))
    elif breakdown.wickets >= 4:
        w4_pts = float(bowl_rules.get("four_wicket_bonus", 8.0))
        breakdown.bonus_points += w4_pts
        breakdown.events.append(PlayerEventBreakdown(description="4-wicket haul bonus", points=w4_pts, category="bonus"))
    elif breakdown.wickets >= 3:
        w3_pts = float(bowl_rules.get("three_wicket_bonus", 4.0))
        breakdown.bonus_points += w3_pts
        breakdown.events.append(PlayerEventBreakdown(description="3-wicket haul bonus", points=w3_pts, category="bonus"))

    # Economy rate (min 2.0 overs bowled)
    econ_rules = bowl_rules.get("economy_rate", {})
    min_overs_econ = float(econ_rules.get("min_overs_bowled", 2.0))
    overs_float = breakdown.balls_bowled / 6.0
    if overs_float >= min_overs_econ:
        econ = breakdown.runs_conceded / overs_float
        for tier in econ_rules.get("tiers", []):
            min_r = tier.get("min_rate", float("-inf"))
            max_r = tier.get("max_rate", float("inf"))
            if min_r <= econ <= max_r or (tier.get("min_rate") is not None and econ >= min_r and "max_rate" not in tier):
                tier_pts = float(tier["bonus"])
                if tier_pts > 0:
                    breakdown.bonus_points += tier_pts
                    breakdown.events.append(
                        PlayerEventBreakdown(description=f"Economy bonus ({econ:.2f} RPO)", points=tier_pts, category="bonus")
                    )
                elif tier_pts < 0:
                    breakdown.penalty_points += tier_pts
                    breakdown.events.append(
                        PlayerEventBreakdown(description=f"High economy penalty ({econ:.2f} RPO)", points=tier_pts, category="penalty")
                    )
                break

    # --- Fielding Points Calculation ---
    if breakdown.catches > 0:
        c_pts = breakdown.catches * float(field_rules.get("catch", 8.0))
        breakdown.fielding_points += c_pts
        breakdown.events.append(
            PlayerEventBreakdown(description=f"{breakdown.catches} catch(es)", points=c_pts, category="fielding")
        )
        if breakdown.catches >= 3:
            c3_pts = float(field_rules.get("three_catch_bonus", 4.0))
            breakdown.bonus_points += c3_pts
            breakdown.events.append(PlayerEventBreakdown(description="3 catches bonus", points=c3_pts, category="bonus"))

    if breakdown.stumpings > 0:
        s_pts = breakdown.stumpings * float(field_rules.get("stumping", 12.0))
        breakdown.fielding_points += s_pts
        breakdown.events.append(
            PlayerEventBreakdown(description=f"{breakdown.stumpings} stumping(s)", points=s_pts, category="fielding")
        )

    if breakdown.run_outs > 0:
        ro_pts = breakdown.run_outs * float(field_rules.get("run_out_direct", 12.0))
        breakdown.fielding_points += ro_pts
        breakdown.events.append(
            PlayerEventBreakdown(description=f"{breakdown.run_outs} run-out(s)", points=ro_pts, category="fielding")
        )

    # --- Total points and Multiplier ---
    breakdown.base_points = (
        breakdown.starting_xi_points
        + breakdown.batting_points
        + breakdown.bowling_points
        + breakdown.fielding_points
        + breakdown.bonus_points
        + breakdown.penalty_points
    )

    if breakdown.is_captain:
        breakdown.multiplier = float(mult_rules.get("captain", 2.0))
    elif breakdown.is_vice_captain:
        breakdown.multiplier = float(mult_rules.get("vice_captain", 1.5))
    else:
        breakdown.multiplier = float(mult_rules.get("normal", 1.0))

    breakdown.total_points = round(breakdown.base_points * breakdown.multiplier, 2)
    return breakdown


def calculate_team_points(
    team_id: str,
    team_name: str,
    team_players: list[dict[str, Any]],  # [{id, name, role, team, is_captain, is_vice_captain}]
    deliveries: list[dict[str, Any]],
    over_number: int,
    rules: Optional[dict[str, Any]] = None,
) -> TeamScoreBreakdown:
    """Calculates deterministic points for an entire fantasy team up to over_number."""
    # Filter deliveries strictly up to over_number
    # Over 0 means no match deliveries yet
    active_deliveries = [d for d in deliveries if d.get("over_number", 0) <= over_number] if over_number > 0 else []

    team_breakdown = TeamScoreBreakdown(
        team_id=team_id,
        team_name=team_name,
        over_number=over_number,
    )

    for p in team_players:
        p_breakdown = calculate_player_points(
            player_id=p["id"],
            player_name=p["name"],
            role=p["role"],
            team=p["team"],
            deliveries=active_deliveries,
            is_captain=p.get("is_captain", False),
            is_vice_captain=p.get("is_vice_captain", False),
            is_playing_xi=p.get("is_playing_xi", True),
            rules=rules,
        )
        team_breakdown.players.append(p_breakdown)
        team_breakdown.total_points += p_breakdown.total_points

    team_breakdown.total_points = round(team_breakdown.total_points, 2)
    return team_breakdown
