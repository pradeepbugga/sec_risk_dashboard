
import dash
from dash import html, dcc, callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import json
from data_store import data, macro_lookup


# callback for page 1 - Structural Analytics chart (how risk allocations change over time)

@callback(
    Output("risk-allocation", "figure"),
    Input("firm-selector", "value")
)
def update_risk_allocation(firm):
    years_dict = data["firms"][firm]["years"]
    

    dist_df = pd.DataFrame({
    year: years_dict[year]["cluster_weights"]
        for year in years_dict
    }).T.fillna(0)

    dist_df = dist_df.sort_index()

    total_weights = dist_df.sum().sort_values(ascending=False)
    dist_df = dist_df[total_weights.index]

    fig = go.Figure()
    

    # restrict to only top 8 then group rest into "Other" for visualization
    top_8_indices = total_weights.head(8).index
    other_indices = total_weights.index[8:]
    
    dist_df_final = dist_df[top_8_indices].copy()
    if not other_indices.empty:
        dist_df_final["Other"] = dist_df[other_indices].sum(axis=1)

    for col in dist_df_final.columns:

        cluster_id = str(col)

        # if value is 0, skip
        if dist_df_final[col].sum() == 0:
            continue


        if cluster_id == "Other":
            name = "Other Risks"
        else:        

            cluster_meta = macro_lookup.get(cluster_id, {})
            name = cluster_meta.get("label", f"Cluster {cluster_id}")

        fig.add_trace(go.Scatter(
            x=dist_df_final.index,
            y=dist_df_final[col],            
            stackgroup="one",
            line=dict(width=0.5),
            name=name
        ))

    # use color palette ideal for financial users

    fig.update_layout(
        colorway=[
        "#1F77B4",
        "#FF7F0E",
        "#2CA02C",
        "#D62728",
        "#9467BD",
        "#17BECF",
        "#BCBD22",
        "#8C564B",
        "#7F7F7F"
    ], 
        barmode="stack",
        template="plotly_white",
        font = dict(family="Inter, Arial, sans-serif", size = 13),
        plot_bgcolor = "white",
        paper_bgcolor = "white",
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.2,
            tracegroupgap=100,
            itemsizing='constant'),
        margin = dict(l=0, r=0, t=0, b=0)
        
        )
    #hide y axes
    fig.update_yaxes(visible=False)

    #make x axes labels gray
    fig.update_xaxes(tickfont=dict(color='#333333'))
    

 
    return fig


# callback that allows user to click on a cluster segment and see representative chunks

@callback(
    Output("chunk-state", "data"),
    Input("risk-allocation", "clickData"),
    Input("prev-chunk", "n_clicks"),
    Input("next-chunk", "n_clicks"),
    State("chunk-state", "data"),
    State("firm-selector", "value"),
)
def manage_chunk_state(clickData, prev_clicks, next_clicks, state, firm):

    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    # -----------------------------
    # 1. Chart click → Load cluster
    # -----------------------------
    if trigger == "risk-allocation" and clickData is not None:

        years_dict = data["firms"][firm]["years"]

        # note we already saved cluster weights in data json, so we just retrieve them here

        dist_df = pd.DataFrame({
            year: years_dict[year]["cluster_weights"]
            for year in years_dict
        }).T.fillna(0)

        dist_df = dist_df.sort_index()

        total_weights = dist_df.sum().sort_values(ascending=False)
        dist_df = dist_df[total_weights.index]

        curve_index = clickData["points"][0]["curveNumber"]
        year = str(clickData["points"][0]["x"])

        cluster = dist_df.columns[curve_index]
        cluster_id = str(cluster)


        # note: we have already stored representative chunks in data json, so we just retrieve them here

        chunks = years_dict[year]["representative_chunks"].get(cluster_id, [])

        return {
            "firm": firm,
            "year": year,
            "cluster_id": cluster_id,
            "chunks": chunks,
            "index": 0
        }

    # -----------------------------
    # 2. Arrow navigation
    # -----------------------------
    if state is None:
        return dash.no_update

    index = state["index"]
    total = len(state["chunks"])

    if trigger == "prev-chunk":
        index = max(0, index - 1)

    elif trigger == "next-chunk":
        index = min(total - 1, index + 1)

    state["index"] = index
    return state


# callback to display chunk details based on chunk state

@callback(
    Output("cluster-details", "children"),
    Input("chunk-state", "data")
)
def display_chunk(state):

    if state is None:
        return "Click a cluster segment to see evidence."

    if not state.get("chunks"):
        cluster_meta = macro_lookup.get(state["cluster_id"], {})
        label = cluster_meta.get("label", f"Cluster {state['cluster_id']}")

        return html.Div([
            html.H4(label),
            html.P(f"{state['firm']} | {state['year']}"),
            html.Hr(),
            html.P("No representative evidence available for this cluster-year.",
                style={"color": "#888"})
        ])


    # our goal is to show the chunk text, heading path, firm, year, source type, and chunk index
    # this explainability makes it clear where our data is coming from

    cluster_meta = macro_lookup.get(state["cluster_id"], {})
    label = cluster_meta.get("label", f"Cluster {state['cluster_id']}")

    chunk = state["chunks"][state["index"]]

    heading_path = " > ".join(chunk.get("heading_path", []))
    text = chunk["text"]
    
    if state["firm"] == "TSM":
        source_label = "Source: 20-F"
    else:
        source_label = "Source: 10-K"

    return html.Div([
        html.H4(label),
        html.Div(

            [
                html.Span(state["firm"], className="tag"),
                html.Span(state["year"], className="tag"),
                html.Span(source_label,  className="tag")
            ],

            style={
                "display": "flex",
                "gap": "8px",
                "marginBottom": "10px"
            }
        ),
        html.Hr(style={
            "marginTop":"10px",
            "marginBottom":"14px",
            "borderColor":"#e5e7eb"
        }),
        html.Div(heading_path, style={
            "fontSize": "13px",
            "color": "#6b7280",
            "marginBottom": "12px",
            "borderLeft": "3px solid #e5e7eb",
            "paddingLeft": "10px"
        }),
        html.Div(text,  style={
            "whiteSpace": "pre-wrap",
            "lineHeight": "1.7",
            "fontSize": "15px",
            "backgroundColor": "#f8fafc",
            "padding": "12px 14px",
            "borderRadius": "6px",
            "border": "1px solid #e5e7eb"
        }),
        html.Div(
            f"Chunk {state['index']+1} / {len(state['chunks'])}",
            style={
                "marginTop":"12px",
                "fontSize":"12px",
                "color":"#6b7280",
                "background":"#f1f5f9",
                "display":"inline-block",
                "padding":"3px 8px",
                "borderRadius":"4px"
            }
        )
    ])


