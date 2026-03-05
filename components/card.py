from dash import html

def card(children):
    return html.Div(
        children,
        style={
            "backgroundColor": "white",
            "borderRadius": "6px",
            "padding": "20px",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
            "marginBottom": "20px"
        }
    )
