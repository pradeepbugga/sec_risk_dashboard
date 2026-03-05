from dash import html, dcc
from dash.dependencies import Input, Output



def header():
    return html.Div(

        [

            # this is title of our dashboard

            html.H2(
                "Semiconductor Risk Narrative Intelligence",
                style={
                    "margin": 0,
                    "color": "white",
                    "fontWeight": "600"
                }
            ),
            # navigation links between pages
            html.Div([
                dcc.Link("Structural View", href="/"),
                html.Span(" | "),
                dcc.Link("Analytics View", href="/analytics"),
                html.Span(" | "),
                dcc.Link("Executive Summary", href="/executive-summary")
            ])

        ],

        className="header-bar",

        style={
            "backgroundColor": "#1F3A5F",
            "padding": "15px 30px",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between"
        }
    )