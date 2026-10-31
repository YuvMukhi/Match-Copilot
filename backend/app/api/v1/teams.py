from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.models import Delivery, FantasyTeam
from app.db.session import get_db
from app.schemas.team import PlayerInTeam, TeamDetail, TeamSummary
from app.services.explain_service import get_team_players_for_db
from app.services.scoring_engine import calculate_team_points

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamSummary])
def list_teams(db: Session = Depends(get_db)) -> list[TeamSummary]:
    teams = db.query(FantasyTeam).all()
    return [
        TeamSummary(
            id=t.id,
            name=t.name,
            user_name=t.user_name,
            player_count=len(t.players),
        )
        for t in teams
    ]


@router.get("/{team_id}", response_model=TeamDetail)
def get_team(
    team_id: str,
    over: Optional[int] = Query(default=10, ge=0, le=20),
    db: Session = Depends(get_db),
) -> TeamDetail:
    team = db.query(FantasyTeam).filter_by(id=team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fantasy team with id '{team_id}' not found",
        )

    team_players = get_team_players_for_db(db, team_id)
    deliveries = db.query(Delivery).filter_by(match_id="match_001").all()
    d_dicts = [
        {
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

    t_score = calculate_team_points(
        team_id=team.id,
        team_name=team.name,
        team_players=team_players,
        deliveries=d_dicts,
        over_number=over if over is not None else 10,
    )

    cap_name = "None"
    vc_name = "None"
    player_entries: list[PlayerInTeam] = []

    p_scores_map = {p.player_id: p.total_points for p in t_score.players}

    for ftp in team.players:
        p = ftp.player
        if ftp.is_captain:
            cap_name = p.name
        if ftp.is_vice_captain:
            vc_name = p.name

        player_entries.append(
            PlayerInTeam(
                id=p.id,
                name=p.name,
                team=p.team,
                role=p.role,
                credits=p.credits,
                is_captain=ftp.is_captain,
                is_vice_captain=ftp.is_vice_captain,
                current_points=p_scores_map.get(p.id, 0.0),
            )
        )

    return TeamDetail(
        id=team.id,
        name=team.name,
        user_name=team.user_name,
        captain_name=cap_name,
        vice_captain_name=vc_name,
        total_points=t_score.total_points,
        players=player_entries,
    )
