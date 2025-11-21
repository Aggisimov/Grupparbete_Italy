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
        {"label": "General", "value": "general"}
    ],
    "Fencing":[
        {"label":"Ålder", "value":"age"},
        {"label":"Medaljer", "value": "medals"},
    ],
    "Equestrianism":[
        {"label":"Ålder", "value":"age"},
        {"label":"Medaljer", "value": "medals"},
        {"label":"Kön", "value":"gender"},
        {"label":"Aktiva År", "value": "aktiva"}
    ],
    "Swimming":[
        {"label":"Ålder", "value":"age"},
        {"label":"Medaljer", "value": "medals"},
    ]
}
#_________________ TEXT BLOCKS __________________
HOME_TEXT = {
    "medals_won": "Here we can see the medals won by Italy on Summer and Winter OS",
    "medals_distribution": "The total medals won by the top 20 countries. Italy is the 6th top medalist.",
    "medals_sport" : "Top 10 sports by number of medals won"
}
SWIMMING_TEXT = {
    "age_main": "This graph shows the range of ages of Italian swimmers",
    "age_medals": "This graph shows the ages of Italian medalist swimmers",
    "age_compare": "This graph displays the age distribution of all Italian athletes. Swimmers Highlighted",
    "medals_year": "Here we can see the medals won by Italy in swimming on each Olympic year",
    "medals_types": "This graph shows what medals were won each year"
}

