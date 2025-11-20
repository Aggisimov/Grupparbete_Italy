from dash import Dash, html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import hashlib

#____________________ VAR & CONST ____________________

data = "athlete_events.csv"
SPORTS = ["Cycling","Equestrianism","Fencing", "Swimming"]
SPORT_OPTIONS = {
    "Cycling":[
        {"label":"Ålder", "value":"age"},
        {"label":"Medaljer", "value": "medals"},
    ],
    "Fencing":[
        {"label":"Ålder", "value":"age"},
        {"label":"Medaljer", "value": "medals"},
    ],
    "Equestrianism":[
        {"label":"Ålder", "value":"age"},
        {"label":"Medaljer", "value": "medals"},
    ],
    "Swimming":[
        {"label":"Ålder", "value":"age"},
        {"label":"Medaljer", "value": "medals"},
    ]
}

#____________________ DATA ______________________
df = pd.read_csv(data)

df = df.fillna({
    'Age': df['Age'].median(),
    'Height': df['Height'].median(),
    'Weight': df['Weight'].median(),
    
})
df = df.astype({'Age': 'float32', 'Height': 'float32', 'Weight': 'float32', 'Year': 'int16'})


italydf = df[df['NOC'] == 'ITA']

#_________________ Anonymisering _______________________

#Skapar en Name_HASH kolumn med den anonymiserade namn
italydf.insert(
    loc=2, column="Name_HASH", value = italydf["Name"]
    .apply( lambda x:hashlib.sha256(x.encode()).hexdigest()
))

#Skapar en anonym version av df utan namn-kolumn
italydf_anon = italydf.drop(["Name"], axis=1)

#Vi ska göra samma sak för den globala df
df.insert(
    loc=2, column="Name_HASH", value = df["Name"]
    .apply( lambda x:hashlib.sha256(x.encode()).hexdigest()
))
df_anon = df.drop(["Name"], axis=1)

#____________________ Sports Dataframes _____________________________
        #__________________ All Sports ___________________
#DF with all ages/sports
ita_all_age = italydf_anon[italydf_anon["Age"] > 0][["Sport", "Age"]]
#Unique sports - Age
unique_sports = ita_all_age["Sport"].unique()
        #______________________Cycling_________________________

        #____________________Equestrianism_____________________

        #______________________Fencing_________________________

        #______________________Swimming________________________

#Först extraherar vi data för simning
ita_swim = italydf_anon[italydf_anon["Sport"]=="Swimming"]

#Simning medaljer utan dubletter
ita_swim_medals = (
    ita_swim.dropna(subset=["Medal"])
    .drop_duplicates(subset=["Year","Medal","Event","ID"])
)
#Medaljer/År
ita_swim_medals_year = ita_swim_medals.groupby("Year")["Medal"].count().reset_index()

#Medaljer typ / År
ita_swim_medal_type = ita_swim_medals.groupby(["Year","Medal"]).size().reset_index(name="Count")


#____________________ APP DEC __________________________

app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO], suppress_callback_exceptions= True )

#____________________ Grafer ____________________________
#   ________________ Swim Medals/Year ________________

fig_swim_med_year = px.line(
    ita_swim_medals_year,
    x= "Year",
    y= "Medal",
    title="Antal Medaljer för Italien per OS",
    markers = True,
    )

fig_swim_med_year.update_layout(
    xaxis_title = "OS År",
    yaxis_title = "Antal Medaljer"
)
#   ____________ Swim Medal Types/Year _______________
fig_swim_med_type = px.bar(
    ita_swim_medal_type,
    x = "Year",
    y = "Count",
    color = "Medal",
    color_discrete_map={
    "Gold": "#C6A907",
    "Silver": "#C0C0C0",
    "Bronze": "#CD7F32"
    },
    title= "Medaljfördelning för Italien i Simning per OS-år",
    barmode="group"
)
fig_swim_med_type.update_layout(
    xaxis_title = "OS År",
    yaxis_title = "Antal Medaljer"
)

#________________ Swim Age Distr vs Other Sports Italy ______________


color_map = {sport: "gray" for sport in unique_sports}
color_map["Swimming"] = "blue"

fig_age_all_sports = px.box(
    ita_all_age,
    x="Sport",
    y="Age",
    color="Sport",
    title="Age Distribution by Sport (Swimming Highlighted)",
    color_discrete_map=color_map,
    #points="all"
)

