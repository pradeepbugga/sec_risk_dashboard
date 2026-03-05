import json
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import glob, os
from layout.main_layout import create_layout



import callbacks.analytics_callbacks
import callbacks.structural_callbacks
import callbacks.executive_callbacks    
import callbacks.home_callbacks

from data_store import dropdown_options, df

app = dash.Dash(
    __name__, suppress_callback_exceptions=True,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
    ]
)


app.layout = create_layout(dropdown_options, df["Ticker"].iloc[0])


server = app.server

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=True)