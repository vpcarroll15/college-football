"""
Rank college football teams according to elo ranking.
"""
import csv
import enum
from collections import defaultdict
from math import log
from copy import deepcopy

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm


# We use the first three years of our training set merely to generate initial elo rankings...we don't actually want
# to measure the loss from these years.
WARMUP_YEARS = set(range(2010, 2013))
# The next six years constitute our training set, against which we will try to minimize loss. (We reserve 2019 as our
# test set.)
TRAINING_YEARS = set(range(2013, 2019))

WEEKS_IN_SEASON = 18


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
        """
        for k in range(self.k_min, self.k_max + 1, self.k_step):
            for home_field in range(
                self.home_field_min, self.home_field_max + 1, self.home_field_step
            ):
                season_regression = self.season_regression_min
                while season_regression < self.season_regression_max:
                    print(
                        "Trying parameters k={}, home_field={}, season_regression={}...".format(
                            k, home_field, season_regression
                        )
                    )
                    loss = yield dict(
                        k=k, home_field=home_field, season_regression=season_regression
                    )
                    print("Loss: {}".format(loss))
                    season_regression += self.season_regression_step


class GradientParameterGenerator:
    """
    A ParameterSearch class that implements a simple form of gradient descent.
    """

    def __init__(
        self,
        k=100,
        home_field=50,
        season_regression=0.9,
        allow_different_k_different_weeks=False,
    ):
        self.allow_different_k_different_weeks = allow_different_k_different_weeks
        self.k_start = k

        self.home_field_start = home_field
        self.season_regression_start = season_regression

    def _alter_params_for_key(self, params, key, delta):
        """
        Given a dict of params, the key in the params that we want to tweak, and the delta by which we want to
        tweak it, yields all the tweaked params.
        """

        def alter_params_helper(keys_list, delta):
            """
            Returns a fresh set of params, tweaked by delta.
            """
            new_params = deepcopy(params)
            value = new_params
            for key in keys_list[:-1]:
                value = new_params[key]
            value[keys_list[-1]] += delta
            return new_params

        if key == "k_list":
            for i in range(len(params["k_list"])):
                # We deliberately don't try to optimize weeks 16 or 17 because we just don't have enough data from them.
                # (Army might play Navy in that week, and nothing else.)
                # (Subtract 1 because zero-indexed.)
                if i in [15, 16]:
                    continue
                yield alter_params_helper(["k_list", i], delta)
                yield alter_params_helper(["k_list", i], -delta)
        else:
            yield alter_params_helper([key], delta)
            yield alter_params_helper([key], -delta)

    def get_next_params(self):
        """
        A generator function for the next values of k, home_field_advantage, and season_regression that we
        should try.
        """
        params = dict(
            home_field=self.home_field_start,
            season_regression=self.season_regression_start,
        )
        if self.allow_different_k_different_weeks:
            params["k_list"] = [self.k_start] * WEEKS_IN_SEASON
        else:
            params["k"] = self.k_start

        delta = 3
        best_loss = yield params
        while delta > 0.1:
            competing_losses_and_params = []
            for key in params.keys():
                scaled_delta = delta * 0.01 if key == "season_regression" else delta
                for test_params in self._alter_params_for_key(
                    params, key, scaled_delta
                ):
                    param_loss = yield test_params
                    competing_losses_and_params.append((param_loss, test_params))
            new_best_loss, new_best_params = min(
                competing_losses_and_params, key=lambda x: x[0]
            )
            if new_best_loss < best_loss:
                best_loss = new_best_loss
                params = new_best_params
                print(
                    "Accepting new best params ({}) because it produced loss of {}".format(
                        params, best_loss
                    )
                )
            else:
                delta /= 3.0


class ParameterTester:
    """
    The class that carries out the search for optimal parameters, according to some strategy that is given to it.
    """

    def __init__(self, scores):
        self.scores = scores

        # Tuples consisting of two elements: first, the log loss, and second, the dict of parameters that attained
        # that log loss.
        self.results = []
        self.best_elo = None
        self.min_loss = 1e9

    def run_one_cycle(self, param_dict):
        """Returns elo ratings for one set of parameters."""
        elo = EloMachine(home_team_advantage=param_dict["home_field"])
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
                elo.regress_to_mean(param_dict["season_regression"])
                last_year = year

            # We don't actually know which games are neutral-site games, unfortunately. We just know
            # that bowl games are at neutral sites.
            if week == WEEKS_IN_SEASON:
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

            if "k_list" in param_dict:
                k = param_dict["k_list"][week - 1]
            else:
                k = param_dict["k"]

            elo.update_ratings_with_result(
                winning_team,
                losing_team,
                winning_team_location,
                k=k,
                include_in_log_loss=year in TRAINING_YEARS,
            )
        return elo

    def optimize(self, parameter_generator_obj):
        """
        Runs a full optimization cycle.
        """
        # Prime the parameter generator and get our first set of parameters.
        parameter_generator = parameter_generator_obj.get_next_params()
        last_loss = None
        while True:
            try:
                param_dict = parameter_generator.send(last_loss)
            except StopIteration:
                break
            else:
                elo = self.run_one_cycle(param_dict)
                if elo.log_loss < self.min_loss:
                    self.best_elo = elo
                    self.min_loss = elo.log_loss
                last_loss = elo.log_loss

                self.results.append((last_loss, param_dict))
        # Just ignore the dict element. We don't want it to be used as a tiebreaker because it isn't sortable.
        self.results.sort(key=lambda x: x[0])

    def plot_one_field(self, field, outfile=None):
        """
        Throws an AssertionError if we haven't generated results yet.
        """
        assert self.results

        grouped_results = defaultdict(list)
        for log_loss, params in self.results:
            grouped_results[params[field]].append(log_loss)
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

        grouped_results = defaultdict(list)
        for log_loss, params in self.results:
            grouped_results[(params[first_field], params[second_field])].append(
                log_loss
            )
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
    searcher = ParameterTester(scores)
    skip_grid_search = False
    if not skip_grid_search:
        searcher.optimize(GridParameterGenerator())
        best_loss, best_params = searcher.results[0]
        print(
            "Best params after initial grid search: {}".format(best_params, best_loss)
        )

    regenerate_plots = False
    if regenerate_plots:
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
    print("\n\nNow carrying out more refined search with gradient descent...")
    if skip_grid_search:
        gradient_parameters = GradientParameterGenerator()
    else:
        gradient_parameters = GradientParameterGenerator(**best_params)
    searcher.optimize(gradient_parameters)
    best_loss, best_params = searcher.results[0]
    print(
        "Best params after gradient refinement: {} (loss={})".format(
            best_params, best_loss
        )
    )
    print(
        "\n\nNow carrying out more refined search by allowing k to vary across weeks..."
    )
    searcher.optimize(
        GradientParameterGenerator(
            **best_params, allow_different_k_different_weeks=True
        )
    )
    best_loss, best_params = searcher.results[0]
    print(
        "Best params after allowing k to vary across weeks: {} (loss={})".format(
            best_params, best_loss
        )
    )
    top_25 = searcher.best_elo.get_players_with_ratings_descending_order()[:25]
    print("Introducing the top 25 of 2019...")
    for i, (player, rating) in enumerate(top_25):
        print("{}) {} ({})".format(i + 1, player, int(rating)))
