import dash
from dash import dcc, html, callback
from dash.dependencies import Input, Output
from pages.structural import page1_layout 
from pages.analytics import page2_layout
from pages.executive import page3_layout


# this callback updates the page content based on the URL pathname
# we have 3 pages -> page 1 and 2 for charts, and page 3 for executive summary

@callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/analytics":
        return page2_layout()
    if pathname == "/executive-summary":
        return page3_layout()
    else:
        return page1_layout()
