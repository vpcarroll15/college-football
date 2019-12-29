import csv


def expected_outcome(rating1, rating2):
	"""
	Given two elo ratings, returns the fractional chance that the player with
	rating1 defeats the player with rating2.
	"""
	return 1 / (1 + 10**((rating2 - rating1) / 400))


def get_correct_value_k(year, week):
	"""
	Given the current week/year, returns the appropriate value of k for our model.
	"""
	# TODO: implement me.
	return 40


class EloMachine:
	def __init__(self, initial_rating=1000):
		self.initial_rating = initial_rating
		self.player_to_rating = {}

	def update_with_result(self, winner, loser, k=20):
		"""
		Updates our ratings with a result. The value of k may be overridden.
		"""
		# TODO: update this signature to handle home team advantage.
		initial_rating_winner = self.player_to_rating.get(winner, self.initial_rating)
		initial_rating_loser = self.player_to_rating.get(loser, self.initial_rating)

		expected_outcome_winner = expected_outcome(initial_rating_winner, initial_rating_loser)
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

	def change_spread(self, z):
		"""
		For each rating, either contracts it toward the initial rating (if z < 1) or
		widens it away from the initial rating (if z > 1). z = 1 has no effect.
		"""
		player_to_new_rating = {}
		for player, rating in self.player_to_rating.items():
			new_rating = self.initial_rating + (rating - self.initial_rating) * z
			player_to_new_rating[player] = new_rating
		self.player_to_rating = player_to_new_rating


elo = EloMachine()
with open('scores.csv', newline='') as csvfile:
	scores_reader = csv.reader(csvfile)
	last_year = 0
	for year, week, visiting_school, visiting_score, home_school, home_score in scores_reader:
		# TODO: find a way to get this to work!
		# if year != last_year:
		#	 elo.change_spread(0.5)
		if visiting_score > home_score:
			elo.update_with_result(visiting_school, home_school)
		else:
			elo.update_with_result(home_school, visiting_school)
		last_year = year
print(elo.get_players_by_descending_rating()[:25])
