from dash import html, dcc
from components.card import card

def page2_layout():
    return html.Div(style={'fontFamily': 'Inter, sans-serif'}, children=[
    
    # use card component for clean look


    html.Div(card(

        # title and dropdown

        html.Div([
            html.H4("Risk Positioning vs Semiconductor Industry"),

            dcc.Dropdown(
                id="deviation-year-selector",
                style={"width": "200px"},
                searchable=False,
                clearable=False
            )
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between"
        })

    ),  style={
        "width": "600px",
        "margin": "0 auto"
    }),

    # showing deviation chart

    dcc.Graph(id="industry-deviation", 
            style={
                'width': '50%',
                'marginLeft': 'auto',
                'marginRight': 'auto'},
                config={'displayModeBar': False}),
    

    html.Br(),
    
    # showing title and dropdown for drift chart

    html.Div(card(

        html.Div([
            html.H4("Risk Narrative Drift"),

            dcc.Dropdown(
                id="drift-year-selector",
                style={"width": "200px"},
                searchable=False,
                clearable=False
            )
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between"
        })

    ),  style={
        "width": "400px",
        "margin": "0 auto"
    }),

    # showing drift chart
    
    dcc.Graph(id="drift-chart", 
            style={
                'width': '60%',
                'marginLeft': 'auto',
                'marginRight': 'auto'},
                config={'displayModeBar': False})      
    ])
