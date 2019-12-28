"""
Downloads all the raw data that we need in order to create our prediction engine.
"""
import subprocess


YEARS_OF_INTEREST = list(range(2010, 2019))
WEEKS_IN_SEASON = list(range(1, 16))
ROOT_URL = "https://www.footballdb.com/college-football/scores.html?lg=FBS&type=reg"

target_urls = []
target_filenames = []
for year in YEARS_OF_INTEREST:
	for week in WEEKS_IN_SEASON:
		target_urls.append(ROOT_URL + "&yr={}&wk={}".format(year, week))
		target_filenames.append('raw_data/year-{}-week-{}.html'.format(year, week))

for url, filename in zip(target_urls, target_filenames):
	print("Downloading {} to {}...".format(url, filename))
	# Ideally I would be able to use the "requests" library for this, but for some reason this website is giving
	# me "permission denied" when I use requests. Whatever.
	subprocess.check_call("wget -O {} \"{}\"".format(filename, url), shell=True)
