import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Delivery, FantasyTeam, Match, Player
from app.db.seed import PLAYERS_DATA, SAMPLE_TEAMS, generate_20_overs_deliveries
from app.db.session import Base


@pytest.fixture
def test_db_session():
    # In-memory SQLite for isolated tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed
    for p in PLAYERS_DATA:
        session.add(Player(**p))

    match = Match(
        id="match_test",
        name="Test Match",
        short_name="TM vs TM2",
        team1="Mumbai Titans",
        team2="Chennai Superstars",
        venue="Test Venue",
        status="in_progress",
        current_innings=1,
        total_overs=20,
    )
    session.add(match)

    deliveries = generate_20_overs_deliveries("match_test")
    for d in deliveries:
        session.add(Delivery(**d))

    for t in SAMPLE_TEAMS:
        session.add(FantasyTeam(id=t["id"], name=t["name"], user_name=t["user_name"]))

    session.commit()
    yield session
    session.close()


def test_seed_counts(test_db_session):
    player_count = test_db_session.query(Player).count()
    delivery_count = test_db_session.query(Delivery).count()
    team_count = test_db_session.query(FantasyTeam).count()

    assert player_count == 22
    assert delivery_count == 120
    assert team_count == 3


def test_over_deliveries_filter(test_db_session):
    # Deliveries up to over 5
    d_over_5 = (
        test_db_session.query(Delivery)
        .filter(Delivery.match_id == "match_test", Delivery.over_number <= 5)
        .all()
    )
    assert len(d_over_5) == 30  # 5 overs * 6 balls
