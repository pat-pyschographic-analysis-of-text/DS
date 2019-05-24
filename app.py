import pandas_datareader.data as web
import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import tweepy
from ibm_watson import PersonalityInsightsV3
import json
import pandas as pd
import time

# Credentials for APIs and auth callers
TWITTER_AUTH = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY,TWITTER_CONSUMER_SECRET)
TWITTER_AUTH.set_access_token(TWITTER_ACCESS_TOKEN,TWITTER_ACCESS_TOKEN_SECRET)
TWITTER = tweepy.API(TWITTER_AUTH)

# Placeholder data
# df = pd.read_csv('austen_with_time.csv')

app = dash.Dash()

app.layout = html.Div(children=[
    # Hidden div that stores cached state, the intermediate value
    html.Div(id='intermediate-value', style={'display': 'none'}),

    html.Div(children='''
        Enter twitter handle:
    '''),
    dcc.Input(id='input', value='elonmusk', type='text'),

    html.Div(id='overall-graph'),
    html.Div(id='personality-graph'),
    html.Div(id='needs-graph'),
    html.Div(id='values-graph'),

])

# Get data, process it, and make it available to other callbacks
@app.callback(Output('intermediate-value', 'children'),
              [Input('input', 'value')]
)
def get_and_process_data(input):
     # WARNING: this is a very expensive step
     # API call and store data
     # Do not set the num_periods over 5, it will eat up the API
     num_periods = 5
     name = 'elonmusk'
     df_a = pd.DataFrame()
     for i in range(num_periods):
         try:
             twitter_user = TWITTER.user_timeline(screen_name=name,
                                              count=30,
                                              tweet_mode='extended',
                                              max_id=twitter_user.max_id)

             favorites = TWITTER.favorites(name,count=30,
                                           max_id=favorites.max_id)

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

             p = pd.DataFrame(profile['personality'],columns=['category','name','raw_score'])
             n = pd.DataFrame(profile['needs'], columns=['category','name','raw_score'])
             v = pd.DataFrame(profile['values'], columns=['category','name','raw_score'])
             df = pd.concat([p,n,v],axis=0)
             df['time'] = twitter_user[0].created_at
             df_a = df_a.append(df)

         except:
             twitter_user = TWITTER.user_timeline(screen_name=name,count=30,tweet_mode='extended')
             favorites = TWITTER.favorites(screen_name=name,count=30)
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

             p = pd.DataFrame(profile['personality'],columns=['category','name','raw_score'])
             n = pd.DataFrame(profile['needs'], columns=['category','name','raw_score'])
             v = pd.DataFrame(profile['values'], columns=['category','name','raw_score'])
             df = pd.concat([p,n,v],axis=0)
             df['time'] = twitter_user[0].created_at
             df_a = df_a.append(df)


     # Return proper data as json for other callbacks
     return df_a.to_json(date_format='iso', orient='split')



# All categories graph
@app.callback(
    Output(component_id='overall-graph', component_property='children'),
    [Input(component_id='intermediate-value', component_property='children')]
)
def overall_graph(jsonified_cleaned_data):
    # Fetch the data from cache, transform it and return a graph to be rendered
    df_a = pd.read_json(jsonified_cleaned_data, orient='split')
    # df_a = pd.read_csv('austen_with_time.csv')
    df = df_a.groupby(['time','category']).mean().unstack()
    df.columns = df.columns.droplevel()
    return html.Div(
        dcc.Graph(
            id='overall_graph',
            figure={
                'data': [{
                     'x': df.index,
                     'y': df[col] ,
                     'type': 'line',
                     'name': col
                } for col in df.columns],
                'layout': {
                    'title': 'Overall graph'
                }
            }
        )
    )

# Personality graph
@app.callback(
    Output(component_id='personality-graph', component_property='children'),
    [Input(component_id='intermediate-value', component_property='children')]
)
def personality_graph(jsonified_cleaned_data):
    # Fetch the data from cache, transform it and return a graph to be rendered
    # df_a = pd.read_json(jsonified_cleaned_data, orient='split')
    df_p = df_a[df_a['category'] == 'personality']
    df_p = df_p.groupby(['time','name']).mean().unstack()
    df_p.columns = df_p.columns.droplevel()
    return html.Div(
        dcc.Graph(
            id='personality-graph',
            figure={
                'data': [{
                     'x': df_p.index,
                     'y': df_p[col] ,
                     'type': 'line',
                     'name': col
                } for col in df_p.columns],
                'layout': {
                    'title': 'Personality'
                }
            }
        )
    )

# Needs graph
@app.callback(
    Output(component_id='needs-graph', component_property='children'),
    [Input(component_id='intermediate-value', component_property='children')]
)
def needs_graph(jsonified_cleaned_data):
    # Fetch the data from cache, transform it and return a graph to be rendered
    df_a = pd.read_json(jsonified_cleaned_data, orient='split')
    df_p = df_a[df_a['category'] == 'needs']
    df_p = df_p.groupby(['time','name']).mean().unstack()
    df_p.columns = df_p.columns.droplevel()
    return html.Div(
        dcc.Graph(
            id='needs-graph',
            figure={
                'data': [{
                     'x': df_p.index,
                     'y': df_p[col] ,
                     'type': 'line',
                     'name': col
                } for col in df_p.columns],
                'layout': {
                    'title': 'Needs'
                }
            }
        )
    )
#
# Values graph
@app.callback(
    Output(component_id='values-graph', component_property='children'),
    [Input(component_id='intermediate-value', component_property='children')]
)
def values_graph(jsonified_cleaned_data):
    # Fetch the data from cache, transform it and return a graph to be rendered
    df_a = pd.read_json(jsonified_cleaned_data, orient='split')
    df_p = df_a[df_a['category'] == 'values']
    df_p = df_p.groupby(['time','name']).mean().unstack()
    df_p.columns = df_p.columns.droplevel()
    return html.Div(
        dcc.Graph(
            id='values-graph',
            figure={
                'data': [{
                     'x': df_p.index,
                     'y': df_p[col] ,
                     'type': 'line',
                     'name': col
                } for col in df_p.columns],
                'layout': {
                    'title': 'Values'
                }
            }
        )
    )



if __name__ == '__main__':
    app.run_server(debug=True)
