import requests
from datetime import datetime
import pytz
import os
from flask import Flask, request, redirect, session, render_template, Response, make_response
import json
from ph_py import ProductHuntClient

app = Flask(__name__)

# establish current date in PT timezone
def getTime():
    tz = pytz.timezone(os.environ['TZ'])
    today = datetime.now(tz)
    today_utc = today.astimezone(pytz.UTC)
    return today_utc


def comments(x):
    if x > 1:
        return str(x) + " comments: "
    else:
        return str(x) + " comment: "


def getHN():
    APIbase = "https://hacker-news.firebaseio.com/v0/"
    APItop = APIbase+"topstories.json"
    topReq = requests.get(APItop)
    topStories = topReq.json()
    #print topStories
    hn = []

    for s in topStories[:5]:
        #print s
        APIstory = APIbase +"item/"+ str(s) +".json"
        r = requests.get(APIstory)
        d = r.json()
        story = {}

        story["uid"] = s
        story["updateDate"] = getTime().strftime('%Y-%m-%dT%H:%M:%S.0Z')
        story["titleText"] = "Top stories on HN: "+ d['title']
        story["mainText"] = "With "+ str(d['score']) +" points and "+ comments(len(d['kids'])) + d['title']
        story["redirectionUrl"] = d['url']

        hn.append(story)

    return hn


def getPH():
    phc = ProductHuntClient(os.environ['PHC'], os.environ['PHS'], "http://localhost:5000")
    # Example request
    ph = []
    for s in phc.get_todays_posts()[:5]:
        print s.id
        print s.name
        print s.tagline
        print s.votes_count
        print s.redirect_url

        story = {}
        story["uid"] = s.id
        story["updateDate"] = getTime().strftime('%Y-%m-%dT%H:%M:%S.0Z')
        story["titleText"] = "Top posts on PH: "+ s.name
        story["mainText"] = "With "+ str(s.votes_count) +" up votes: " + s.name + ", " + s.tagline
        story["redirectionUrl"] = s.redirect_url
        ph.append(story)

    return ph

## GENERATE FEEDS
@app.route('/hn', methods=['GET'])
def hn():
    feed = getHN()
    if feed:
        return json.dumps(feed)
    else:
        return make_response("Feed Error", 400)

## GENERATE FEEDS
@app.route('/ph', methods=['GET'])
def ph():
    feed = getPH()
    if feed:
        return json.dumps(feed)
    else:
        return make_response("Feed Error", 400)

if __name__ == "__main__":
	app.run(debug=os.environ['DEBUG'])
