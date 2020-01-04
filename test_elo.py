import pytest

from elo import *


def test_grid_parameter_search():
    searcher = GridParameterGenerator(
        k_min=1,
        k_max=2,
        k_step=1,
        home_field_min=0,
        home_field_max=1,
        home_field_step=1,
        season_regression_min=0,
        season_regression_max=0.06,
        season_regression_step=0.05,
    )
    grid_params = list(searcher.get_next_params())
    assert len(grid_params) == 8


def test_elo_machine_prediction():
    elo = EloMachine(home_team_advantage=200)

    assert pytest.approx(elo.expected_outcome(900, 900)) == 0.50
    assert pytest.approx(elo.expected_outcome(900, 1100), abs=1e-2) == 0.24
    assert pytest.approx(elo.expected_outcome(900, 1300), abs=1e-2) == 0.09

    elo.player_to_rating = {"Notre Dame": 900, "USC": 1100}
    assert pytest.approx(elo.predict_outcome("Notre Dame", "USC", WinningTeamLocation.HOME)) == 0.50
    assert pytest.approx(elo.predict_outcome("Notre Dame", "USC", WinningTeamLocation.NEUTRAL_SITE), abs=1e-2) == 0.24
    assert pytest.approx(elo.predict_outcome("Notre Dame", "USC", WinningTeamLocation.ROAD), abs=1e-2) == 0.09

