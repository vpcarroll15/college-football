# The question

Which are the best teams in college football?

To answer this question, most people turn to the
[College Football Playoff selection committee](https://collegefootballplayoff.com/sports/2017/10/16/selection-committee.aspx).
(There is also something called the AP poll, but nobody really cares about that.) "The committee," as
it's cryptically known, determines which teams get to play for the national championship and which teams have to
duke it out in the [Beef O' Brady's bowl](https://en.wikipedia.org/wiki/2011_Beef_%27O%27_Brady%27s_Bowl). 
We are told that the committee's integrity is unimpeachable, and that it
carefully considers the resume of each team before making its decision.

But why rely on the committee? This is the twenty-first century, and we have computers and statistics.
Nothing is more objective than a computer making a list. Let's see which teams the computer thinks are the best, and
whether there are any surprises.

# The method

## The Elo system

In order to measure the strength of each team, I decided to use the [Elo system](
https://en.wikipedia.org/wiki/Elo_rating_system). The Elo system is *not* the most powerful method for estimating the
strength of competitors. Indeed, it's a bit old and crusty. Proposed in 1939 by a Hungarian-American
physics professor who wanted to devise more accurate ratings for chess players, the calculations required
by the algorithm are simple. It's clear that it was designed by someone who lived in a world without
powerful computers.

Elo's biggest weakness is that it throws a lot of information away. In particular, it only looks at the outcomes of
games. It doesn't care about margin of victory, which most college football fans agree is a good predictor of
a team's quality. It also doesn't care if an important player was injured during the week at practice, or if the team
is coming off a bye week. If I were training a model to help me make lots of money betting on the outcomes of college
football games, I would want to incorporate all this information.

That having been said, I like Elo for several reasons:

1) It's popular. To this day, it is used in chess competitions, and lots of people know what it is.
2) Because it is used in the chess world, I have an intuition for what the ratings mean, which I like.
3) You, too, can develop an intuition for what Elo ratings mean! If Player A has a rating that is 200 points higher than
player B, then Player A has a ~75% chance of winning. If Player A's rating is 400 points higher,
then Player A has a ~90% chance of winning. Now you have Elo intuition, too.
4) It's easy to program, which is important, because I am going to be programming it.

Also, I love the fact that, with Elo, it's simple to estimate the probability that one team will defeat another.
This will be the basis for optimizing our model.

## The optimization problem

So, how can we create Elo rankings for college football teams?

Almost any ranking system is governed by parameters, the correct values for which depend on the activity
that is being ranked. We need to set our parameters carefully if we want our rankings to be meaningful.

### k

The most important parameter in the Elo system is called *k*. *k* measures to what extent we should
update someone's ranking after a win or loss.

Let's imagine that two
teams, the Finches and the Groundhogs, play a game. Initially, both teams have a rating of 1000. It's a close
match, but the Finches pull it out at the last minute. How much should we update each
team's ranking? Are the Finches now rated 1001, and the Groundhogs 999? Or are the Finches now rated
1100, and the Groundhogs 900? Without knowing more about the sport that is being played,
there is no objectively correct answer to this question.

If the Finches and the Groundhogs are baseball teams, and this is the 162nd game of
the season, then we should only make a small update. Each team's Elo rating is based on the previous
161 games. The fact that the Finches beat the Groundhogs doesn't give us much new information, and we shouldn't
dramatically revise our opinion
of either team. We nudge the Finches' rating up a few points, and we take a few points away from the Groundhogs,
but that's all.

This is what it means to use a small value of *k*.

On the other hand, if this is the first game of the football season, then the fact that the Finches beat the Groundhogs
might give us a lot of information. In this case, we should make a bigger update to each of their ratings.

Chess players play a lot of games, and their strength changes gradually over time. For this reason, the chess
ranking system has a low value of *k*: *k*=20 for most players, and *k*=10 for elite players. Significantly,
*k*=40 is used for players under the age of eighteen. This is because young players improve rapidly,
and their ratings need to be able to update quickly to reflect this.

Do we expect our college football ranking system to have a high or low value of *k*? (It doesn't actually matter what
we think, because the optimization algorithm is indifferent to our thoughts, but it's good to build intuition anyway.)
Anyone who has watched college football knows the following:

1) Teams often get much better or much worse as the season progresses.
2) The season has at most fifteen games, and the majority of teams only play twelve or thirteen games.
3) Teams can become much stronger or much weaker in the offseason.

