from dash import html, dcc
from data_store import dropdown_options, df


def firm_selector(dropdown_options, default_value):
    return  html.Div(html.Div(
        [

            # dropdown for selecting firm
            
            html.Div(
                "Company",
                style={
                    "fontWeight": 500,
                    "marginRight": "10px"
                }
            ),
            dcc.Dropdown(
                id="firm-selector",
                options=dropdown_options,
                value=df['Ticker'].iloc[0],
                searchable=False,
                clearable=False,
                style={
                    "width": "220px"
                }
            )
        ],
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "gap": "10px",
            "padding": "12px 18px",
            "backgroundColor": "white",
            "borderRadius": "6px",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
            "margin": "20px auto"
        }
    ), style={"textAlign": "center"})