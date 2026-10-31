import pytest
from httpx import ASGITransport, AsyncClient

from app.db.seed import seed_database
from app.main import app


@pytest.fixture(scope="module", autouse=True)
def setup_seed_db():
    seed_database()


@pytest.mark.asyncio
async def test_api_list_matches():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/matches")
        assert response.status_code == 200
        matches = response.json()
        assert len(matches) >= 1
        assert matches[0]["id"] == "match_001"


@pytest.mark.asyncio
async def test_api_match_state():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/matches/match_001/state?over=10&team_id=team_001")
        assert response.status_code == 200
        data = response.json()
        assert data["match_id"] == "match_001"
        assert data["over"] == 10
        assert data["runs"] > 0
        assert data["team_points"] is not None
        assert len(data["recent_balls"]) <= 6


@pytest.mark.asyncio
async def test_api_list_and_get_team():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res_list = await ac.get("/api/v1/teams")
        assert res_list.status_code == 200
        teams = res_list.json()
        assert len(teams) >= 1

        res_team = await ac.get("/api/v1/teams/team_001?over=10")
        assert res_team.status_code == 200
        team = res_team.json()
        assert team["id"] == "team_001"
        assert len(team["players"]) == 11
        assert team["captain_name"] == "Rohit Sharma"


@pytest.mark.asyncio
async def test_api_chat_explain():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "match_id": "match_001",
            "team_id": "team_001",
            "over": 10,
            "message": "Why did my points change in the last over?",
            "language": "en",
        }
        res = await ac.post("/api/v1/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "Points" in data["answer"] or "points" in data["answer"].lower()
        assert data["evidence"] is not None
        assert data["evidence"]["tool_called"] == "explain_points_change"
        assert len(data["evidence"]["table_rows"]) == 11


@pytest.mark.asyncio
async def test_api_chat_advisor():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "match_id": "match_001",
            "team_id": "team_001",
            "over": 10,
            "message": "Should I change my captain?",
            "language": "en",
        }
        res = await ac.post("/api/v1/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "Captain" in data["answer"] or "captain" in data["answer"].lower()
        assert data["evidence"] is not None
        assert data["evidence"]["tool_called"] == "suggest_changes"
        assert len(data["evidence"]["table_rows"]) == 11


@pytest.mark.asyncio
async def test_api_chat_dls_what_if():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "match_id": "match_001",
            "team_id": "team_001",
            "over": 10,
            "message": "What if rain cuts it to 15 overs?",
            "language": "en",
        }
        res = await ac.post("/api/v1/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "15" in data["answer"]
        assert data["evidence"] is not None
        assert data["evidence"]["tool_called"] == "simulate_reduced_overs"


@pytest.mark.asyncio
async def test_api_chat_hinglish():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "match_id": "match_001",
            "team_id": "team_001",
            "over": 10,
            "message": "Fix my captain",
            "language": "hinglish",
        }
        res = await ac.post("/api/v1/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert any(w in data["answer"] for w in ["Aapka", "Aapko", "captain", "karein", "dekhne"])


@pytest.mark.asyncio
async def test_api_chat_out_of_scope():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "match_id": "match_001",
            "team_id": "team_001",
            "over": 10,
            "message": "What is the capital of Australia?",
            "language": "en",
        }
        res = await ac.post("/api/v1/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["is_out_of_scope"] is True
        assert "only help with this" in data["answer"].lower()
        assert data["evidence"] is None
