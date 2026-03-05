
import dash
from dash import dcc, html, callback
from dash.dependencies import Input, Output, State
from plotly import graph_objs as go
import pandas as pd
import json
from data_store import data, macro_lookup


# callback for updating deviation year options and figure
@callback(
    Output("deviation-year-selector", "options"),
    Output("deviation-year-selector", "value"),
    Input("firm-selector", "value")
)
def update_deviation_year_options(firm):

    years = sorted(data["firms"][firm]["years"].keys())

    options = [
        {"label": y, "value": y}
        for y in years
    ]

    return options, years[-1]



# callback for updating relative positioning vs industry figure

@callback(
    Output("industry-deviation", "figure"),
    Input("firm-selector", "value"),
    Input("deviation-year-selector", "value")
)
def update_relative_positioning(firm, year):

    years_dict = data["firms"][firm]["years"]
    year = str(year)

    firm_weights = pd.Series(
        years_dict[year]["cluster_weights"]
    ).astype(float)

    # --- Collect industry cluster weights ---
    cluster_accumulator = []

    for other_firm in data["firms"]:
        if year in data["firms"][other_firm]["years"]:
            cluster_accumulator.append(
                data["firms"][other_firm]["years"][year]["cluster_weights"]
            )

    industry_df = pd.DataFrame(cluster_accumulator).fillna(0)

    #collect industry mean and std

    industry_mean = industry_df.mean()
    industry_std = industry_df.std().replace(0, 1e-6)  # avoid divide-by-zero

    # --- Compute Z-scores ---
    z_scores = (firm_weights - industry_mean) / industry_std

    # Top 10 strongest deviations
    z_scores = z_scores.reindex(
        z_scores.abs().sort_values(ascending=False).index
    ).head(10)

    # Sort negative → positive (useful for bar chart)
    z_scores = z_scores.sort_values()

    # color positives and negatives differently
    colors = [
        "#4F6BED" if v > 0 else "#F28E2B"
        for v in z_scores.values
    ]

    # make sure to get labels for clusters
    labels = [
        macro_lookup[str(cid)]["label"]
        for cid in z_scores.index
    ]


    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=z_scores.values,
        y=labels,
        orientation="h",
        marker=dict(color=colors),
        hovertemplate="%{y}<br>Z-score: %{x:.2f}<extra></extra>",
        text=[f"{v:+.1f}" for v in z_scores.values],
        textposition="outside"
    ))

    fig.update_layout(
        height=500,
        margin=dict(l=300, t=40, b=40),
        template="plotly_white",
        yaxis=dict(ticklabelstandoff=30),
    )

    # reverse y axis to have most negative on top
    fig.update_yaxes(autorange="reversed")

    # add vertical line at x=0 as reference
    fig.add_vline(x=0, line_color="#222222", line_width=1)

    # add annotation explaining the chart
    fig.add_annotation(
        text="0 = Industry Average<br>+ = Greater narrative emphasis<br>– = Lower narrative emphasis",
        xref="paper",
        yref="paper",
        x=1.12,
        y=1,
        showarrow=False,
        align="left",
        bordercolor="#e5e7eb",
        borderwidth=1,
        borderpad=20,
        #very light gray
        bgcolor="#f8f8f8",
        font=dict(size=14)
    )

    # label for the zero line
    fig.add_annotation(
        x=0,
        y=1.05,
        xref="x",
        yref="paper",
        text="Industry Average",
        showarrow=False,
        
        font=dict(size=14, color="#222222")
    )
    
    # expand the x axis a bit so that labels don't get cut off
    xmin = z_scores.min() - 0.3
    xmax = z_scores.max() + 0.4

    #hide x axis labels
    fig.update_xaxes(range=[xmin, xmax], showgrid=False, visible=False)

    return fig


# callback for risk narrative drift

@callback(
    Output("drift-year-selector", "options"),
    Output("drift-year-selector", "value"),
    Input("firm-selector", "value")
)
def update_drift_year_options(firm):

    years = sorted(data["firms"][firm]["years"].keys())

    transitions = [
        {"label": f"{years[i]} → {years[i+1]}", "value": f"{years[i]}_{years[i+1]}"}
        for i in range(len(years)-1)
    ]

    return transitions, transitions[-1]["value"]

@callback(
    Output("drift-chart", "figure"),
    Input("firm-selector", "value"),
    Input("drift-year-selector", "value")
)
def update_drift_detail(firm, year_transition):

    from_year, to_year = year_transition.split("_")

    # --- Firm drift ---
    w1 = pd.Series(
        data["firms"][firm]["years"][from_year]["cluster_weights"]
    ).astype(float)

    w2 = pd.Series(
        data["firms"][firm]["years"][to_year]["cluster_weights"]
    ).astype(float)

    firm_delta = w2 - w1

    # --- Collect industry drift ---
    industry_deltas = []

    for other_firm in data["firms"]:

        years = data["firms"][other_firm]["years"]

        if from_year in years and to_year in years:

            ow1 = pd.Series(
                years[from_year]["cluster_weights"]
            ).astype(float)

            ow2 = pd.Series(
                years[to_year]["cluster_weights"]
            ).astype(float)

            industry_deltas.append(ow2 - ow1)

    industry_df = pd.DataFrame(industry_deltas).fillna(0)

    industry_mean = industry_df.mean()
    industry_std = industry_df.std().replace(0, 1e-6)

    # Align indices
    firm_delta = firm_delta.reindex(industry_mean.index).fillna(0)

    # --- Z score drift ---
    z_drift = (firm_delta - industry_mean) / industry_std

    # Sort by magnitude
    z_drift = z_drift.reindex(
        z_drift.abs().sort_values(ascending=False).index
    ).head(8)


    # Sort negative → positive
    z_drift = z_drift.sort_values()


    # color positives and negatives differently

    colors = [
        "#4F6BED" if v > 0 else "#F28E2B"
        for v in z_drift.values
    ]

    # make sure to get labels for clusters

    labels = [
        macro_lookup[str(cid)]["label"]
        for cid in z_drift.index
    ]

    fig = go.Figure()

    # use similar logic as above to add bars

    fig.add_trace(go.Bar(
        x=z_drift.values,
        y=labels,
        
        orientation="h",
        marker=dict(color=colors),
        hovertemplate="%{y}<br>Z-score: %{x:.2f}<extra></extra>",
        text=[f"{v:+.1f}" for v in z_drift.values],
        textposition="outside"
    ))
    fig.update_yaxes(autorange="reversed")
    fig.add_vline(x=0, line_color="#222222", line_width=1)
    fig.update_layout(
        margin=dict(t=40, b=40, l=300, r=100),
        height=500,
        template = "plotly_white",
        yaxis=dict(ticklabelstandoff=30)
    )

    
    fig.add_annotation(
        x=0,
        y=1.05,
        xref="x",
        yref="paper",
        text="No Change",
        showarrow=False,
        
        font=dict(size=14, color="#222222")
    )


    fig.add_annotation(
        text="0 = No change in narrative emphasis<br>+ = More narrative emphasis vs prior year <br>– = Less narrative emphasis vs prior year",
        xref="paper",
        yref="paper",
        x=1.15,
        y=1,
        showarrow=False,
        align="left",
        bordercolor="#e5e7eb",
        borderwidth=1,
        borderpad=10,
        #very light gray
        bgcolor="#f8f8f8",
        font=dict(size=14)
    )


    xmin = z_drift.min() - 0.6
    xmax = z_drift.max() + 0.6

    #hide x axis labels
    fig.update_xaxes(range=[xmin, xmax], showgrid=False, visible=False)

    return fig
