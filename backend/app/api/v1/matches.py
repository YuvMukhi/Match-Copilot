from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.models import Delivery, FantasyTeam, Match, Player
from app.db.session import get_db
from app.schemas.match import (
    MatchDeliverySummary,
    MatchStateResponse,
    MatchSummary,
)
from app.services.explain_service import get_team_players_for_db
from app.services.scoring_engine import calculate_team_points

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchSummary])
def list_matches(db: Session = Depends(get_db)) -> list[MatchSummary]:
    matches = db.query(Match).all()
    return [
        MatchSummary(
            id=m.id,
            name=m.name,
            short_name=m.short_name,
            team1=m.team1,
            team2=m.team2,
            venue=m.venue,
            status=m.status,
            current_innings=m.current_innings,
            total_overs=m.total_overs,
        )
        for m in matches
    ]


@router.get("/{match_id}", response_model=MatchSummary)
def get_match(match_id: str, db: Session = Depends(get_db)) -> MatchSummary:
    m = db.query(Match).filter_by(id=match_id).first()
    if not m:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id '{match_id}' not found",
        )
    return MatchSummary(
        id=m.id,
        name=m.name,
        short_name=m.short_name,
        team1=m.team1,
        team2=m.team2,
        venue=m.venue,
        status=m.status,
        current_innings=m.current_innings,
        total_overs=m.total_overs,
    )


@router.get("/{match_id}/state", response_model=MatchStateResponse)
def get_match_state(
    match_id: str,
    over: int = Query(default=10, ge=0, le=20, description="Match moment over (0-20)"),
    team_id: Optional[str] = Query(default="team_001", description="Fantasy team id for score overlay"),
    db: Session = Depends(get_db),
) -> MatchStateResponse:
    match = db.query(Match).filter_by(id=match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id '{match_id}' not found",
        )

    # Fetch deliveries up to this over
    all_deliveries = (
        db.query(Delivery)
        .filter_by(match_id=match_id)
        .order_by(Delivery.innings, Delivery.over_number, Delivery.ball_in_over)
        .all()
    )

    active_delivs = [d for d in all_deliveries if d.over_number <= over] if over > 0 else []

    # Match tally
    runs = sum(d.runs_batter + d.runs_extras for d in active_delivs)
    wickets = sum(1 for d in active_delivs if d.is_wicket)
    run_rate = round(runs / over, 2) if over > 0 else 0.0

    # Determine current bowler and batters from the last few balls
    players_cache = {p.id: p.name for p in db.query(Player).all()}

    current_bowler_name = "Not started"
    current_batters: list[str] = []

    if active_delivs:
        last_ball = active_delivs[-1]
        current_bowler_name = players_cache.get(last_ball.bowler_id, last_ball.bowler_id)
        b1 = players_cache.get(last_ball.batter_id, last_ball.batter_id)
        b2 = players_cache.get(last_ball.non_striker_id, last_ball.non_striker_id)
        current_batters = [b1, b2]

    # Recent deliveries (up to 6)
    recent_delivs_objs = active_delivs[-6:] if active_delivs else []
    recent_summaries: list[MatchDeliverySummary] = []
    for d in recent_delivs_objs:
        txt = str(d.runs_batter)
        if d.is_wicket:
            txt = f"W ({d.dismissal_kind or 'out'})"
        elif d.extra_type:
            txt = f"{d.runs_extras}{d.extra_type[0].upper()}"

        recent_summaries.append(
            MatchDeliverySummary(
                over_number=d.over_number,
                ball_in_over=d.ball_in_over,
                bowler_name=players_cache.get(d.bowler_id, d.bowler_id),
                batter_name=players_cache.get(d.batter_id, d.batter_id),
                runs_batter=d.runs_batter,
                runs_extras=d.runs_extras,
                extra_type=d.extra_type,
                is_wicket=d.is_wicket,
                dismissal_kind=d.dismissal_kind,
                display_text=txt,
            )
        )

    # Calculate fantasy team points if team_id provided
    team_points: Optional[float] = None
    team_breakdown_list: Optional[list[dict]] = None

    if team_id:
        team = db.query(FantasyTeam).filter_by(id=team_id).first()
        if team:
            t_players = get_team_players_for_db(db, team_id)
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
                for d in all_deliveries
            ]
            t_score = calculate_team_points(
                team_id=team.id,
                team_name=team.name,
                team_players=t_players,
                deliveries=d_dicts,
                over_number=over,
            )
            team_points = t_score.total_points
            team_breakdown_list = [
                {
                    "player_id": p.player_id,
                    "player_name": p.player_name,
                    "role": p.role,
                    "is_captain": p.is_captain,
                    "is_vice_captain": p.is_vice_captain,
                    "multiplier": p.multiplier,
                    "total_points": p.total_points,
                    "runs": p.runs,
                    "wickets": p.wickets,
                    "events": [e.description for e in p.events],
                }
                for p in t_score.players
            ]

    return MatchStateResponse(
        match_id=match.id,
        match_name=match.name,
        over=over,
        total_overs=match.total_overs,
        runs=runs,
        wickets=wickets,
        run_rate=run_rate,
        current_batters=current_batters,
        current_bowler=current_bowler_name,
        recent_balls=recent_summaries,
        team_points=team_points,
        team_breakdown=team_breakdown_list,
    )
