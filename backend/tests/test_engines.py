import pytest

from app.db.seed import PLAYERS_DATA, SAMPLE_TEAMS, generate_20_overs_deliveries
from app.services.dls_estimator import (
    get_resource_percentage,
    simulate_reduced_overs,
)
from app.services.projection_engine import (
    project_player_rest_of_match,
    rank_and_advise_captain,
)
from app.services.scoring_engine import (
    calculate_player_points,
    calculate_team_points,
    load_scoring_rules,
)


@pytest.fixture
def scoring_rules():
    return load_scoring_rules()


@pytest.fixture
def all_deliveries():
    return generate_20_overs_deliveries("match_001")


@pytest.fixture
def sample_team_players():
    # Team 1 players
    t1_info = SAMPLE_TEAMS[0]
    players_map = {p["id"]: p for p in PLAYERS_DATA}
    result = []
    for p_id in t1_info["players"]:
        p_base = players_map[p_id].copy()
        p_base["is_captain"] = (p_id == t1_info["captain"])
        p_base["is_vice_captain"] = (p_id == t1_info["vice_captain"])
        p_base["is_playing_xi"] = True
        result.append(p_base)
    return result


# =========================================================================
# Scoring Engine Unit Tests
# =========================================================================

def test_scoring_known_single_boundary_four(scoring_rules):
    deliveries = [
        {"over_number": 1, "ball_in_over": 1, "batter_id": "p1", "bowler_id": "b1", "runs_batter": 4, "extra_type": None}
    ]
    # Starting XI: 4, 4 runs: 4, boundary four: 1 -> total = 9.0
    res = calculate_player_points(
        player_id="p1", player_name="Player 1", role="BAT", team="Team A",
        deliveries=deliveries, rules=scoring_rules
    )
    assert res.runs == 4
    assert res.fours == 1
    assert res.starting_xi_points == 4.0
    assert res.batting_points == 5.0
    assert res.total_points == 9.0


def test_scoring_known_six_and_captain_multiplier(scoring_rules):
    deliveries = [
        {"over_number": 1, "ball_in_over": 1, "batter_id": "p1", "bowler_id": "b1", "runs_batter": 6, "extra_type": None}
    ]
    # Starting XI: 4, 6 runs: 6, boundary six: 2 -> base = 12.0
    # Captain multiplier = 2.0x -> total = 24.0
    res = calculate_player_points(
        player_id="p1", player_name="Player 1", role="BAT", team="Team A",
        deliveries=deliveries, is_captain=True, rules=scoring_rules
    )
    assert res.base_points == 12.0
    assert res.multiplier == 2.0
    assert res.total_points == 24.0


def test_scoring_bowled_wicket_bonus(scoring_rules):
    deliveries = [
        {
            "over_number": 1, "ball_in_over": 1, "batter_id": "p1", "bowler_id": "b1",
            "runs_batter": 0, "extra_type": None, "is_wicket": True,
            "dismissal_kind": "bowled", "dismissed_player_id": "p1"
        }
    ]
    # Bowler: Starting XI: 4, Wicket: 25, Bowled bonus: 8 -> base = 37.0
    res = calculate_player_points(
        player_id="b1", player_name="Bowler 1", role="BOWL", team="Team B",
        deliveries=deliveries, rules=scoring_rules
    )
    assert res.wickets == 1
    assert res.bowled_or_lbw_count == 1
    assert res.bowling_points == 25.0
    assert res.bonus_points == 8.0
    assert res.total_points == 37.0


def test_scoring_duck_penalty(scoring_rules):
    deliveries = [
        {
            "over_number": 1, "ball_in_over": 1, "batter_id": "p1", "bowler_id": "b1",
            "runs_batter": 0, "extra_type": None, "is_wicket": True,
            "dismissal_kind": "caught", "dismissed_player_id": "p1"
        }
    ]
    # Batter: Starting XI: 4, Runs: 0, Duck penalty: -2 -> base = 2.0
    res = calculate_player_points(
        player_id="p1", player_name="Player 1", role="BAT", team="Team A",
        deliveries=deliveries, rules=scoring_rules
    )
    assert res.is_dismissed is True
    assert res.penalty_points == -2.0
    assert res.total_points == 2.0


