import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Delivery, FantasyTeam, FantasyTeamPlayer, Match, Player
from app.db.seed import PLAYERS_DATA, SAMPLE_TEAMS, generate_20_overs_deliveries
from app.db.session import Base
from app.services.advisor_service import advise_team_lineup
from app.services.explain_service import explain_points_change


@pytest.fixture
def service_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    for p in PLAYERS_DATA:
        session.add(Player(**p))

    match = Match(
        id="match_001",
        name="MI VS CSK",
        short_name="MI vs CSK",
        team1="MI",
        team2="CSK",
        venue="Wankhede Stadium, Mumbai",
        status="in_progress",
        current_innings=1,
        total_overs=20,
    )
    session.add(match)

    deliveries = generate_20_overs_deliveries("match_001")
    for d in deliveries:
        session.add(Delivery(**d))

    for t in SAMPLE_TEAMS:
        ft = FantasyTeam(id=t["id"], name=t["name"], user_name=t["user_name"])
        session.add(ft)
        for p_id in t["players"]:
            session.add(
                FantasyTeamPlayer(
                    team_id=t["id"],
                    player_id=p_id,
                    is_captain=(p_id == t["captain"]),
                    is_vice_captain=(p_id == t["vice_captain"]),
                )
            )

    session.commit()
    yield session
    session.close()


def test_explain_service_points_gain(service_db_session):
    # In Over 3: Ishan hits boundary then gets caught by Dhoni
    result = explain_points_change(
        session=service_db_session,
        match_id="match_001",
        team_id="team_001",
        current_over=3,
        compare_over=2,
    )
    assert result.current_over == 3
    assert result.compare_over == 2
    assert result.net_points_change != 0
    assert len(result.player_changes) == 11
    assert len(result.evidence_table) == 11
    assert len(result.summary_narrative) > 0


def test_explain_service_over_zero_to_five(service_db_session):
    # From match start to end of over 5
    result = explain_points_change(
        session=service_db_session,
        match_id="match_001",
        team_id="team_001",
        current_over=5,
        compare_over=0,
    )
    assert result.current_total_points > result.previous_total_points
    assert result.net_points_change > 0


def test_advisor_service_captain_switch(service_db_session):
    # Over 10: Rohit Sharma is dismissed, team_001 has Rohit as captain
    res = advise_team_lineup(
        session=service_db_session,
        match_id="match_001",
        team_id="team_001",
        current_over=10,
    )
    assert res.current_captain == "Rohit Sharma"
    assert res.should_change_captain is True
    assert len(res.suggestions) >= 1
    assert len(res.player_rankings) == 11
    assert len(res.evidence_table) == 11
    assert "SWITCH" in res.summary_narrative
