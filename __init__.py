from flask import Flask, render_template, session, request, redirect, url_for
from court import Court
import os
import config
import requests
import json

app = Flask(__name__)

YELP_ACCESS_TOKEN = "aqKeXPatJnHAFTXPoyuhkrIbgDvt5KfFrkwitxXGVGrtexzENT57Pk2EPmGoebTeQT7-iMC6Ul-Q568toAA4oe8LUNlL571AjfEHfNktKUKzhYD--mizotdiG4bdV3Yx"
EMPTY_RESPONSE = json.dumps('')

app = Flask(__name__)

def get_auth_dict(access_token):
    return {'Authorization' : "Bearer " + access_token}

def get_yelp_access_token():
    # WARNING: Ideally we would also expire the token. An expiry is sent with the token which we ignore.
    if YELP_ACCESS_TOKEN in session:
        print "access token found in session"
    else:
        print "access token needs to be retrieved"
        response = requests.post('https://api.yelp.com/oauth2/token', data=config.yelp_api_auth)
        if response.status_code == 200:
            session[YELP_ACCESS_TOKEN] = response.json()['access_token']
            print "stored access token in session:", session[YELP_ACCESS_TOKEN]
        else:
            raise RuntimeError("Unable to get token, received status code " + str(response.response))
    
    return session[YELP_ACCESS_TOKEN]

def getData(response):
    try:
        result = response.json()
        allcourts = result["businesses"]
        if not allcourts:
            raise ValueError("Search is invalid.") 
        courts = []
    except ValueError as e:
        print e
    for a in allcourts:
        name  = a["name"]
        image_url = a["image_url"]
        location = a["location"]
        coordinates = a["coordinates"]

        court = Court(name, image_url, location, coordinates)
        courts.append(court)
    return courts

@app.route("/search", methods=['POST', 'GET'])
def search():
    term = request.form['term']
    location = request.form['location']

    response = requests.get('https://api.yelp.com/v3/businesses/search',
    params=get_search_params(term, location),
    headers=get_auth_dict(get_yelp_access_token()))

    if response.status_code == 200:
        print "Got 200 for business search"
        courts = getData(response)
        return results(courts)
    else:
        print "Received non-200 response({}) for business search, returning empty response".format(response.status_code)
        return EMPTY_RESPONSE

def get_search_params(term, location):
    return {'term': term, 'location' : location}

@app.route("/results")
def results(courts):
    return render_template('results.html', courts=courts)

@app.route('/')
def homepage():
	return render_template('index.html')

port = os.getenv('PORT', '5000')
if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(host='0.0.0.0', port=int(port), debug=True)