CYCLING_TEXT = {
    "medals_age": f"How does aging affect likelihood to score a medal in Olympic cycling? While entering their 30s (and even 40's) may not end the chances of an Olympic medal for athletes of endurance sports, likelihood drops sharply after passing their mid-20s.",
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
unique_sports_age = ita_all_age["Sport"].unique()

#All medals
global_medals = df_anon.dropna(subset=["Medal"]).groupby("NOC")["Medal"].count()
top20_global = global_medals.sort_values(ascending=False).head(20).reset_index()
top20_global["Color"] = top20_global["NOC"].apply(
    lambda x: "red" if x == "ITA" else "gray"
)

#Athletes gender/year
gender_year = italydf_anon.groupby(["Year", "Sex"]).size().reset_index(name="Count")

#Italy unique medals
ita_medals_unique = (
    italydf_anon[italydf_anon["Medal"] != "None"]
    .drop_duplicates(subset=["Games", "Event", "Medal"])
)

#Italy medals by sport
medals_by_sport_all = (
    ita_medals_unique
    .groupby("Sport")["Medal"]
    .count()
    .sort_values(ascending=False)
)

#Italy Summer Medals
ita_summer_unique = (
    italydf_anon[
        (italydf_anon["Medal"] != "None") &
        (italydf_anon["Season"] == "Summer")
    ]
    .drop_duplicates(subset=["Games", "Event", "Medal"])
)
ita_summer_unique["Year"] = ita_summer_unique["Games"].str[:4].astype(int)

summer = (
    ita_summer_unique
    .groupby("Year")["Medal"]
    .count()
    .reset_index()
)
summer["Season"] = "Sommar"

#Italy Winter Medals
ita_winter_unique = (
    italydf_anon[
        (italydf_anon["Medal"] != "None") &
        (italydf_anon["Season"] == "Winter")
    ]
    .drop_duplicates(subset=["Games", "Event", "Medal"])
)
ita_winter_unique["Year"] = ita_winter_unique["Games"].str[:4].astype(int)

winter = (
    ita_winter_unique
    .groupby("Year")["Medal"]
    .count()
    .reset_index()
)
winter["Season"] = "Vinter"

ita_medals_combined = pd.concat([summer, winter], ignore_index=True)

        #______________________Cycling_________________________

cycling_df = df_anon[df_anon["Sport"] == "Cycling"].copy()

cycling_df["Event"] = cycling_df["Event"].str.replace(
    "Cycling Women's Team Pursuit",
    "Cycling Women's Team Pursuit, 4,000 metres",
)

def cycling_base_event(cycling_event):
    cycling_event = cycling_event.replace("Cycling ", "")
    cycling_event = cycling_event.replace("Men's ", "")
    cycling_event = cycling_event.replace("Women's ", "")
    return cycling_event

cycling_df.loc[:, "Base Event"] = cycling_df["Event"].apply(cycling_base_event)

unique_cycling_events = cycling_df["Base Event"].unique()

men_event_amount = (cycling_df[cycling_df["Sex"] == "M"].groupby("Base Event")["Year"].nunique())
sorted_base_events = sorted(unique_cycling_events, key=lambda x: men_event_amount.get(x, 0), reverse=True)

cycling_df["Grouped Event"] = cycling_df.apply(lambda cycling_heatmap_row: f"{"Men's" if cycling_heatmap_row["Sex"] == "M" else "Women's"} {cycling_heatmap_row["Base Event"]}", axis=1)

cycling_heatmap_data = cycling_df.groupby(["Grouped Event", "Year"])["ID"].count().reset_index()
cycling_heatmap_data["Base Event"] = cycling_heatmap_data["Grouped Event"].apply(lambda x: x.split(" ", 1)[1])

cycling_heatmap_data["Base Event Order"] = cycling_heatmap_data["Base Event"].apply(lambda x: sorted_base_events.index(x))
cycling_heatmap_data["Gender"] = cycling_heatmap_data["Grouped Event"].apply(lambda x: x.split(" ", 1)[0])
cycling_heatmap_data = cycling_heatmap_data.sort_values(by=["Base Event Order", "Gender"])

cycling_heatmap_data = cycling_heatmap_data.drop(columns=["Base Event", "Base Event Order", "Gender"])
cycling_heatmap_data = cycling_heatmap_data.iloc[::-1]

cycling_color_scale = [[0.0, "white"], [0.001, "salmon"], [1.0, "blue"]]

#____cycling Medal by country______
national_cycling_df = cycling_df[["NOC", "Year", "Event", "Medal"]].drop_duplicates()
cycling_medal_distribution = national_cycling_df.groupby("NOC")["Medal"].value_counts().unstack().fillna(0)
cycling_medal_distribution_NOC = cycling_medal_distribution.assign(Total=cycling_medal_distribution.sum(axis=1)).sort_values(by="Total", ascending=False).iloc[:15]

#________ Cycling medals by age _______________


cycling_medal_distribution = (
    cycling_df.groupby("Age")["Medal"]
    .value_counts()
    .unstack(fill_value=0)
    .reset_index()
)

cycling_medal_distribution_melted = cycling_medal_distribution.melt(
    id_vars="Age",
    value_vars=["Bronze", "Silver", "Gold"],
    var_name="Medal",
    value_name="Count"
)

#_______Cycling medal years ______________
cycling_medal_counts = (
    cycling_df.groupby(["Year", "NOC"])["Medal"].count().unstack(fill_value=0)
)

cycling_medal_proportion_plot = (
    cycling_medal_counts
    .assign(not_italy=lambda df: df.drop(columns=["ITA"]).sum(axis=1))
    [["not_italy", "ITA"]]
    .reset_index()
    .melt(id_vars="Year", var_name="Group", value_name="Medals")
)

cycling_participant_distribution = (
    cycling_df.groupby(["Age", "NOC"])["ID"]
    .nunique()
    .unstack(fill_value=0)
    .reset_index()
)

cycling_participant_distribution["Not_Italy"] = (
    cycling_participant_distribution.drop(columns=["Age", "ITA"], errors="ignore")
    .sum(axis=1)
)
cycling_participant_distribution = cycling_participant_distribution[["Age", "ITA", "Not_Italy"]].fillna(0)

participant_distribution_melted = cycling_participant_distribution.melt(
    id_vars="Age",
    value_vars=["Not_Italy", "ITA"],
    var_name="Group",
    value_name="Count"
)


        #____________________Equestrianism_____________________

df_equestrianism = df[df['Sport'] == 'Equestrianism']

ita_df_equestrianism = italydf_anon[italydf_anon['Sport'] == 'Equestrianism']

medals_per_country_eq = (df_equestrianism[df_equestrianism['Medal'].notnull()]['NOC'].value_counts().reset_index())
medals_per_country_eq.columns = ['NOC', 'Count']

equestrianism = italydf_anon[italydf_anon["Sport"] == "Equestrianism"].copy()
equestrianism["Group"] = "Equestrianism"

other_sports_eq = italydf_anon[italydf_anon["Sport"] != "Equestrianism"].copy()
other_sports_eq["Group"] = "Other sports"

age_compare_eq = pd.concat([equestrianism, other_sports_eq], ignore_index=True)

mean_age_eq = (
        age_compare_eq.groupby("Group")["Age"]
        .mean()
        .reset_index()
        .round(1)
    )

#EQ activity years
age_span_per_person = ita_df_equestrianism.groupby('Name_HASH').agg(
    MinAge=('Age', 'min'),
    MaxAge=('Age', 'max'),
    ActiveYears=('Year', lambda x: x.nunique())
).reset_index()

longest_active = age_span_per_person['ActiveYears'].max()

bins = list(range(0, int(longest_active + 5), 1))

# EQ Gender distribution
counts_eq = ita_df_equestrianism.groupby(['Year','Sex']).size().unstack().fillna(0)
df_counts = counts_eq.reset_index().melt(id_vars='Year', value_name='Count', var_name='Sex')

#EQ Medals / type
ita_eq_medals = ita_df_equestrianism.dropna(subset=['Medal']).drop_duplicates(subset=['Year', 'Medal', 'Event', 'ID'])
eq_medals_type= ita_eq_medals.groupby(['Year', 'Medal']).size().reset_index(name="Count")

        #______________________Fencing_________________________

fencing = italydf_anon[italydf_anon["Sport"] == "Fencing"].copy()

fencing_unique_medals = (
    fencing[fencing["Medal"] != "None"]
    .drop_duplicates(subset=["Games", "Event", "Medal"])
)
# Medals by type -Fen

medals_by_type_fen = (
    fencing_unique_medals
    .pivot_table(
        index="Year",
        columns="Medal",
        values="ID",      # bara för count
        aggfunc="count",
        fill_value=0
    )
    .reset_index()
)
medals_type_cols = [c for c in medals_by_type_fen.columns if c in ["Gold", "Silver", "Bronze"]]
medals_by_type_fen["Total"] = medals_by_type_fen[medals_type_cols].sum(axis=1)

#Fenc_Age_Distr
fencing = italydf_anon[italydf_anon["Sport"] == "Fencing"].copy()
fencing["Group"] = "Fencing"

other_sports = italydf_anon[italydf_anon["Sport"] != "Fencing"].copy()
other_sports["Group"] = "Other sports"

age_compare = pd.concat([fencing, other_sports], ignore_index=True)

#Men age _Fen
mean_age = (
    age_compare.groupby("Group")["Age"]
    .mean()
    .reset_index()
    .round(1)
)


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
#___________________ Italy ________________________
#______________ Italy medals compared to world __________
fig_global_medals = px.bar(
    top20_global,
    x = "NOC",
    y= "Medal",
    title= "Global top 20 medalist countries",
    color= "Color",
    color_discrete_map={"red":"red", "gray":"gray"},
    )
fig_global_medals.update_layout(
    xaxis_title="Country",
    yaxis_title="Medals",
    showlegend = False,
    xaxis={'categoryorder':'array', 'categoryarray':top20_global["NOC"]}
)
#_____________Italy Medals per Year _________

fig_ita_medal_year = px.line(
    ita_medals_combined,
    x="Year",
    y="Medal",
    color="Season",
    markers=True,
    title="Medaljer per år - Italien (Sommar och vinter)"
)

fig_ita_medal_year.update_layout(
    legend_title_text="Säsong",
    yaxis_title="Antal medaljer"
)

#__________________ Italy Medals by Sport _____________
fig_medal_sport = px.bar(
    medals_by_sport_all.head(10),
    title="Top 10 sporter där Italien tagit flest medaljer",
    labels={"index": "Sport", "value": "Antal medaljer"}
)
fig_medal_sport.update_layout(
       showlegend = False
)
# __________________ FENCING _______________________
#    __________________Fencing Medals by year ______________
fig_fenc_medal = px.bar(
    medals_by_type_fen,
    x="Year",
    y="Total",
    title="Italy Fencing - Total Medals per Year",
    labels={"Total": "Total Medals"}
)

#_________________ Fencing Medals by Type ________
fig_medal_by_type_gsb = px.bar(
    medals_by_type_fen,
    x="Year",
    y=["Gold", "Silver", "Bronze"],
    title="Italy Fencing - Medals per Year",
    labels={"value": "Number of Medals", "variable": "Medal Type"},
    color_discrete_map={
        "Gold": "#F6D411",
        "Silver": "#D7D4D4",
        "Bronze": "#CD7532"
    }
)
fig_medal_by_type_gsb.update_layout(barmode="stack")

#________________Fencing Age Distribution _________________

fig_fen_age_distr = px.histogram(
    age_compare,
    x="Age",
    nbins=30,
    histnorm="percent",
    facet_row="Group",
    title="Age Distribution - Fencing vs Other Italian Sports",
    labels={"Age": "Age", "Group": "Group"}
)
fig_fen_age_distr.update_layout(
    height=700,
    margin=dict(t=80, b=40),
    font=dict(size=14),
)
fig_fen_age_distr.update_xaxes(range=[10, 50])     # adjust if you have older athletes
fig_fen_age_distr.update_yaxes(matches=None)

#__________________CYCLING ________________________
#Heatmap
cycling_heatmap_fig = px.density_heatmap(
    cycling_heatmap_data,
    x="Year",
    y="Grouped Event",
    z="ID",
    nbinsx=int((cycling_df["Year"].max()-cycling_df["Year"].min()+4)/4),
    color_continuous_scale=cycling_color_scale,
    title="Cycling through the Olympics",
    labels={"ID": "Number of Participants"},
    height=800,
    text_auto=True,
)

cycling_heatmap_end_year = cycling_df["Year"].max()
cycling_heatmap_tick_vals = list(range(1896, cycling_heatmap_end_year + 1, 8))


cycling_heatmap_fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Event",
    coloraxis_colorbar={"title": "Participants"},
    xaxis=dict(tickmode="array", tickvals=cycling_heatmap_tick_vals)
    
)

