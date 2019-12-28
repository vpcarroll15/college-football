"""
In this file, we parse all the stuff that we retrieved from the college football
database into a consistent csv format.
"""
import os
import csv

from bs4 import BeautifulSoup


def extract_score_tuples(contents):
	"""
	Given an HTML file of raw college football data, returns a list of 4-tuples consisting
	of the visiting team's name, the home team's name, the visiting team's score, and the
	home team's score.
	"""
	parsed_html = BeautifulSoup(contents, features="html.parser")
	games = parsed_html.body.find_all('table', attrs={'class': 'fb_component_tbl'})

	def get_team_and_score_from_table_row(row):
		"""Returns the name of the team and the score, given an HTML row."""
		final_score_elem = row('td')[-1]
		team_elem = row('td')[0]

		final_score = int(final_score_elem.text)
		# This will look like: 'UTSA (1-1)' or '(4) Oklahoma (2-0)'
		team_with_record = team_elem.text
		team_pieces = [piece for piece in team_with_record.split() if '(' not in piece]
		team_no_record = ' '.join(team_pieces)
		return team_no_record, final_score

	score_tuples = []
	for game in games:
		try:
			visitor_row = game.find('tr', attrs={'class': 'row-visitor'})
			visiting_team, visiting_score = get_team_and_score_from_table_row(visitor_row)
			home_row = game.find('tr', attrs={'class': 'row-home'})
			home_team, home_score = get_team_and_score_from_table_row(home_row)
			score_tuples.append((visiting_team, visiting_score, home_team, home_score))
		except ValueError:
			print("Failed to parse result from game--likely cancelled. "
				  "Please verify by looking at the html object: {}".format(game))

	return score_tuples


files_of_interest = os.listdir('raw_data/')
all_score_tuples = []
for i, file in enumerate(files_of_interest):
	# We expect files to be formatted as:
	# year-2018-week-11.html
	_, year, _, week = os.path.splitext(file)[0].split('-')
	year = int(year)
	week = int(week)
	print("Processing week {} of {}...".format(i, len(files_of_interest)))

	with open(os.path.join('raw_data/', file)) as file_handle:
		file_text = file_handle.read()
	score_tuples = extract_score_tuples(file_text)
	for score_tuple in score_tuples:
		# We want to store the year and the week in addition to the score.
		all_score_tuples.append((year, week, score_tuple[0], score_tuple[1], score_tuple[2], score_tuple[3]))

with open('scores.csv', 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    for entry in sorted(all_score_tuples):
    	csv_writer.writerow(entry)
