"""Advisor service for fantasy cricket tactical captaincy and lineup advice.

Answers: "Should I change my captain?"
Deterministic ranking, risk detection, and actionable fixes.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.db.models import FantasyTeam, Match
from app.services.explain_service import (
    get_match_deliveries_from_db,
    get_team_players_for_db,
)
from app.services.projection_engine import (
    CaptaincyAdvice,
    rank_and_advise_captain,
)
from app.services.scoring_engine import load_scoring_rules


@dataclass
class AdvisorServiceResult:
    match_id: str
    match_name: str
    team_id: str
    team_name: str
    current_over: int
    current_captain: str
    current_vice_captain: str
    recommended_captain: str
    recommended_vice_captain: str
    should_change_captain: bool
    suggestions: list[str] = field(default_factory=list)
    player_rankings: list[dict[str, Any]] = field(default_factory=list)
    evidence_table: list[dict[str, Any]] = field(default_factory=list)
    summary_narrative: str = ""


def advise_team_lineup(
    session: Session,
    match_id: str,
    team_id: str,
    current_over: int,
    total_overs: int = 20,
    rules: Optional[dict[str, Any]] = None,
) -> AdvisorServiceResult:
    """Evaluates team captaincy and projected point upside for rest of match."""
    if rules is None:
        rules = load_scoring_rules()

    match = session.query(Match).filter_by(id=match_id).first()
    match_name = match.name if match else match_id
    team = session.query(FantasyTeam).filter_by(id=team_id).first()
    team_name = team.name if team else team_id

    team_players = get_team_players_for_db(session, team_id)
    deliveries = get_match_deliveries_from_db(session, match_id)

    raw_advice: CaptaincyAdvice = rank_and_advise_captain(
        team_players=team_players,
        deliveries=deliveries,
        current_over=current_over,
        total_overs=total_overs,
        rules=rules,
    )

    rankings_data: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []

    for rank, p_proj in enumerate(raw_advice.ranked_players, 1):
        role_label = p_proj.role
        if p_proj.is_captain:
            role_label += " (Current C)"
        elif p_proj.is_vice_captain:
            role_label += " (Current VC)"

        status_str = "Active"
        if p_proj.is_out:
            status_str = "OUT"
        elif p_proj.quota_exhausted:
            status_str = "Quota Done"

        p_dict = {
            "rank": rank,
            "player_id": p_proj.player_id,
            "player_name": p_proj.player_name,
            "role": role_label,
            "team": p_proj.team,
            "current_points": p_proj.current_points,
            "projected_remaining": f"{p_proj.remaining_low} - {p_proj.remaining_high} (Exp: {p_proj.remaining_expected})",
            "captaincy_potential": p_proj.captaincy_potential_expected,
            "status": status_str,
            "risks": p_proj.risk_tags,
            "notes": p_proj.reasoning,
        }
        rankings_data.append(p_dict)

        evidence_rows.append({
            "Rank": f"#{rank}",
            "Player": p_proj.player_name,
            "Role": role_label,
            "Current Pts": p_proj.current_points,
            "Exp Rem Pts": p_proj.remaining_expected,
            "If Captain (2x)": p_proj.captaincy_potential_expected,
            "Status & Risks": ", ".join(p_proj.risk_tags) if p_proj.risk_tags else "Optimal",
        })

    # Summary narrative
    if raw_advice.should_change_captain:
        narrative = (
            f"At Over {current_over}, you should SWITCH your captain from {raw_advice.current_captain_name} "
            f"to {raw_advice.recommended_captain_name}. {raw_advice.suggestions[0]}"
        )
    else:
        narrative = (
            f"At Over {current_over}, your captain {raw_advice.current_captain_name} remains optimal. "
            f"{raw_advice.suggestions[0]}"
        )

    return AdvisorServiceResult(
        match_id=match_id,
        match_name=match_name,
        team_id=team_id,
        team_name=team_name,
        current_over=current_over,
        current_captain=raw_advice.current_captain_name,
        current_vice_captain=raw_advice.current_vc_name,
        recommended_captain=raw_advice.recommended_captain_name,
        recommended_vice_captain=raw_advice.recommended_vc_name,
        should_change_captain=raw_advice.should_change_captain,
        suggestions=raw_advice.suggestions,
        player_rankings=rankings_data,
        evidence_table=evidence_rows,
        summary_narrative=narrative,
    )
