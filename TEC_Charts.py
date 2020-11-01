import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
server = app.server

#---------- Extract data from Aragon Tokens xdai Subgraph ----------

sample_transport=RequestsHTTPTransport(
    url='https://api.thegraph.com/subgraphs/name/1hive/aragon-tokens-xdai',
    verify=True,
    retries=3,
)
client = Client(
    transport=sample_transport
)
query = gql('''
query {
    tokenHolders(first: 1000 where : { tokenAddress: "0x8FbeD5491438B81b2fCDBFd4A53e7eD8d5B4f1be"}) {
    address
    balance
  }
}
''')
response1 = client.execute(query)


#---------- Extract data from Conviction Voting xdai Subgraph ----------

sample_transport=RequestsHTTPTransport(
    url='https://api.thegraph.com/subgraphs/name/1hive/aragon-conviction-voting-xdai',
    verify=True,
    retries=3,
)
client = Client(
    transport=sample_transport
)
query = gql('''
query {
    proposals(first: 500 where: {orgAddress: "0x070e93753657a6bfd7055bf99e762bfb065a1037", status: "Active"}) {
  	name
    totalTokensStaked
  }
}
''')
response2 = client.execute(query)

#---------- Get total used tokens in proposals  -------
df4 = pd.DataFrame(response2['proposals'])
df4['totalTokensStaked'] = df4['totalTokensStaked'].astype(float)
df4['totalTokensStaked'] = df4['totalTokensStaked']/1000000000000000000
usedTokens = df4['totalTokensStaked'].sum(axis = 0, skipna = True)

#---------- Create Token Holders dataframe  ----------

df3 = pd.DataFrame(response1['tokenHolders'])
df3['balance'] = df3['balance'].astype(float)
df3['balance'] = df3['balance']/1000000000000000000
df3.sort_values(by=['balance'], inplace=True, ascending=False)
#print('Total number of holders: ',df3['balance'].count())
#print('Mean value: ', df3['balance'].mean())
totalTokens = df3['balance'].sum(axis = 0, skipna = True)


#---------- Generate Token Holders Pie Chart -------------

df3.loc[df3['balance'] < 5, 'address'] = 'Other' # Represent only large holders

labels = df3['address'].tolist()
values = df3['balance'].tolist()

fig3 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
fig3.update_traces(hoverinfo='label+value', textinfo='percent', textfont_size=10,
                  marker=dict(line=dict(color='#000000', width=1)))
fig3.update_layout(autosize=True)

#---------- Generate Impact Hours Bar Charts -------------

df1 = pd.read_csv('TEC_Total_Impact_Hours.csv')
df2 = pd.read_csv('TEC#3_IH.csv')

fig1 = px.bar(df1, x="Telegram Handle", y="Impact Hours")
fig2 = px.bar(df2, x="Telegram Handle", y="Impact Hours")

#----------  Generate Conviction Voting Gauge chart ----------
fig4 = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = usedTokens,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "Committed Tokens", 'font': {'size': 18}},
    #delta = {'reference': 400, 'increasing': {'color': "RebeccaPurple"}},
    gauge = {
        'axis': {'range': [None, totalTokens], 'tickwidth': 1, 'tickcolor': "darkblue"},
        'bar': {'color': "darkblue"},
        'bgcolor': "white",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, totalTokens], 'color': 'cyan'}],
        #'threshold': {
        #    'line': {'color': "red", 'width': 4},
        #    'thickness': 0.75,
        #    'value': totalTokens
        }))

fig4.update_layout(paper_bgcolor = "lavender", font = {'color': "darkblue", 'family': "Arial"})

#------------- Tap Styles  -----------
tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}

#----------  App Layout  ---------
app.layout = html.Div([
    dcc.Tabs(id="tabs-styled-with-inline", value='tab-1', children=[
        dcc.Tab(label='Impact Hours', value='tab-1', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Token Holders', value='tab-2', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Convitcion Voting', value='tab-3', style=tab_style, selected_style=tab_selected_style),
    ], style=tabs_styles),
    html.Div(id='tabs-content-inline')
])

@app.callback(Output('tabs-content-inline', 'children'),
              [Input('tabs-styled-with-inline', 'value')])
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            html.H3(' Cumulated Impact Hours'),
            html.Label('As of October 23rd, 2020'),

            dcc.Graph(
                id='Bar-graph1',
                figure=fig1
            ),

            html.H3(' Last Period Impact Hours'),
            html.Label('As of October 23rd, 2020'),

            dcc.Graph(
                id='Bar-graph2',
                figure=fig2
            ),
        ])
    elif tab == 'tab-2':
        return html.Div([
            html.H3('Token Holders'),
            html.Label('Extracted from xDai Chain'),
            dcc.Graph(
                id='Pie-graph1',
                figure=fig3
            ),
        ])
    elif tab == 'tab-3':
        return html.Div([
            html.H3('TEC Conviction Voting'),
            html.Label('Total issued tokens: '+str(totalTokens)),
            dcc.Graph(
                id='Gauge-graph1',
                figure=fig4
            ),
        ])

if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port='8050', debug=True)

