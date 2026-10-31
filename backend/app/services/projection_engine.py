"""Deterministic projection engine for fantasy cricket.

Projects rest-of-match points as ranges (low, expected, high),
detects player risks (out, quota exhausted), and ranks players for captaincy advice.
Pure functions with mathematical transparency.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from app.services.scoring_engine import (
    calculate_player_points,
    load_scoring_rules,
)


@dataclass
class PlayerProjection:
    player_id: str
    player_name: str
    role: str
    team: str
    is_captain: bool
    is_vice_captain: bool
    current_points: float

    # Rest-of-match projections (base, before captaincy multiplier)
    remaining_low: float
    remaining_expected: float
    remaining_high: float

    # Total match projections (with current multiplier applied)
    projected_total_low: float
    projected_total_expected: float
    projected_total_high: float

    # Captaincy potential if captain (2.0x on remaining)
    captaincy_potential_expected: float

    # Risk flags and match context
    is_out: bool = False
    quota_exhausted: bool = False
    overs_bowled: float = 0.0
    remaining_quota: float = 0.0
    risk_tags: list[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class CaptaincyAdvice:
    current_captain_id: str
    current_captain_name: str
    current_vc_id: str
    current_vc_name: str
    recommended_captain_id: str
    recommended_captain_name: str
    recommended_vc_id: str
    recommended_vc_name: str
    should_change_captain: bool
    suggestions: list[str] = field(default_factory=list)
    ranked_players: list[PlayerProjection] = field(default_factory=list)


def project_player_rest_of_match(
    player: dict[str, Any],
    deliveries: list[dict[str, Any]],
    current_over: int,
    total_overs: int = 20,
    rules: Optional[dict[str, Any]] = None,
) -> PlayerProjection:
    """Projects remaining points for a player from current_over to total_overs."""
    if rules is None:
        rules = load_scoring_rules()

    # Deliveries up to current_over
    active_deliveries = [d for d in deliveries if d.get("over_number", 0) <= current_over] if current_over > 0 else []

    current_score = calculate_player_points(
        player_id=player["id"],
        player_name=player["name"],
        role=player["role"],
        team=player["team"],
        deliveries=active_deliveries,
        is_captain=player.get("is_captain", False),
        is_vice_captain=player.get("is_vice_captain", False),
        is_playing_xi=player.get("is_playing_xi", True),
        rules=rules,
    )

    remaining_overs_match = max(0, total_overs - current_over)
    role = player["role"]

    is_out = current_score.is_dismissed
    overs_bowled = current_score.overs_bowled
    # Standard T20 quota is 4 overs per bowler
    max_quota = 4.0 if total_overs >= 20 else max(1.0, round(total_overs * 0.2))
    remaining_quota = max(0.0, max_quota - overs_bowled)
    quota_exhausted = remaining_quota <= 0.0

    risk_tags: list[str] = []
    reasoning_parts: list[str] = []

    # Calculate remaining batting potential
    rem_bat_low = 0.0
    rem_bat_expected = 0.0
    rem_bat_high = 0.0

    if remaining_overs_match == 0:
        # Match already completed
        rem_bat_low = rem_bat_expected = rem_bat_high = 0.0
        reasoning_parts.append("Match innings finished; 0 overs remaining.")
    elif is_out:
        risk_tags.append("Batter already dismissed")
        reasoning_parts.append(f"Dismissed ({current_score.dismissal_kind}); no further batting points possible.")
    else:
        # Player is batting or yet to bat
        if role in ("BAT", "WK", "AR"):
            # Batting capacity factor based on overs left
            # Expected runs per remaining over in death / middle
            base_rate = 1.6 if current_over >= 15 else 1.3
            expected_balls = min(remaining_overs_match * 3.5, 24.0)

            rem_bat_low = round(expected_balls * 0.6, 1)
            rem_bat_expected = round(expected_balls * base_rate, 1)
            rem_bat_high = round(expected_balls * 2.4 + 12.0, 1)  # ceiling with boundaries/bonus
            reasoning_parts.append(f"Active batter with {remaining_overs_match} overs left.")

    # Calculate remaining bowling potential
    rem_bowl_low = 0.0
    rem_bowl_expected = 0.0
    rem_bowl_high = 0.0

    if remaining_overs_match == 0:
        rem_bowl_low = rem_bowl_expected = rem_bowl_high = 0.0
    elif role in ("BOWL", "AR"):
        if quota_exhausted:
            risk_tags.append(f"Quota exhausted ({overs_bowled:.1f}/{max_quota:.0f} overs)")
            reasoning_parts.append("Completed bowling quota; cannot bowl more overs.")
        else:
            avail_overs = min(remaining_quota, float(remaining_overs_match))
            # Average T20 wicket rate ~ 0.35 wickets per over, plus economy
            rem_bowl_low = round(avail_overs * 1.5, 1)
            rem_bowl_expected = round(avail_overs * 7.5, 1)  # ~0.25 wickets + dot balls/econ
            rem_bowl_high = round(avail_overs * 18.0 + 25.0, 1)  # 1-2 wickets + bonus
            reasoning_parts.append(f"{avail_overs:.1f} overs quota remaining.")

    # Fielding expectation
    fielding_exp = round(min(remaining_overs_match * 0.3, 2.0) * 8.0, 1) if remaining_overs_match > 0 else 0.0

    rem_low = round(rem_bat_low + rem_bowl_low, 1)
    rem_expected = round(rem_bat_expected + rem_bowl_expected + (fielding_exp * 0.5), 1)
    rem_high = round(rem_bat_high + rem_bowl_high + fielding_exp, 1)

    multiplier = current_score.multiplier
    proj_total_low = round(current_score.total_points + (rem_low * multiplier), 1)
    proj_total_exp = round(current_score.total_points + (rem_expected * multiplier), 1)
    proj_total_high = round(current_score.total_points + (rem_high * multiplier), 1)

    # What if they were captain (2.0x)?
    cap_potential = round(current_score.base_points + (rem_expected * 2.0), 1)

    return PlayerProjection(
        player_id=player["id"],
        player_name=player["name"],
        role=player["role"],
        team=player["team"],
        is_captain=player.get("is_captain", False),
        is_vice_captain=player.get("is_vice_captain", False),
        current_points=current_score.total_points,
        remaining_low=rem_low,
        remaining_expected=rem_expected,
        remaining_high=rem_high,
        projected_total_low=proj_total_low,
        projected_total_expected=proj_total_exp,
        projected_total_high=proj_total_high,
        captaincy_potential_expected=cap_potential,
        is_out=is_out,
        quota_exhausted=quota_exhausted,
        overs_bowled=overs_bowled,
        remaining_quota=remaining_quota,
        risk_tags=risk_tags,
        reasoning="; ".join(reasoning_parts),
    )


def rank_and_advise_captain(
    team_players: list[dict[str, Any]],
    deliveries: list[dict[str, Any]],
    current_over: int,
    total_overs: int = 20,
    rules: Optional[dict[str, Any]] = None,
) -> CaptaincyAdvice:
    """Ranks fantasy team players by projected points and provides 2-3 tactical fixes."""
    if rules is None:
        rules = load_scoring_rules()

    projections: list[PlayerProjection] = [
        project_player_rest_of_match(p, deliveries, current_over, total_overs, rules)
        for p in team_players
    ]

    # Rank by captaincy potential (projected total if given 2x)
    ranked = sorted(projections, key=lambda p: p.captaincy_potential_expected, reverse=True)

    curr_cap = next((p for p in projections if p.is_captain), None)
    curr_vc = next((p for p in projections if p.is_vice_captain), None)

    curr_cap_id = curr_cap.player_id if curr_cap else ""
    curr_cap_name = curr_cap.player_name if curr_cap else "None"
    curr_vc_id = curr_vc.player_id if curr_vc else ""
    curr_vc_name = curr_vc.player_name if curr_vc else "None"

    rec_cap = ranked[0] if ranked else None
    rec_vc = ranked[1] if len(ranked) > 1 else None

    rec_cap_id = rec_cap.player_id if rec_cap else curr_cap_id
    rec_cap_name = rec_cap.player_name if rec_cap else curr_cap_name
    rec_vc_id = rec_vc.player_id if rec_vc else curr_vc_id
    rec_vc_name = rec_vc.player_name if rec_vc else curr_vc_name

    should_change = False
    suggestions: list[str] = []

    # Analyze current captain
    if curr_cap:
        if curr_cap.is_out:
            should_change = True
            suggestions.append(
                f"🚨 Critical Fix: Your captain {curr_cap.player_name} is already dismissed. "
                f"They cannot earn further batting points. Switch captaincy to {rec_cap_name}."
            )
        elif curr_cap.quota_exhausted:
            should_change = True
            suggestions.append(
                f"⚠️ Quota Warning: Your captain {curr_cap.player_name} has completed their 4-over bowling quota. "
                f"Switch to an active batter or death bowler like {rec_cap_name}."
            )
        elif rec_cap and rec_cap.player_id != curr_cap.player_id:
            point_diff = round(rec_cap.captaincy_potential_expected - curr_cap.captaincy_potential_expected, 1)
            if point_diff >= 12.0:
                should_change = True
                suggestions.append(
                    f"📈 Value Upgrade: {rec_cap_name} has an expected +{point_diff} higher points potential "
                    f"due to remaining death overs/quota. Consider promoting {rec_cap_name} to Captain."
                )

    # Analyze Vice-Captain
    if curr_vc and rec_vc and curr_vc.player_id != rec_vc.player_id:
        if curr_vc.is_out or curr_vc.quota_exhausted:
            suggestions.append(
                f"🔄 Vice-Captain Tuning: {curr_vc.player_name} has limited remaining upside ({', '.join(curr_vc.risk_tags) or 'completed participation'}). "
                f"Move VC to {rec_vc.player_name} ({rec_vc.remaining_expected} exp remaining pts)."
            )

    if not suggestions:
        suggestions.append(
            f"✅ Solid Selection: Your captain {curr_cap_name} remains optimal for the current match conditions."
        )

    return CaptaincyAdvice(
        current_captain_id=curr_cap_id,
        current_captain_name=curr_cap_name,
        current_vc_id=curr_vc_id,
        current_vc_name=curr_vc_name,
        recommended_captain_id=rec_cap_id,
        recommended_captain_name=rec_cap_name,
        recommended_vc_id=rec_vc_id,
        recommended_vc_name=rec_vc_name,
        should_change_captain=should_change,
        suggestions=suggestions[:3],
        ranked_players=ranked,
    )
