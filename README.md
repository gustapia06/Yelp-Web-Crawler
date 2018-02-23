README
Dia&Co Coding Exercise by Gustavo Tapia

- Instructions to run in a local machine
What you need:
 - python3
 - pip (or pip3, depending on your system)
 - Flask (pip install Flask)
 - BeautifulSoup (pip install beautifulsoup4)
 - requests (pip install requests)
 - fuzzywuzzy (pip install fuzzywuzzy[speedup])

Once you install all packages, in the command line navigate to the src/ directory of the tool, and execute the following command:
	src $<your_python3_executable> run.py
which should start the Flask server.
At this point, you should be able to go to any web browser and access http://localhost:5000 to start the tool.

- Instructions on how to use the tool
The main page on http://localhost:5000 will show you a textbox where you can input the restaurant name that you want to query, and a drop-down list for you to select the number of recent reviews to be shown.

Once you click on the submit button, the website will search for the query string within Yelp and the following cases might happen:
a. If the query was exactly matched with a restaurant, then the reviews will show.
b. If the query was matched with a restaurant, but there are other restaurants that the query also matched with, then the reviews for the 'best-match' restaurant will show, and additionally, some suggestions for the other restaurants will show as a link.
c. If the query did not match with any restaurant, but there are some restaurant names that might be slightly similar to, then suggestions of these restaurant will show as a link.
d. If the query did not match no restaurant names, then the website will inform the user that the search failed.

Note: If the user clicks into a suggestion, the website will present the reviews for that suggested restaurant, and the number of reviews to show are assumed to be the same as the original query.

If the user want to start over with a new search, there is a link for them to go to the main page.