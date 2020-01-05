# The question

What are the best teams in college football at the end of the 2019-2020 season?

To answer this question, most people turn to the
[College Football Playoff selection committee](https://collegefootballplayoff.com/sports/2017/10/16/selection-committee.aspx). "The committee," as
it's cryptically known, determines which teams get to play for the national championship and which teams have to
duke it out in the [Beef O' Brady's bowl](https://en.wikipedia.org/wiki/2011_Beef_%27O%27_Brady%27s_Bowl) (yes
this is real). We are told that the committee's integrity is unimpeachable, and that it
carefully considers the resume of each team before making its decision.

But why take the committee's word for it? This is the twenty-first century, and we have computers and statistics.
Nothing is more objective than a computer making a list. Let's see which teams the computer thinks are the best, and
whether there are any surprises.

# The method

## The Elo system

In order to measure the strength of each team, I decided to use the [Elo system](
https://en.wikipedia.org/wiki/Elo_rating_system). The Elo system is *not* the most powerful method for estimating the
strength of different competitors. Indeed, it's actually a bit old and crusty. Proposed in 1939 by a Hungarian-American
physics professor who wanted more accurate ratings for chess players, the calculations required
by the algorithm are simple. It is clear that it was designed by someone who lived in a world without
powerful computers.

Elo's biggest weakness is that it throws a lot of information away. In particular, it only looks at the outcomes of
games. It doesn't care about margin of victory, which most college football fans agree is a good predictor of how
good a team is. It also doesn't care if an important player was injured during the week at practice, or if the team
just had a bye week. If I were training a model to help me make lots of money betting on the outcomes of college
football games, I would want to incorporate all this information.

That having been said, I like Elo for several reasons:

1) It's popular. To this day, it is used in the chess world, and lots of people know what it is.
2) Because it is used in the chess world, I have an intuition for what the ratings mean, which I like.
3) You, too, can develop an intuition for what Elo ratings mean! If Player A has a rating that is 200 points higher than
player B, then Player A has a ~75% chance of winning. If Player A has a rating that is 400 points higher
than player B, then Player A has a ~90% chance of winning. See? Now you have Elo intuition, too.
4) It's easy to program, which is important, because I am going to be programming it.

Also, I love the fact that, with Elo, it's simple to determine the probability that one team will defeat another.
As we will see, this will be the basis for optimizing our algorithm.

## The optimization problem

So, how can we create Elo rankings for college football teams?

First, we need to understand that we are solving an optimization problem. Almost any ranking system is governed by
parameters, the correct values for which depend on the activity that is being ranked. We need to set our
parameters correctly if we want our rankings to be meaningful.

### k

The most important parameter in the Elo system is a variable called *k*. *k* measures how drastically we should
update someone's ranking after they win or lose a game. I can make this clear with an example. Let's imagine that two
teams, the Finches and the Groundhogs, play a football game. Initially, both teams have a rating of 1000. It's a close
game, but the Finches pull it out at the last minute with a clutch touchdown pass. How much should we update each
team's ranking? Are the Finches now rated 1001, and the Groundhogs rated 999? Or are the Finches now rated
1100, and the Groundhogs rated 900?

Without knowing more about the sport that is being played, there is no objectively correct answer to this question.
Let's imagine for a moment that the Finches and the Groundhogs are baseball teams, and that this is the 162nd game of
the season. Each team's Elo rating is calculated based on the previous 161 games. In this case, the fact that the
Finches beat the Groundhogs doesn't give us much new information, and we shouldn't dramatically reconsider our opinion
of either team. We should nudge the Finches' rating up a few points, and take a few points away from the Groundhogs,
but that's all. This is what it means to use a small value of *k*.

On the other hand, let's imagine that this is the first game of the football season, and that both teams are kind of a
mystery. In this case, the fact that the Finches beat the Groundhogs does give us a lot of information, and we should
make a bigger update to each of their ratings.

Chess players tend to play a lot of games, and their strength changes gradually over time. For this reason, the chess
ranking system has a low value of *k*: *k*=20 for most players, and *k*=10 for elite players. Significantly,
*k*=40 is used for players under the age of eighteen. This is because young players are often
improving rapidly, and their ratings need to be able to update quickly to reflect this.

