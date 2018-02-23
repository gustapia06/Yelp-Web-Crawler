from app import app
from flask import render_template
from flask import request as rq
from bs4 import BeautifulSoup
import requests
import json
from fuzzywuzzy import fuzz, process
import re
import os


# Yelp API urls and constants
API_HOST = 'https://api.yelp.com'
WEBSITE_HOST = 'https://www.yelp.com/biz/'
SEARCH_PATH = '/v3/businesses/search'
TOKEN_PATH = '/oauth2/token'
GRANT_TYPE = 'client_credentials'
USER_AGENT = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
TOKEN = os.getenv('TOKEN')
PATTERN = re.compile('[^a-zA-Z0-9 ]+')
LOCATION = 'New York, NY'
RADIUS = int(round(5*1.6*1000))
CATEGORY = 'pizza'
SEARCH_LIMIT = 10


#function to scrape reviews from Yelp's website
def get_reviews(bizID, n_revs):
    # scrape the business Yelp url
    url = '{0}{1}'.format(WEBSITE_HOST, bizID)
    url_params = {
        'start': 0,
        'sort_by': 'date_desc'
    }
    headers = {
        'user-agent': USER_AGENT
    }

    response = requests.get(url,headers=headers, params=url_params)
    soup = BeautifulSoup(response.text, 'html.parser')

    # from the html content, get the reviews
    #for Yelp, they happen to be on a js script and formatted as json (very nice guys!!)
    reviewsRaw = soup.find_all('script',type='application/ld+json')

    #but if they are not in the js script, then they changed their
    #webpage structure so tool would need to be rewritten to adapt to that change
    if len(reviewsRaw) != 1:
        raise('Error scraping Yelp\'s webpage')

    #tranform to dict and get all needed data
    reviewsDict = json.loads(reviewsRaw[0].string)
    result = {
        'name': reviewsDict['name'],
        'address': '%s, %s, %s %s' %(reviewsDict['address']['streetAddress'],
                                reviewsDict['address']['addressLocality'],
                                reviewsDict['address']['addressRegion'],
                                reviewsDict['address']['postalCode']),
        'rating': reviewsDict['aggregateRating']['ratingValue'],
        'reviews': reviewsDict['aggregateRating']['reviewCount'],
        'disp_reviews': n_revs,
        'url': url
    }

    #check if available reviews are at least the number set by the user
    n_revs = min(n_revs, len(reviewsDict['review']))

    #get review data
    reviews = [{
               'date': reviewsDict['review'][i]['datePublished'],
               'rating': reviewsDict['review'][i]['reviewRating']['ratingValue'],
               'description': reviewsDict['review'][i]['description']
               } for i in range(n_revs)]

    return result, reviews


# main page where user inputs query
@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

# search page that dynamically changes depending on results
@app.route('/search', methods=['GET','POST'])
def search():
    # two types of methods for the page:
    
    # if POST, then we are coming from the main page after submitting the search form
    if rq.method == 'POST':
        # get the form
        search_term = rq.form["searchBox"]
        n_revs = int(rq.form["numRevs"])
        
        #search for the search term within Yelp's API
        search_term_regex = PATTERN.sub('',search_term.lower())
        url = '{0}{1}'.format(API_HOST, SEARCH_PATH)
        url_params = {
            'term': search_term_regex,
            'location': LOCATION,
            'limit': SEARCH_LIMIT,
            'categories': CATEGORY,
            'radius': RADIUS
        }
        headers = {
            'user-agent': USER_AGENT,
            'Authorization': 'Bearer %s' % TOKEN
        }
        response = requests.get(url,headers=headers, params=url_params)

        #if search doesnt return results, tell the user
        if response.json()['total'] < 1:
            return render_template("search.html", search_term = search_term)

        #else get results strings that are most similar to query
        search_results = [PATTERN.sub('',biz['name'].lower()) for biz in response.json()['businesses']]
        n_results = len(search_results)
        search_scores = process.extract(search_term, search_results, limit=4, scorer=fuzz.token_set_ratio)

        #different cases for similarities in results:
        #if highest scored result is 90% or more similar:
        if search_scores[0][1] > 90:
            #if there are more than 1 result that are 90% or more similar, then
            #present the first results but also suggest others
            if n_results > 1 and search_scores[1][1] > 90:
                idx = search_results.index(search_scores[0][0])
                idxSet = [search_results.index(res[0]) for res in search_scores[1:] if res[1]>90]
            else:
                #else only present the highest scored result
                idx = search_results.index(search_scores[0][0])
                idxSet = []
        #if highest scored results is between 75-90% similar:
        elif search_scores[0][1] > 75:
            #if only one high score or other scores are less than 50% similar, then
            #only present the highest scored result
            if n_results == 1 or (n_results > 1 and search_scores[1][1] < 50):
                idx = search_results.index(search_scores[0][0])
                idxSet = []
            else:
                #else present the highest, and also suggest the others above 50%
                idx = search_results.index(search_scores[0][0])
                idxSet = [search_results.index(res[0]) for res in search_scores[1:] if res[1]>50]
        else:
            #if no result over 75%, then do not present reviews but only present
            #suggestions that are similar at least 50% to query
            idx = None
            idxSet = [search_results.index(res[0]) for res in search_scores if res[1]>50]

        #parse reviews and show suggestions depending on search results and similarities
        if idx is not None:
            bizID = response.json()['businesses'][idx]['id']
            result, reviews = get_reviews(bizID, n_revs)
        else:
            result = {}
            reviews = []

        #get the suggestions
        if idxSet:
            suggestions = [{
                           'name': response.json()['businesses'][i]['name'],
                           'link': '/search?id=%s&n=%d' % (response.json()['businesses'][i]['id'], n_revs)
                           } for i in idxSet]
        else:
            suggestions = []

        #prepare the dynamic html page
        return render_template("search.html", result = result, reviews = reviews, search_term = search_term, suggestions = suggestions)

    elif rq.method == 'GET':
        # if method is GET, then we are coming from a suggestion, so we are passing
        # options within the url
        # number of reviews come from original query, and no suggestions are shown (obviously!!)
        bizID = rq.args.get('id')
        n_revs = rq.args.get('n', 1, type=int)
        result, reviews = get_reviews(bizID, n_revs)
        return render_template("search.html", result = result, reviews = reviews)
