from dash import html, dcc
from components.card import card

def page1_layout():
    return html.Div(style={'fontFamily': 'Inter, sans-serif',
                            'maxWidth': '1200px',
                            'margin': '0 auto',
                            'padding': '20px',
                            'backgroundColor': '#f5f7fa'
    
    }, children=[
    
    
    # card container with title, dropdown, and graph for risk allocation

    card([
    html.H4("Find out company-specific exposure to industry-wide risks", 
                style={
                    'fontFamily': 'Inter, sans-serif',
                    'textAlign': 'center',
                    'fontWeight': '600'
                    }),


    html.Div([
        html.H5(["Click on a data point", html.Br(), "to see source text below"], 
                style={
                    'fontFamily': 'Inter, sans-serif',
                    'marginLeft': '5%',
                    'textAlign': 'center',
                    'fontWeight': '500'
                    }),
        dcc.Graph(
            id="risk-allocation", 
            style={'width': '100%',                   
            },
            config={'displayModeBar': False}
        )
    ], style={
        'display': 'flex',           # Turns the container into a flexbox
        'alignItems': 'center',      # Vertically centers all children
        'justifyContent': 'center',   # Centrally aligns the whole group horizontally
        'gap': '5px'                # Adds space between children
    })
    ]),

    # card for bottom panel showing source evidence with pagination
  
    card([html.H4("Source Evidence"), 
   
    html.Div(
        id="cluster-details",
        style={
            "overflowY": "scroll",
            "height": "400px",
            "marginTop": "20px",
            "padding": "10px",
            "border": "1px solid #ddd",
            #color light gray
            'backgroundColor': '#f9f9f9',
            #font color
            'color': '#333333'
        }
    )]),

    html.Div([
        html.Button("←", id="prev-chunk", n_clicks=0),
        html.Button("→", id="next-chunk", n_clicks=0),
    ], style={"marginTop": "10px"})
])
