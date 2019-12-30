from elo import *

def test_grid_parameter_search():
	searcher = GridParameterSearch(k_min=1, k_max=2, k_step=1,
								   home_field_min=0, home_field_max=1, home_field_step=1,
				 				   season_regression_min=0, season_regression_max=0.06, season_regression_step=0.05)
	grid_params = list(searcher.get_next_params())
	grid_params.sort()
	assert grid_params == [(1, 0, 0.0), (1, 0, 0.05), (1, 1, 0.0), (1, 1, 0.05),
	                       (2, 0, 0.0), (2, 0, 0.05), (2, 1, 0.0), (2, 1, 0.05)]