def test_scoring_edge_case_over_0(sample_team_players, all_deliveries, scoring_rules):
    # At over 0, no match balls have been bowled
    team_breakdown = calculate_team_points(
        team_id="team_001", team_name="Challengers XI",
        team_players=sample_team_players,
        deliveries=all_deliveries,
        over_number=0,
        rules=scoring_rules,
    )
    # 11 players in Starting XI (4 pts each), Captain gets 2.0x (8 pts), Vice-Captain gets 1.5x (6 pts)
    # 9 normal players * 4 = 36 + 8 (C) + 6 (VC) = 50.0 pts
    assert team_breakdown.over_number == 0
    assert len(team_breakdown.players) == 11
    assert team_breakdown.total_points == 50.0


def test_scoring_edge_case_empty_team(all_deliveries, scoring_rules):
    team_breakdown = calculate_team_points(
        team_id="empty", team_name="Empty XI",
        team_players=[],
        deliveries=all_deliveries,
        over_number=5,
        rules=scoring_rules,
    )
    assert team_breakdown.total_points == 0.0
    assert len(team_breakdown.players) == 0


def test_scoring_edge_case_player_did_not_play(scoring_rules):
    res = calculate_player_points(
        player_id="bench_1", player_name="Bench Player", role="BAT", team="Team A",
        deliveries=[], is_playing_xi=False, rules=scoring_rules
    )
    assert res.starting_xi_points == 0.0
    assert res.base_points == 0.0
    assert res.total_points == 0.0


# =========================================================================
# Projection Engine Unit Tests
# =========================================================================

def test_projection_ranges_and_ordering(sample_team_players, all_deliveries, scoring_rules):
    for p in sample_team_players:
        proj = project_player_rest_of_match(
            player=p, deliveries=all_deliveries, current_over=10, total_overs=20, rules=scoring_rules
        )
        assert proj.remaining_low <= proj.remaining_expected <= proj.remaining_high
        assert proj.projected_total_low <= proj.projected_total_expected <= proj.projected_total_high


def test_projection_dismissed_batter_risk_flag(all_deliveries, scoring_rules):
    # Rohit is dismissed in over 8
    rohit = {"id": "p_rohit", "name": "Rohit Sharma", "role": "BAT", "team": "Mumbai Titans", "is_captain": True}
    proj_over_10 = project_player_rest_of_match(
        player=rohit, deliveries=all_deliveries, current_over=10, total_overs=20, rules=scoring_rules
    )
    assert proj_over_10.is_out is True
    assert "Batter already dismissed" in proj_over_10.risk_tags
    assert "Dismissed" in proj_over_10.reasoning


def test_projection_advisor_suggests_captain_switch(sample_team_players, all_deliveries, scoring_rules):
    # At over 10, Rohit (current captain) is out
    advice = rank_and_advise_captain(
        team_players=sample_team_players, deliveries=all_deliveries, current_over=10, total_overs=20, rules=scoring_rules
    )
    assert advice.current_captain_name == "Rohit Sharma"
    assert advice.should_change_captain is True
    assert len(advice.suggestions) >= 1
    assert "Rohit Sharma" in advice.suggestions[0]


def test_projection_edge_case_over_20(sample_team_players, all_deliveries, scoring_rules):
    # At over 20, match is finished
    for p in sample_team_players:
        proj = project_player_rest_of_match(
            player=p, deliveries=all_deliveries, current_over=20, total_overs=20, rules=scoring_rules
        )
        assert proj.remaining_low == 0.0
        assert proj.remaining_expected == 0.0
        assert proj.remaining_high == 0.0


# =========================================================================
# DLS Estimator Unit Tests
# =========================================================================

def test_dls_resource_table():
    assert get_resource_percentage(20, 0) == 100.0
    assert get_resource_percentage(15, 0) == 82.5
    assert get_resource_percentage(0, 0) == 0.0
    # Interpolation test
    r_11 = get_resource_percentage(11, 2)
    assert 55.8 <= r_11 <= 63.2


def test_dls_reduced_overs_simulation(sample_team_players, all_deliveries, scoring_rules):
    sim = simulate_reduced_overs(
        team_players=sample_team_players,
        deliveries=all_deliveries,
        current_over=10,
        reduced_overs=15,
        original_overs=20,
        rules=scoring_rules,
    )
    assert sim.original_overs == 20
    assert sim.reduced_overs == 15
    assert sim.current_over == 10
    assert sim.overs_lost == 5
    assert sim.projected_innings1_total_low <= sim.projected_innings1_total_expected <= sim.projected_innings1_total_high
    assert sim.approximate_revised_target > 0
    assert "Approximate DLS-style Revised Target" in sim.model_name
    assert len(sim.player_projections) == len(sample_team_players)
    for p_proj in sim.player_projections:
        assert p_proj.projected_low <= p_proj.projected_expected <= p_proj.projected_high