fig_age_all_sports.update_layout(
    xaxis_title="Sport",
    yaxis_title="Age",
    showlegend=False  # legend not needed, too many categories
)
#____________________ GRAPH CALLER __________________
#This function will show the right graphs based on sport/category chosen 
def get_sport_graphs(sport, category):
    if sport == "Swimming":
        if category == "age":
            return[
                dcc.Graph(figure=fig_age_all_sports)
            ]
        elif category == "medals":
            return[
                dcc.Graph(figure=fig_swim_med_year),
                dcc.Graph(figure=fig_swim_med_type)
            ]
    elif sport == "Cycling":
        if category == "age":
            return[
            ]
        elif category == "medals":
            return[
            ]
    elif sport == "Equestrianism":
        if category == "age":
            return[
            ]
        elif category == "medals":
            return[
            ]
    elif sport == "Fencing":
        if category == "age":
            return[
            ]
        elif category == "medals":
            return[
            ]
            
    return html.Div("No available Data yet")

#____________________ PAGES ________________________
#Here we have the general structure of the pages
def home_page():
    return html.Div([
        html.H1("Italy Olympic Dashboard — Overview"),
        html.P("General Olympic statistics about Italy will appear here."),
       
    ])

def sport_page(sport):
    return html.Div([
        html.H1(f"{sport} OS Analysis",style={"text-align":"center"}),

        #dynamisk Dropdown
        html.Div([
            dcc.Dropdown(
                id="dropdown-sport-option",
                options=SPORT_OPTIONS[sport],
                placeholder="Choose category...",
                clearable=False
            )
        ], style={"width": "50%", "margin": "20px auto"}),

        html.Div(id="sports-graphs-area", style={"margin-top":"30px"})

    ], style={"padding":"20px","margin-right":"10%"})
       

    

#___________________ APP ___________________

app.layout = html.Div([
    
    #Sidebar structure
    html.Div(
        id = "sidebar",
        children=[
            html.H1("Italy Olympic Dashboard", className="sidebar-title"),
            html.P("Select a Sport"),
            
            #create buttons
                #Home button
            dbc.Button(
                "Home",
                id="btn_home",
                n_clicks=0,
                color="primary",
                className="mb-2 w-100"
            ),

                #Sports buttons
            html.Div([
                dbc.Button(
                    sport,
                    id=f"btn-{sport.lower()}",
                    n_clicks=0,
                    color="secondary",
                    className="mb-2 w-100"
                )
                for sport in SPORTS
            ])
        ],
        style = {
            "width": "20%",
            "background-color": "#f4f4f4",
            "padding": "20px",
            "height": "100vh",
            "position": "fixed",
            "left": 0,
            "right": 0
        }
    ),
    dcc.Store(id="current-sport"),

#_____________Main content_______________
    html.Div(
        id="page-content",
        children=[
            html.H1("Välkomna till Italiens OS Dashboard!")
        ],
        style={
            "margin-left": "22%",
            "padding":"20px"
        }
    )

])



@app.callback(
    Output("page-content", "children"),
    [Input("btn_home", "n_clicks")]+
    [Input(f"btn-{sport.lower()}", "n_clicks")for sport in SPORTS]
)
def display_page(*clicks):
    #kollar vilken knapp clickades
    ctx = callback_context

    if not ctx.triggered:
        #Om inget knapp klickades visa hemsidan
        return home_page()
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

#Matchar knapp-id
    if button_id == "btn_home":
        return home_page()
    
    
    sport = button_id.replace("btn-","").capitalize()

    return sport_page(sport)

@app.callback(
    Output("current-sport","data"),
    [Input("btn_home","n_clicks")]+
    [Input(f"btn-{sport.lower()}", "n_clicks")for sport in SPORTS]
)
def store_sport(*clicks):
    ctx = callback_context
    if not ctx.triggered:
        return None
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "btn_home":
        return None
    
    sport = button_id.replace("btn-","").capitalize()
    return sport

#This makes sure the right graphs are called on the page when a category is selected
@app.callback(
    Output("sports-graphs-area","children"),
    Input("dropdown-sport-option", "value"),
    State("current-sport","data")
)
def update_graphs(category,sport):
    if sport is None or category is None:
        return []
    return get_sport_graphs(sport, category)

if __name__ == "__main__":
    app.run(debug = True)