from flask import Flask
import tweepy
from ibm_watson import PersonalityInsightsV3
import json
import time

app = Flask(__name__)

# Twitter and PI credentials go here

TWITTER_AUTH = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY,TWITTER_CONSUMER_SECRET)
TWITTER_AUTH.set_access_token(TWITTER_ACCESS_TOKEN,TWITTER_ACCESS_TOKEN_SECRET)
TWITTER = tweepy.API(TWITTER_AUTH)


twitter_user = TWITTER.user_timeline(screen_name='austen',
                                     count=100,
                                     tweet_mode='extended')

favorites = TWITTER.favorites('austen',count=100)

def convert_status_to_pi_content_item(t,f):
            return {
                'content': t.full_text + f.text,
                'contenttype': 'text/plain',
                'created': int(time.mktime(t.created_at.timetuple())),
                'id': str(t.id),
                'language': t.lang
            }

pi_content_items_array = list(map(convert_status_to_pi_content_item, twitter_user,
                                  favorites))

pi_content_items = {'contentItems': pi_content_items_array}

data = json.dumps(pi_content_items, indent=2)

personality_insights = PersonalityInsightsV3(
    version='2017-10-13',
    url=pi_url,
    iam_apikey= pi_password)

profile = personality_insights.profile(
          data,
          accept='application/json',
          content_type='application/json',
          consumption_preferences=True,
          raw_scores=True).get_result()

profile = json.dumps(profile, indent=2)

@app.route('/')
def hello_world():
    return profile
