from dash import Dash, html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import hashlib

#____________________ DATA ______________________
SPORTS = ["Cycling","Equestrianism","Fencing", "Swimming"]
data = "athlete_events.csv"

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

#____________________ Sport _____________________________
       
        #______________________Swimming_________________________

#Först extraherar vi data för simning
ita_swim = italydf_anon[italydf_anon["Sport"]=="Swimming"]

#och börjar kolla på medaljer och att filtrera ut dubletter 
ita_swim_medals = (
    ita_swim.dropna(subset=["Medal"])
    .drop_duplicates(subset=["Year","Medal","Event","ID"])
)
#Medaljer/År
ita_swim_medals_year = ita_swim_medals.groupby("Year")["Medal"].count().reset_index()

#Medaljer typ / År
ita_swim_medal_type = ita_swim_medals.groupby(["Year","Medal"]).size().reset_index(name="Count")

#DF with all ages/sports
ita_all_age = italydf_anon[italydf_anon["Age"] > 0][["Sport", "Age"]]

#Unique sports

unique_sports = ita_all_age["Sport"].unique()




app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO] )
#____________________ Grafer ____________________________
#   ________________ Swim Medals/Year ________________

#Nu kan vi skapa vår första plot med plotly
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

#____________________ PAGES ________________________
def home_page():
    return html.Div([
        html.H1("Italy Olympic Dashboard — Overview"),
        html.P("General Olympic statistics about Italy will appear here."),
       
    ])

def sport_page(sport):
    if sport == "Cycling":
        return html.Div([
            html.H1("Cycling OS Analysis"),
        ])

    elif sport == "Equestrianism":
        return html.Div([
            html.H1("Equestrianism OS Analysis"),
        ])
    
    elif sport == "Fencing":
        return html.Div([
            html.H1("Fencing OS Analysis"),
        ])
    
    elif sport == "Swimming":
        return html.Div([
            html.H1("Swimming OS Analysis", style={"text-align":"center"}),

            html.Div([
                dcc.Graph(figure=fig_swim_med_year),
            ], style={"margin-top": "20px"}),

            html.Div([
                dcc.Graph(figure=fig_swim_med_type),
            ], style={"margin-top": "20px"}),
            
            html.Div([
                dcc.Graph(figure=fig_age_all_sports),
            ], style={"margin-top": "20px"}),


        ], style={"padding":"20px", "margin-right":"10%"})


    else: return home_page()
    

#___________________ APP ___________________

app.layout = html.Div([
    
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

if __name__ == "__main__":
    app.run(debug = True)