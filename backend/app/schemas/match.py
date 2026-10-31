from typing import Any, Optional

from pydantic import BaseModel


class MatchSummary(BaseModel):
    id: str
    name: str
    short_name: str
    team1: str
    team2: str
    venue: str
    status: str
    current_innings: int
    total_overs: int


class MatchDeliverySummary(BaseModel):
    over_number: int
    ball_in_over: int
    bowler_name: str
    batter_name: str
    runs_batter: int
    runs_extras: int
    extra_type: Optional[str] = None
    is_wicket: bool
    dismissal_kind: Optional[str] = None
    display_text: str


class MatchStateResponse(BaseModel):
    match_id: str
    match_name: str
    over: int
    total_overs: int
    runs: int
    wickets: int
    run_rate: float
    current_batters: list[str]
    current_bowler: str
    recent_balls: list[MatchDeliverySummary]
    team_points: Optional[float] = None
    team_breakdown: Optional[list[dict[str, Any]]] = None