cycling_heatmap_fig.add_annotation(
    text="Amount of cycling event participants by year and event", 
    xref="paper", yref="paper", x=0.5, y=1.05, 
    showarrow=False, font=dict(size=14))

#Cycling medals by country______

national_cycling_fig = px.bar(
    cycling_medal_distribution_NOC.reset_index(),
    x="NOC",
    y=["Bronze", "Silver", "Gold"],
    title="Cycling medal distribution by country",
    labels={"value": "Number of medals", "variable": "Medal Type", "NOC": "Country"},
    color_discrete_map={"Bronze": "saddlebrown", "Silver": "silver", "Gold": "gold"},
    barmode="stack"
)

national_cycling_fig.update_layout(xaxis_tickangle=-45)

#Cycling medals by age _____________

cycling_medal_distribution_fig = px.bar(
    cycling_medal_distribution_melted,
    x="Age",
    y="Count",
    color="Medal",
    title="Cycling medal distribution by athlete age",
    labels={"Age": "Athlete age", "Count": "Number of medals"},
    color_discrete_map={"Bronze": "saddlebrown", "Silver": "silver", "Gold": "gold"},
    barmode="stack"
)
#Cycling medals over years ___________________

cycling_proportion_medal_fig = px.bar(
    cycling_medal_proportion_plot,
    x="Year",
    y="Medals",
    color="Group",
    title="Italy's historical medal proportion in Olympic cycling",
    labels={"Medals": "Number of Medals", "Year": "Year"},
    color_discrete_map={"not_italy": "blue", "ITA": "salmon"},
    barmode="stack"
)