Do we expect our college football rankings system to have a high or low value of *k*? (It doesn't actually matter what
we think, because the optimization algorithm is indifferent to our thoughts, but it's good to build intuition anyway.)
Anyone who has watched college football knows the following:

1) Teams often get much better or much worse as the season progresses.
2) The season has at most fifteen games, and most teams only play twelve or thirteen games.
3) Teams sometimes become much stronger or much weaker in the offseason.

For all of these reasons, we should expect to have a high value of *k*. We will see if that actually comes to pass.

What other parameters will we need to optimize? Two come to mind immediately...

### Home field advantage

The Elo rating, since it was designed for chess, makes no accommodation for home field advantage, but it's
difficult to imagine how our algorithm could have predictive power without it. Home field advantage makes a difference
in college football. Teams often have much better home records than road records.

In order to wedge this into the Elo system, we will create a new variable called *home_field*. Returning to our
previous example, let's imagine that the Finches played the Groundhogs at home. Previously, we said that both teams had
a rating of 1000. But now, to account for the fact
that the Finches are playing at home, let's increase their expected strength by *home_field* points. If
*home_field*=200, then we pretend as though the Finches are rated 1200. The Groundhogs retain their old rating of 1000.
We then predict that the Finches have a ~75% chance of winning.

Of course, there is no way to know *a priori* what *home_field* should be. We are going to have to solve for it.

### Regression to the mean between seasons

One final, important distinction between college football and chess is that every year in college football, the team
becomes substantially different in the offseason.
(Yes, I am aware that there are more differences between chess and football, but I can't think of any that
are relevant to our statistical model!) Some years, a team gets a lot better; other times, it gets a
lot worse. In general, though, we should expect some regression to the mean. (We have all been waiting for Alabama
to regress to the mean for a long time...)

To be frank, I think that I could probably leave this variable out of the model. Yes, college football teams become
stronger or weaker in the offseason, but dynasties also last for a long time. The best predictor for who will
be good next season is to look at who is good this season.

Nevertheless, I don't want to make any judgment calls about what should or shouldn't be in the model. Our optimization
algorithm can decide which variables are useful and which are not. So I will give it a variable to play with:
*season_regression*.

It works like this: if a team's strength is 1500 at the end of the season, and the average
strength of a team in the league is 1000, then I adjust the team's strength as follows before starting the next season:

1000 + (1500-1000) * *season_regression*

If a team is weaker than average at the end of the season, then I adjust it toward the mean, too. Let's consider a team
with a ranking of 700.

1000 + (700-1000) * *season_regression*

Again, it's not clear what this variable should be set to. Something less than one, presumably...but how much less
than one?

Note that, if the optimization algorithm decides that this variable is useless, it can set it to 1.0 to make it
irrelevant. Similarly, if the algorithm decides that home field advantage means nothing, then it can set that to 0.

### Our objective function

I have left out the most important element in our optimization problem. What variable are we trying to maximize or
minimize?

Qualitatively, we are trying to minimize the error of our model's predictions. If the model says that Team A has a 99%
chance of beating Team B, and Team B wins, that is bad. We want that to happen as rarely as possible. At the same time,
we obviously don't want our model to just always say that Team A has a 50% chance of beating Team B. That kind of model
is useless.

We can make this goal quantitative in the following way. Let's train our model over several seasons of college
football results. Our Elo system will assign a probability to each result, and our objective will be to choose our
values of *k*, *home_field*, and *season_regression* to maximize the product of those probabilities. In statistics,
this is called [maximum likelihood estimation](https://en.wikipedia.org/wiki/Maximum_likelihood_estimation). If we
choose good values for *k*, *home_field*, and *season_regression*, then our model shouldn't be "surprised" by the
results of too many games.

I like maximum likelihood estimation because it rewards our model for being confident. If the model says that the
Finches have a 90% chance of beating the Groundhogs, and the Finches win, that's great! But we prefer a model that
assigns a 95% chance of beating the Groundhogs, or a 99% chance, and gets it right.
By default, the Elo system doesn't assign meaningful probabilities to the outcomes of matches. By training it in this
way, we force the probabilities to be meaningful. And this will be useful when we want to use our trained model
to answer questions like, "How likely is it that Notre Dame will beat USC this weekend?"

### Actually solving the problem

So how do we choose *k*, *home_field*, and *season_regression* in order to maximize the likelihood of the data?

Well, there are different strategies for doing this. 