For all of these reasons, we should expect to have a high value of *k*. We will see if that actually comes to pass.

### Home field advantage

The Elo rating, since it was designed for chess, makes no accommodation for home field advantage, but it's
difficult to imagine how our algorithm could have meaningful predictive power without it.
Home field makes a difference in college football. Teams often have much better home records than road records.

To wedge this into the Elo system, we will create a new parameter called *home_field*. Returning to our
previous example, let's imagine that the Finches played the Groundhogs at home. Previously, we said that both teams had
a rating of 1000. But now, to account for the fact
that the Finches are playing at home, we increase their expected strength by *home_field* points. If
*home_field*=200, then we pretend as though the Finches are rated 1200. The Groundhogs retain their old rating of 1000.
We then predict that the Finches have a ~75% chance of winning.

### Regression to the mean between seasons

One final, important distinction between college football and chess is that every year in college football, the team
becomes substantially different in the offseason. Some years, a team gets a lot better; other times, it gets a
lot worse. In general, though, we should expect some [regression to the mean](https://en.wikipedia.org/wiki/Regression_toward_the_mean).
(We have all been waiting for Alabama to regress to the mean for a long time...)

To be frank, I think that I could leave this variable out of the model. Yes, college football teams become
stronger or weaker in the offseason, but dynasties also last for a long time because of college football's 
recruiting imbalances. The best predictor for who will be good next season is to look at who is good this season.

Nevertheless, I don't want to make any judgment calls about what should or shouldn't be in the model. Our optimization
algorithm can decide which variables are useful and which are not. So I will give it a parameter to play with:
*season_regression*.

It works like this: if a team's strength is 1500 at the end of the season, and the average
strength of a team in the league is 1000, then I adjust the team's strength as follows in the offseason:

1000 + (1500-1000) * *season_regression*

If a team is weaker than average at the end of the season, then I adjust it toward the mean, too. Let's consider a team
with a ranking of 700.

1000 + (700-1000) * *season_regression*

If the optimization algorithm decides that this variable is useless, it can set it to 1.0 to make it
irrelevant.

### Our objective function

I have left out the most important element in our optimization problem. What variable are we trying to maximize or
minimize?

Qualitatively, we are trying to minimize the error of our model's predictions. If the model says that Team A has a 99%
chance of beating Team B, and Team B wins, that is bad. We want that to happen as rarely as possible.

We can make this goal quantitative in the following way. Let's train our model over several seasons of college
football results. We will feed each result into our model, and ask it to assign a probability to the result. The best
model will be the one that maximizes the product of those probabilities. In statistics,
this is called [maximum likelihood estimation](https://en.wikipedia.org/wiki/Maximum_likelihood_estimation).

I like maximum likelihood estimation because it rewards our model for being confident. If the model says that the
Finches have a 90% chance of beating the Groundhogs, and the Finches win, that's great! But we prefer a model that
assigns a 95% chance of beating the Groundhogs, or a 99% chance, and gets it right.

Here is how maximum likelihood estimation will work for our use case.
I have access to [ten years of college football results](scores.csv), from 2010 to 2019. I will
begin by giving every team an Elo ranking of 1000, and I will choose my values of *k*, *home_field*, and
*season_regression*. Then I will start feeding scores into my model. I will ask it to predict the outcome of the
contest between the Chipmunks and the Orioles, and the model will give me a probability. It then updates the Elo
ratings of both teams according to the result. The product of all those probabilities is the quality
of the model.

If we are choosing between two models, or two sets of parameters, then we choose the one that is
"surprised" less often. To put it another way, a good model matches the data.

Because every team starts with a rating of 1000, our model will be terrible at predicting the outcome of games in the
early years, and will take a while to "right" itself. For this reason, I ignore the probabilities that it assigns
to games between 2010 and 2012.

I also ignore the probabilities that it assigns to games in 2019, for a more subtle reason. I am hoping to measure the
quality of my model by looking at how effectively it predicts the outcomes of games in this past season. If I train
my model using the data from this season, then I am giving it an unfair advantage. I will be "fitting" my model's
parameters to the data that I want to use to determine if the model is good. For more on this, see [the difference
between training, validation, and test sets.](https://en.wikipedia.org/wiki/Training,_validation,_and_test_sets) The
data from 2019 is my test set.

### Actually solving the problem

So how do we optimize the values of *k*, *home_field*, and *season_regression*?

Well, there are different strategies for doing this. 