cycling_proportion_medal_fig.update_layout(
    legend_title_text='Medals by'
).for_each_trace(
    lambda trace: trace.update(name="Not Italy")
    if trace.name == "not_italy" else trace.update(name="Italy")
)

#Cycling Age Distribution
cycling_participant_age_distribution_fig = px.bar(
    participant_distribution_melted,
    x="Age",
    y="Count",
    color="Group",
    title="Cyclist distribution by age",
    labels={"Age": "Athlete age", "Count": "Number of participants"},
    color_discrete_map={"ITA": "salmon", "Not_Italy": "blue"},
    barmode="stack"
)

cycling_participant_age_distribution_fig.update_layout(legend_title_text="Participants by").for_each_trace(
    lambda trace: trace.update(name="Not Italy")
    if trace.name == "Not_Italy" else trace.update(name="Italy")
)

#_____________ EQUESTRIANISM __________________
#Medal distribution_country
fig_eq_NOC_medal_distribution = px.bar(
    medals_per_country_eq,
    x='NOC',
    y='Count',
    title="Equestrianism medals per country",
    labels={'NOC': 'Country', 'Count': 'Number of Medals'}
)

#Age Distribution
fig_age_distribution_eq_vs_other = px.histogram(
        age_compare_eq,
        x="Age",
        nbins=30,
        histnorm="percent",
        facet_row="Group",
        title="Age Distribution - Equestrianism vs Other Italian Sports",
        labels={"Age": "Age", "Group": "Group"}
    )
fig_age_distribution_eq_vs_other.update_layout(
        height=700,
        margin=dict(t=80, b=40),
        font=dict(size=14),
    )

    # Adjust axes to remove the messy right-end overflow
