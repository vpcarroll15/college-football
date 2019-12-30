"""
Rank college football teams according to elo ranking.
"""
import csv


class EloMachine:
	"""
	A class that abstracts away all the stuff specific to the Elo algorithm.
	"""
	def __init__(self, initial_rating=1000):
		self.initial_rating = initial_rating
		self.player_to_rating = {}

	@staticmethod
	def expected_outcome(rating1, rating2):
		"""
		Given two elo ratings, returns the probability that the player with
		rating1 defeats the player with rating2.
		"""
		return 1 / (1 + 10**((rating2 - rating1) / 400))

	def update_with_result(self, winner, loser, k=20):
		"""
		Updates our ratings with a result. The value of k may be overridden.
		"""
		# TODO: update this signature to handle home team advantage.
		initial_rating_winner = self.player_to_rating.get(winner, self.initial_rating)
		initial_rating_loser = self.player_to_rating.get(loser, self.initial_rating)

		expected_outcome_winner = self.expected_outcome(initial_rating_winner, initial_rating_loser)
		delta = k * (1 - expected_outcome_winner)

		self.player_to_rating[winner] = initial_rating_winner + delta
		self.player_to_rating[loser] = initial_rating_loser - delta

	def get_players_by_descending_rating(self):
		"""
		Returns our list of players as tuples in descending rank:

		[(player1, rating1), (player2, rating2)...]
		"""
		# TODO: make this handle the case of conflicting ratings?
		rating_to_player = {v: k for k, v in self.player_to_rating.items()}

		players = []
		for rating in reversed(sorted(rating_to_player.keys())):
			players.append(rating_to_player[rating])
		return players

	def regress_to_mean(self, z):
		"""
		For each rating, either contracts it toward the initial rating (if z < 1) or
		widens it away from the initial rating (if z > 1). z = 1 has no effect.
		"""
		player_to_new_rating = {}
		for player, rating in self.player_to_rating.items():
			new_rating = self.initial_rating + (rating - self.initial_rating) * z
			player_to_new_rating[player] = new_rating
		self.player_to_rating = player_to_new_rating


class GridParameterSearch:
	"""
	A ParameterSearch class that implements the grid search strategy.
	"""
	def __init__(self, k_min=10, k_max=80, k_step=5,
		         home_field_min=0, home_field_max=300, home_field_step=50,
				 season_regression_min=0.25, season_regression_max=1.3, season_regression_step=0.2):
		self.k_min = k_min
		self.k_max = k_max
		self.k_step = k_step
		self.home_field_min = home_field_min
		self.home_field_max = home_field_max
		self.home_field_step = home_field_step
		self.season_regression_min = season_regression_min
		self.season_regression_max = season_regression_max
		self.season_regression_step = season_regression_step

	def get_next_params(self):
		"""
		A generator function for the next values of k, home_field_advantage, and season_regression that we
		should try.

		Ignores input to the generator function.
		"""
		for k in range(self.k_min, self.k_max + 1, self.k_step):
			for home_field in range(self.home_field_min, self.home_field_max + 1, self.home_field_step):
				season_regression = self.season_regression_min
				while season_regression < self.season_regression_max:
					yield k, home_field, season_regression
					season_regression += self.season_regression_step


if __name__ == "__main__":
	elo = EloMachine()
	with open('scores.csv', newline='') as csvfile:
		scores_reader = csv.reader(csvfile)
		last_year = 0
		for year, week, visiting_school, visiting_score, home_school, home_score in scores_reader:
			if visiting_score > home_score:
				elo.update_with_result(visiting_school, home_school)
			else:
				elo.update_with_result(home_school, visiting_school)
			last_year = year
	print(elo.get_players_by_descending_rating()[:25])
