from elo import *

def test_grid_parameter_search():
	searcher = GridParameterSearch(k_min=1, k_max=2, k_step=1,
								   home_field_min=0, home_field_max=1, home_field_step=1,
				 				   season_regression_min=0, season_regression_max=0.06, season_regression_step=0.05)
	grid_params = list(searcher.get_next_params())
	grid_params.sort()
	assert grid_params == [(1, 0, 0.0), (1, 0, 0.05), (1, 1, 0.0), (1, 1, 0.05),
	                       (2, 0, 0.0), (2, 0, 0.05), (2, 1, 0.0), (2, 1, 0.05)]


def test_elo_machine_prediction():
	elo = EloMachine(home_team_advantage=200)

	assert abs(elo.expected_outcome(900, 900) - 0.50) < 0.01
	assert abs(elo.expected_outcome(900, 1100) - 0.24) < 0.01
	assert abs(elo.expected_outcome(900, 1300) - 0.09) < 0.01

	elo.player_to_rating = {"Notre Dame": 900, "USC": 1100}
	assert (elo.predict_outcome("Notre Dame", "USC", WinningTeamLocation.HOME) - 0.50) < 0.01
	assert (elo.predict_outcome("Notre Dame", "USC", WinningTeamLocation.NEUTRAL_SITE) - 0.24) < 0.01
	assert (elo.predict_outcome("Notre Dame", "USC", WinningTeamLocation.ROAD) - 0.09) < 0.01