fig_age_distribution_eq_vs_other.update_xaxes(range=[10, 65])
fig_age_distribution_eq_vs_other.update_yaxes(matches=None)


#Activity Years
fig_eq_activity_years = px.histogram(
        age_span_per_person,
        x='ActiveYears',
        nbins=len(bins),
        title="Amount of Active Years for Italian Athletes",
        labels={"ActiveYears": "Number of Games", "count": "Numbr of Athletes"}
    )

fig_eq_activity_years.update_traces(marker_line_width=1, marker_line_color="black")
fig_eq_activity_years.update_layout(bargap=0.05)

#Gender Distribution EQ
fig_eq_gender_distribution = px.bar(
    df_counts,
    x='Year',
    y='Count',
    color='Sex',
    barmode='group',
    title="Gender distribution of Italian equestrianism athletes over the years"
)

#Medals by type / year

fig_eq_medals_type = px.bar(
    eq_medals_type,
    x = 'Year',
    y = 'Count',
    color = 'Medal',
    color_discrete_map={
        "Gold": "#C6A907",
        "Silver": "#C0C0C0",
        "Bronze": "#CD7F32"},
    title= "Medal Distribution for Italy per year",
    barmode='group'
)

fig_eq_medals_type.update_layout(
        xaxis_title = "Year",
        yaxis_title = "Number of Medals"
)
# ______________SWIMMING _______________________
#   ________________ Swim Medals/Year ________________

fig_swim_med_year = px.bar(
    ita_swim_medals_year,
    x= "Year",
    y= "Medal",
    title="Antal Medaljer för Italien per OS"
    
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


color_map = {sport: "gray" for sport in unique_sports_age}
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
                dcc.Graph(figure=fig_age_all_sports),
                html.P(SWIMMING_TEXT["age_main"], className="graph-text"),
            ]
        elif category == "medals":
            return[
                dcc.Graph(figure=fig_swim_med_year),
                html.P(SWIMMING_TEXT["medals_year"], className= "graph-text"),

                dcc.Graph(figure=fig_swim_med_type),
                html.P(SWIMMING_TEXT["medals_types"], className="graph-text")
            ]
    elif sport == "Cycling":
        if category == "age":
            return[

                dcc.Graph(figure=cycling_participant_age_distribution_fig),
                
                dcc.Graph(figure=cycling_medal_distribution_fig),
                html.P(CYCLING_TEXT["medals_age"],className="graph-text")

            ]
        elif category == "medals":
            return[
                dcc.Graph(figure=national_cycling_fig),

                dcc.Graph(figure=cycling_proportion_medal_fig)

            ]
        elif category == "general":
            return[
                dcc.Graph(figure=cycling_heatmap_fig)
            ]
    elif sport == "Equestrianism":
        if category == "age":
            return[
                dcc.Graph(figure=fig_age_distribution_eq_vs_other)
            ]
        elif category == "medals":
            return[
                dcc.Graph(figure=fig_eq_NOC_medal_distribution),

                dcc.Graph(figure=fig_eq_medals_type)
            ]
        elif category == "gender":
            return[
                dcc.Graph(figure=fig_eq_gender_distribution)
            ]
        elif category == "aktiva":
            return[
                dcc.Graph(figure=fig_eq_activity_years)

            ]
    elif sport == "Fencing":
        if category == "age":
            return[
                dcc.Graph(figure=fig_fen_age_distr)

            ]
        elif category == "medals":
            return[
                dcc.Graph(figure=fig_fenc_medal),

                dcc.Graph(figure=fig_medal_by_type_gsb),
            ]
            
    return html.Div("No available Data yet")

#____________________ PAGES ________________________
#Here we have the general structure of the pages
def home_page():
    return html.Div([
        html.H1("Italy Olympic Dashboard — Overview"),
        
        html.H2("Global Medal Ranking . Top 20"),
        dcc.Graph(figure=fig_global_medals),
        html.P(HOME_TEXT["medals_distribution"],className="graph_text"),


       html.H2("Italy medals per year"),
       dcc.Graph(figure=fig_ita_medal_year),
       html.P(HOME_TEXT["medals_won"],className="graph-text"),

       html.H2("Italy Medals by Sport"),
       dcc.Graph(figure = fig_medal_sport),
       html.P(HOME_TEXT["medals_sport"], className="graph-text")
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