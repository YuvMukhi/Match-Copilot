from typing import Optional

from pydantic import BaseModel


class PlayerInTeam(BaseModel):
    id: str
    name: str
    team: str
    role: str
    credits: float
    is_captain: bool
    is_vice_captain: bool
    current_points: Optional[float] = 0.0


class TeamSummary(BaseModel):
    id: str
    name: str
    user_name: str
    player_count: int = 11


class TeamDetail(BaseModel):
    id: str
    name: str
    user_name: str
    captain_name: str
    vice_captain_name: str
    total_points: float = 0.0
    players: list[PlayerInTeam]
