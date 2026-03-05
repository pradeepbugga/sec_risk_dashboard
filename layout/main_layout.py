
from dash import Dash, dcc, html
from layout.header import header
from layout.firm_selector import firm_selector
from data_store import dropdown_options, df

def create_layout(dropdown_options, default_value):

    return html.Div(style={}, children=[

        dcc.Location(id="url", refresh=False),

        header(),

        firm_selector(dropdown_options, default_value),

        dcc.Store(id="chunk-state"),

        html.Div(id="page-content")
    ])



