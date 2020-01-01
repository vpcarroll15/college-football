"""
Rank college football teams according to elo ranking.
"""
import csv
import enum
from collections import defaultdict
from math import log


class WinningTeamLocation(enum.Enum):
	HOME = 1
	ROAD = 2
	NEUTRAL_SITE = 3



class EloMachine:
	"""
	A class that abstracts away all the stuff specific to the Elo algorithm.
	"""
	def __init__(self, initial_rating=1000, home_team_advantage=200):
		self.initial_rating = initial_rating
		self.home_team_advantage = home_team_advantage
		# Map each player to his rating under our Elo scheme.
		self.player_to_rating = {}
		# Accumulate the log loss, which we will attempt to minimize.
		self.log_loss = 0

	@staticmethod
	def expected_outcome(rating1, rating2):
		"""
		Given two elo ratings, returns the probability that the player with
		rating1 defeats the player with rating2.
		"""
		return 1 / (1 + 10**((rating2 - rating1) / 400))

	def predict_outcome(self, team1, team2, team1_location):
		"""
		Given two teams and the location of the first team, returns the probability that team1 wins.

		No side effects.
		"""
		initial_rating_winner = self.player_to_rating.get(team1, self.initial_rating)
		initial_rating_loser = self.player_to_rating.get(team2, self.initial_rating)

		# Adjust the ratings according to where the game was played. If the game was played at a neutral site,
		# no adjustment is necessary.
		if team1_location == WinningTeamLocation.HOME:
			initial_rating_winner += self.home_team_advantage
		elif team1_location == WinningTeamLocation.ROAD:
			initial_rating_winner -= self.home_team_advantage

		expected_outcome_winner = self.expected_outcome(initial_rating_winner, initial_rating_loser)
		return expected_outcome_winner

	def update_ratings_with_result(self, winner, loser, winning_team_location, k=40, include_in_log_loss=True):
		"""
		Updates our ratings with a result. The value of k may be overridden.
		"""
		predicted_outcome = self.predict_outcome(winner, loser, winning_team_location)

		if include_in_log_loss:
			self.log_loss -= log(predicted_outcome)

		delta = k * (1 - predicted_outcome)
		initial_rating_winner = self.player_to_rating.get(winner, self.initial_rating)
		initial_rating_loser = self.player_to_rating.get(loser, self.initial_rating)
		self.player_to_rating[winner] = initial_rating_winner + delta
		self.player_to_rating[loser] = initial_rating_loser - delta

	def get_players_by_descending_rating(self):
		"""
		Returns our list of players in descending quality.
		"""
		rating_to_players = defaultdict(list)
		for player, rating in self.player_to_rating.items():
			rating_to_players[rating].append(player)

		players = []
		for rating in reversed(sorted(rating_to_players.keys())):
			players.extend(rating_to_players[rating])
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


class GridParameterGenerator:
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


class ParameterTester:
	"""
	The class that carries out the search for optimal parameters, according to some strategy that is given to it.
	"""
	def __init__(self, scores, parameter_generator_obj):
		self.scores = scores
		self.parameter_generator = parameter_generator_obj.get_next_params()

	def optimize(self):
		"""
		Runs a full optimization cycle, consuming its parameter generator.
		"""
		# Prime the parameter generator and get our first set of parameters.
		k, home_field, season_regression = self.parameter_generator.send(None)
		while True:
			pass


		pass







if __name__ == "__main__":
	scores = []
	with open('scores.csv', newline='') as csvfile:
		scores_reader = csv.reader(csvfile)
		for year, week, visiting_school, visiting_score, home_school, home_score in scores_reader:
			scores.append((int(year), int(week), visiting_school, int(visiting_score), home_school, int(home_score)))
	searcher = ParameterSearcher(scores, GridParameterGenerator())

	elo = EloMachine()
	with open('scores.csv', newline='') as csvfile:
		scores_reader = csv.reader(csvfile)
		for year, week, visiting_school, visiting_score, home_school, home_score in scores_reader:
			year = int(year)
			week = int(week)
			visiting_score = int(visiting_score)
			home_score = int(home_score)

			# We don't actually know which games are neutral-site games, unfortunately. We just know
			# that bowl games are at neutral sites.
			if week == 16:
				winning_team_location = WinningTeamLocation.NEUTRAL_SITE
			else:
				if home_score > visiting_score:
					winning_team_location = WinningTeamLocation.HOME
				else:
					winning_team_location = WinningTeamLocation.ROAD
			if home_score > visiting_score:
				winning_team, losing_team = home_school, visiting_school
			else:
				winning_team, losing_team = visiting_school, home_school

			elo.update_ratings_with_result(winning_team, losing_team, winning_team_location,
										   include_in_log_loss=(year in range(2013, 2019)))

	print(elo.get_players_by_descending_rating()[:25])
	print(elo.log_loss)
