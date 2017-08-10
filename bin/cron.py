#!/usr/bin/env python
import requests
from datetime import datetime
import pytz
import os
from flask import Flask, request, redirect, session, render_template, Response, make_response, jsonify
import json
from ph_py import ProductHuntClient
import random
import feedparser
from lxml import html
import requests
import redis

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

        #print story["uid"]
        if 'url' in d:
            story["redirectionUrl"] = d['url']
        else:
            story["redirectionUrl"] = story["commentURL"]

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


def getWIB():
    url = "https://warisboring.com/feed/"
    rss = feedparser.parse(url)
    wib = []

    for s in rss['entries']:
        story = {}
        story['title'] = s['title']
        story['commentURL'] = s['link']
        story['thumbnail'] = "http://i.imgur.com/rUk5Tar.png"
        wib.append(story)

    return wib


def getND():
    page = requests.get('http://nextdraft.com/current')
    tree = html.fromstring(page.content)
    nd = []

    links = tree.xpath('//div[@class="blurb-content"]/p/a/@href')
    sentences = tree.xpath('//div[@class="blurb-content"]/p/a/text()')

    for l, s in zip(links, sentences):
        story = {}
        story['title'] = s
        story['commentURL'] = l
        story['thumbnail'] = "http://i.imgur.com/Pbcu4DI.png"
        nd.append(story)

    return nd


def getALL():
    feed = {}
    feed["stories"] = []
    feed["stories"].extend(getPH(20))
    feed["stories"].extend(getHN(20))
    feed["stories"].extend(getWIB())
    feed["stories"].extend(getND())

    #f = open("../feed.json", 'w')
    #f.write(str(json.dumps(feed)))
    #f.close()

    # CONNECT TO REDIS & MYSQL + define ORM
    redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL']) # Heroku Redis
    print redisdb.set("feed", str(json.dumps(feed)))

# generate feed
getALL()

#print "\n***\n"
#redisdb = #redis.StrictRedis.from_url(os.environ['REDIS_URL']) # Heroku Redis

#print "\n***\n"
#print redisdb.get("feed")

#print "\n***\n"
#print json.dumps(redisdb.get("feed"))
