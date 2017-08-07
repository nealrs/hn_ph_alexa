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
    if x == 1:
        return str(x) + " comment: "
    else:
        return str(x) + " comments: "


def getHN(num=5):
    APIbase = "https://hacker-news.firebaseio.com/v0/"
    APItop = APIbase+"topstories.json"
    topReq = requests.get(APItop)
    topStories = topReq.json()
    #print topStories
    hn = []

    for s in topStories[:int(num)]:
        #print s
        APIstory = APIbase +"item/"+ str(s) +".json"
        r = requests.get(APIstory)
        d = r.json()
        story = {}
        #print d

        story["uid"] = s
        story["updateDate"] = getTime().strftime('%Y-%m-%dT%H:%M:%S.0Z')
        story["titleText"] = "From HN: "+ d['title'].encode('utf-8')
        story["commentURL"] = "https://news.ycombinator.com/item?id="+ str(s)
        story["title"] = d['title'].encode('utf-8')
        story["thumbnail"]="http://i.imgur.com/iNheuJ7.png"

        if 'descendants' in d:
            story["mainText"] = "With "+ str(d['score']) +" points and "+ comments(d['descendants']) + d['title'].encode('utf-8')
        else:
            story["mainText"] = "With "+ str(d['score']) +" points: "+ d['title'].encode('utf-8')

        story["redirectionUrl"] = d['url']

        hn.append(story)

    return hn


def getPH(num=5):
    phc = ProductHuntClient(os.environ['PHC'], os.environ['PHS'], "http://localhost:5000")
    # Example request
    ph = []
    for s in phc.get_todays_posts()[:int(num)]:
        story = {}
        story["uid"] = s.id
        story["updateDate"] = getTime().strftime('%Y-%m-%dT%H:%M:%S.0Z')
        story["titleText"] = "From PH: "+ (s.name).encode('utf-8') + ", " + (s.tagline).encode('utf-8')

        story["title"] = (s.name).encode('utf-8') + ", " + (s.tagline).encode('utf-8')
        story["commentURL"] =s.discussion_url.encode('utf-8')
        story["thumbnail"]="http://i.imgur.com/BOUdyc2.jpg"

        if s.comments_count:
            story["mainText"] = "With "+ str(s.votes_count) +" up votes and "+ comments(s.comments_count) + (s.name).encode('utf-8') + ", " + (s.tagline).encode('utf-8')
        else:
            story["mainText"] = "With "+ str(s.votes_count) +" up votes: " + (s.name).encode('utf-8') + ", " + (s.tagline).encode('utf-8')

        story["redirectionUrl"] = s.redirect_url
        ph.append(story)

    return ph

## GENERATE HN FEED
@app.route('/hn', methods=['GET'])
def hn():
    feed = getHN()
    if feed:
        return json.dumps(feed)
    else:
        return make_response("Feed Error", 400)

## GENERATE PH FEED
@app.route('/ph', methods=['GET'])
def ph():
    feed = getPH()
    if feed:
        return json.dumps(feed)
    else:
        return make_response("Feed Error", 400)

## GENERATE combined/big FEED
@app.route('/all', methods=['GET'])
def all():
    feed = []
    feed.extend(getPH(20))
    feed.extend(getHN(20))
    if feed:
        return json.dumps(feed)
    else:
        return make_response("Feed Error", 400)


if __name__ == "__main__":
	app.run(debug=os.environ['DEBUG'])
