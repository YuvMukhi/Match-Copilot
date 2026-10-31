"""Explain service for fantasy cricket points breakdown.

Answers: "Why did I lose/gain points?"
Compares fantasy team points between two match moments (e.g. over N vs over M)
and traces every single point change to exact match events.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.db.models import Delivery, FantasyTeam, Match
from app.services.scoring_engine import (
    TeamScoreBreakdown,
    calculate_team_points,
    load_scoring_rules,
)


@dataclass
class PlayerDeltaCause:
    player_id: str
    player_name: str
    role: str
    team: str
    is_captain: bool
    is_vice_captain: bool
    multiplier: float
    previous_points: float
    current_points: float
    delta_points: float
    causes: list[str] = field(default_factory=list)


@dataclass
class PointsExplanationResult:
    match_id: str
    match_name: str
    team_id: str
    team_name: str
    current_over: int
    compare_over: int
    previous_total_points: float
    current_total_points: float
    net_points_change: float
    player_changes: list[PlayerDeltaCause] = field(default_factory=list)
    significant_events: list[str] = field(default_factory=list)
    summary_narrative: str = ""
    evidence_table: list[dict[str, Any]] = field(default_factory=list)


def get_team_players_for_db(session: Session, team_id: str) -> list[dict[str, Any]]:
    team = session.query(FantasyTeam).filter_by(id=team_id).first()
    if not team:
        raise ValueError(f"Team {team_id} not found")

    players_data = []
    for ftp in team.players:
        p = ftp.player
        players_data.append({
            "id": p.id,
            "name": p.name,
            "role": p.role,
            "team": p.team,
            "is_captain": ftp.is_captain,
            "is_vice_captain": ftp.is_vice_captain,
            "is_playing_xi": True,
        })
    return players_data


def get_match_deliveries_from_db(session: Session, match_id: str) -> list[dict[str, Any]]:
    deliveries = (
        session.query(Delivery)
        .filter_by(match_id=match_id)
        .order_by(Delivery.innings, Delivery.over_number, Delivery.ball_in_over)
        .all()
    )
    return [
        {
            "match_id": d.match_id,
            "innings": d.innings,
            "over_number": d.over_number,
            "ball_in_over": d.ball_in_over,
            "bowler_id": d.bowler_id,
            "batter_id": d.batter_id,
            "non_striker_id": d.non_striker_id,
            "runs_batter": d.runs_batter,
            "runs_extras": d.runs_extras,
            "extra_type": d.extra_type,
            "is_wicket": d.is_wicket,
            "dismissal_kind": d.dismissal_kind,
            "dismissed_player_id": d.dismissed_player_id,
            "fielder_id": d.fielder_id,
        }
        for d in deliveries
    ]


def explain_points_change(
    session: Session,
    match_id: str,
    team_id: str,
    current_over: int,
    compare_over: Optional[int] = None,
    rules: Optional[dict[str, Any]] = None,
) -> PointsExplanationResult:
    """Computes exact delta and reasons between compare_over and current_over."""
    if rules is None:
        rules = load_scoring_rules()

    if compare_over is None:
        compare_over = max(0, current_over - 1)
    if compare_over > current_over:
        compare_over, current_over = current_over, compare_over

    match = session.query(Match).filter_by(id=match_id).first()
    match_name = match.name if match else match_id
    team = session.query(FantasyTeam).filter_by(id=team_id).first()
    team_name = team.name if team else team_id

    team_players = get_team_players_for_db(session, team_id)
    deliveries = get_match_deliveries_from_db(session, match_id)

    curr_score: TeamScoreBreakdown = calculate_team_points(
        team_id, team_name, team_players, deliveries, current_over, rules
    )
    prev_score: TeamScoreBreakdown = calculate_team_points(
        team_id, team_name, team_players, deliveries, compare_over, rules
    )

    prev_player_map = {p.player_id: p for p in prev_score.players}

    # Intervening deliveries that caused this change
    interval_deliveries = [
        d for d in deliveries if compare_over < d.get("over_number", 0) <= current_over
    ]

    player_changes: list[PlayerDeltaCause] = []
    significant_events: list[str] = []
    evidence_rows: list[dict[str, Any]] = []

    for curr_p in curr_score.players:
        prev_p = prev_player_map.get(curr_p.player_id)
        prev_pts = prev_p.total_points if prev_p else 0.0
        delta = round(curr_p.total_points - prev_pts, 2)

        causes: list[str] = []
        if prev_p:
            runs_diff = curr_p.runs - prev_p.runs
            fours_diff = curr_p.fours - prev_p.fours
            sixes_diff = curr_p.sixes - prev_p.sixes
            wickets_diff = curr_p.wickets - prev_p.wickets
            catches_diff = curr_p.catches - prev_p.catches

            if runs_diff > 0:
                causes.append(f"+{runs_diff} runs")
            if fours_diff > 0:
                causes.append(f"+{fours_diff} boundary 4s (+{fours_diff} bonus)")
            if sixes_diff > 0:
                causes.append(f"+{sixes_diff} sixes (+{sixes_diff * 2} bonus)")
            if curr_p.is_dismissed and not prev_p.is_dismissed:
                if curr_p.runs == 0:
                    causes.append("Dismissed for duck (-2 pts)")
                else:
                    causes.append(f"Dismissed ({curr_p.dismissal_kind})")
            if wickets_diff > 0:
                causes.append(f"+{wickets_diff} wicket(s) (+{wickets_diff * 25} pts)")
            if catches_diff > 0:
                causes.append(f"+{catches_diff} catch(es) (+{catches_diff * 8} pts)")
            if curr_p.maidens > prev_p.maidens:
                causes.append(f"+{curr_p.maidens - prev_p.maidens} maiden over (+12 pts)")

        role_label = curr_p.role
        if curr_p.is_captain:
            role_label += " (C - 2.0x)"
        elif curr_p.is_vice_captain:
            role_label += " (VC - 1.5x)"

        change_entry = PlayerDeltaCause(
            player_id=curr_p.player_id,
            player_name=curr_p.player_name,
            role=role_label,
            team=curr_p.team,
            is_captain=curr_p.is_captain,
            is_vice_captain=curr_p.is_vice_captain,
            multiplier=curr_p.multiplier,
            previous_points=prev_pts,
            current_points=curr_p.total_points,
            delta_points=delta,
            causes=causes if causes else ["No scoring actions in this interval"],
        )
        player_changes.append(change_entry)

        # Tabular evidence
        evidence_rows.append({
            "Player": curr_p.player_name,
            "Role": role_label,
            f"Over {compare_over} Pts": prev_pts,
            f"Over {current_over} Pts": curr_p.total_points,
            "Delta": f"{'+' if delta > 0 else ''}{delta}",
            "Key Causes": ", ".join(causes) if causes else "Quiet over",
        })

    # Summary of significant interval events
    for d in interval_deliveries:
        if d.get("is_wicket"):
            significant_events.append(
                f"Over {d['over_number']}.{d['ball_in_over']}: WICKET! {d.get('dismissal_kind')} "
                f"(Bowler: {d['bowler_id']}, Batter: {d['batter_id']})"
            )
        elif d.get("runs_batter") == 6:
            significant_events.append(f"Over {d['over_number']}.{d['ball_in_over']}: SIX by {d['batter_id']}!")
        elif d.get("runs_batter") == 4:
            significant_events.append(f"Over {d['over_number']}.{d['ball_in_over']}: FOUR by {d['batter_id']}")

    net_change = round(curr_score.total_points - prev_score.total_points, 2)
    direction = "gained" if net_change >= 0 else "lost"
    summary = (
        f"Between Over {compare_over} and Over {current_over}, your team '{team_name}' {direction} "
        f"{abs(net_change)} points (from {prev_score.total_points} to {curr_score.total_points}). "
    )
    # Highlight top movers
    movers = sorted(player_changes, key=lambda x: abs(x.delta_points), reverse=True)
    if movers and movers[0].delta_points != 0:
        top = movers[0]
        sign = "+" if top.delta_points > 0 else ""
        summary += f"Main contributor: {top.player_name} ({sign}{top.delta_points} pts due to {', '.join(top.causes)})."

    return PointsExplanationResult(
        match_id=match_id,
        match_name=match_name,
        team_id=team_id,
        team_name=team_name,
        current_over=current_over,
        compare_over=compare_over,
        previous_total_points=prev_score.total_points,
        current_total_points=curr_score.total_points,
        net_points_change=net_change,
        player_changes=player_changes,
        significant_events=significant_events,
        summary_narrative=summary,
        evidence_table=evidence_rows,
    )
