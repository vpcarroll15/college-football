"""
Rank college football teams according to elo ranking.
"""
import csv
import enum
from collections import defaultdict
from math import log

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm


# We use the first three years of our training set merely to generate initial elo rankings...we don't actually want
# to measure the loss from these years.
WARMUP_YEARS = set(range(2010, 2013))
# The next six years constitute our training set, against which we will try to minimize loss. (We reserve 2019 as our
# test set.)
TRAINING_YEARS = set(range(2013, 2019))


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
        return 1 / (1 + 10 ** ((rating2 - rating1) / 400))

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

        expected_outcome_winner = self.expected_outcome(
            initial_rating_winner, initial_rating_loser
        )
        return expected_outcome_winner

    def update_ratings_with_result(
        self, winner, loser, winning_team_location, k=40, include_in_log_loss=True
    ):
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

    def get_players_with_ratings_descending_order(self):
        """
        Returns a list of (player, rating) tuples in descending order.
        """
        rating_to_players = defaultdict(list)
        for player, rating in self.player_to_rating.items():
            rating_to_players[rating].append(player)

        players = []
        ratings = []
        for rating in reversed(sorted(rating_to_players.keys())):
            players.extend(rating_to_players[rating])
            while len(ratings) < len(players):
                ratings.append(rating)

        return list(zip(players, ratings))

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

    def __init__(
        self,
        k_min=10,
        k_max=150,
        k_step=5,
        home_field_min=0,
        home_field_max=200,
        home_field_step=20,
        season_regression_min=0.5,
        season_regression_max=1.1,
        season_regression_step=0.05,
    ):
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
            for home_field in range(
                self.home_field_min, self.home_field_max + 1, self.home_field_step
            ):
                season_regression = self.season_regression_min
                while season_regression < self.season_regression_max:
                    yield k, home_field, season_regression
                    season_regression += self.season_regression_step


class ParameterTester:
    """
    The class that carries out the search for optimal parameters, according to some strategy that is given to it.
    """

    PARAMETERS = ["k", "home_field", "season_regression"]

    def __init__(self, scores, parameter_generator_obj):
        self.scores = scores
        self.parameter_generator_obj = parameter_generator_obj

        # Tuples consisting of two elements: first, the log loss, and second, the tuple of parameters that attained
        # that log loss (k, home_field, season_regression).
        self.results = []
        self.best_elo = None
        self.min_loss = 1e9

    def run_one_cycle(self, k, home_field, season_regression):
        """Returns elo ratings for one set of parameters."""
        elo = EloMachine(home_team_advantage=home_field)
        last_year = None
        for (
            year,
            week,
            visiting_school,
            visiting_score,
            home_school,
            home_score,
        ) in self.scores:
            if year != last_year:
                elo.regress_to_mean(season_regression)
                last_year = year

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

            elo.update_ratings_with_result(
                winning_team,
                losing_team,
                winning_team_location,
                k=k,
                include_in_log_loss=year in TRAINING_YEARS,
            )
        return elo

    def optimize(self):
        """
        Runs a full optimization cycle.
        """
        # Prime the parameter generator and get our first set of parameters.
        parameter_generator = self.parameter_generator_obj.get_next_params()
        last_loss = None
        while True:
            try:
                k, home_field, season_regression = parameter_generator.send(last_loss)
            except StopIteration:
                break
            else:
                print(
                    "Trying parameters k={}, home_field={}, season_regression={}...".format(
                        k, home_field, season_regression
                    )
                )
                elo = self.run_one_cycle(k, home_field, season_regression)
                if elo.log_loss < self.min_loss:
                    self.best_elo = elo
                    self.min_loss = elo.log_loss
                last_loss = elo.log_loss
                print("Loss: {}".format(last_loss))

                self.results.append((last_loss, (k, home_field, season_regression)))
        self.results.sort()

    def plot_one_field(self, field, outfile=None):
        """
        Throws an AssertionError if we haven't generated results yet.
        """
        assert self.results

        field_index = self.PARAMETERS.index(field)
        grouped_results = defaultdict(list)
        for log_loss, params in self.results:
            grouped_results[params[field_index]].append(log_loss)
        grouped_results_flattened = [(k, min(v)) for k, v in grouped_results.items()]

        x_list = []
        y_list = []
        for x, y in sorted(grouped_results_flattened):
            x_list.append(x)
            y_list.append(y)

        plt.plot(x_list, y_list)
        plt.xlabel(field)
        plt.ylabel("log_loss")
        if outfile:
            plt.savefig(outfile)
        plt.show()

    def plot_two_fields(self, first_field, second_field, outfile=None):
        """
        Given two fields of the three that we searched over, generates a surface plot of the two parameters
        vs loss.

        Throws an AssertionError if we haven't generated results yet.
        """
        assert self.results

        first_field_index = self.PARAMETERS.index(first_field)
        second_field_index = self.PARAMETERS.index(second_field)

        grouped_results = defaultdict(list)
        for log_loss, params in self.results:
            grouped_results[
                (params[first_field_index], params[second_field_index])
            ].append(log_loss)
        grouped_results_flattened = {k: min(v) for k, v in grouped_results.items()}

        x_list = []
        y_list = []
        z_list = []
        for (x, y), z in grouped_results_flattened.items():
            x_list.append(x)
            y_list.append(y)
            z_list.append(z)

        fig = plt.figure()
        ax = Axes3D(fig)
        ax.plot_trisurf(x_list, y_list, z_list, cmap=cm.coolwarm, linewidth=0.1)
        ax.set_xlabel(first_field)
        ax.set_ylabel(second_field)
        ax.set_zlabel("log_loss")
        if outfile:
            plt.savefig(outfile)
        plt.show()


if __name__ == "__main__":
    scores = []
    with open("scores.csv", newline="") as csvfile:
        scores_reader = csv.reader(csvfile)
        for (
            year,
            week,
            visiting_school,
            visiting_score,
            home_school,
            home_score,
        ) in scores_reader:
            scores.append(
                (
                    int(year),
                    int(week),
                    visiting_school,
                    int(visiting_score),
                    home_school,
                    int(home_score),
                )
            )
    searcher = ParameterTester(scores, GridParameterGenerator())
    searcher.optimize()
    print(searcher.results[:10])
    top_25 = searcher.best_elo.get_players_with_ratings_descending_order()[:25]
    print("Introducing the top 25 of 2019...")
    for i, (player, rating) in enumerate(top_25):
        print("{}) {} ({})".format(i + 1, player, int(rating)))
    searcher.plot_one_field("k", outfile="k.png")
    searcher.plot_one_field("home_field", outfile="home_field.png")
    searcher.plot_one_field("season_regression", outfile="season_regression.png")
    searcher.plot_two_fields("k", "home_field", outfile="k_and_home_field.png")
    searcher.plot_two_fields(
        "k", "season_regression", outfile="k_and_season_regression.png"
    )
    searcher.plot_two_fields(
        "home_field",
        "season_regression",
        outfile="home_field_and_season_regression.png",
    )
