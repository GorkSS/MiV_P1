import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
from math import pi, sqrt, pow
from typing import List
import streamlit as st

st.set_page_config(page_title="Paco", layout="wide")

def distribute_sizes(real_size_col : pd.Series, total_rel_size : int):
    total_size = real_size_col.agg('sum')
    return real_size_col.apply(lambda s: int(total_rel_size * s / total_size))

def plotly_legend_config(fig : Figure, visible_traces : List, labels : List):
    labels_used = 0
    if visible_traces.count(True) != len(labels):
        raise Exception(f"Number of traces visible ({visible_traces.count(True)}) in legend is not equal to number of labels ({len(labels)})")
    
    if len(visible_traces) == len(fig.data):
        for i, visible in enumerate(visible_traces):
            fig.data[i]['showlegend'] = visible
            if visible:
                fig.data[i]['name'] = labels[labels_used]
                labels_used += 1
    else:
        raise Exception(f"Number of values of visibility {len(visible_traces)} is not equal to number of traces {len(fig.data)}")

if __name__ == "__main__":
    plot_df = pd.read_csv("data/global_births_full_data.csv")
    plot_df['area'] = plot_df['Radius(px)'].apply(lambda r: pi * pow(r, 2))
    plot_df['Births in 2026 (M)'] = plot_df['Births in 2026 (thousands)'] / 1000

    total_size = 160
    plot_df['og_chart_size'] = distribute_sizes(plot_df["area"], total_size)
    plot_df['new_chart_size'] = distribute_sizes(plot_df["Births in 2026 (M)"], total_size)

    # Trace 0: Original bubble plot
    bubble_fig = px.scatter(plot_df,
                    x='Continent',
                    y=[1] * len(plot_df),
                    size='og_chart_size',
                    size_max=plot_df['og_chart_size'].max(),
                    opacity=1,
                    custom_data=["Births in 2026 (M)"]
                    )
    bubble_fig.update_traces(marker=dict(color='red'))
    bubble_fig.update_layout(hovermode="x unified")
    bubble_fig.update_yaxes(title_text="", showticklabels=False, showgrid=False, zeroline=False)
    bubble_fig.update_xaxes(showgrid=False, zeroline=False)

    # Trace 1: Original bubble plot with correct proportions
    bubble_fig.add_trace(
        px.scatter(plot_df,
                    x='Continent',
                    y=[0] * len(plot_df),
                    size='new_chart_size',
                    size_max=plot_df['new_chart_size'].max(),
                    opacity=1,
                    custom_data=["Births in 2026 (M)"],
                    ).data[0])

    bubble_fig.update_traces(hovertemplate="Births in 2026 (M): %{customdata[0]}",
                    marker=dict(line_width=0))

    plotly_legend_config(bubble_fig, [True, True], ["Original chart", "Updated chart"])

    fig = Figure()

    # Trace 2: Bar plot with source data
    bar_fig = px.bar(plot_df, x='Continent', y='Births in 2026 (M)')

    # Trace 3: Radar plot with source data
    radar_fig = px.line_polar(plot_df, r="Births in 2026 (M)", theta="Continent", line_close=True)
    
    fig.add_trace(bar_fig.data[0])
    fig.add_trace(radar_fig.data[0])

    fig.update_traces(hovertemplate="Births in 2026 (M): %{y}",
                  visible=False,
                  selector=dict(type='scatterpolar'))

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                active=0,
                buttons=list([
                    dict(
                        args=[
                                {"visible": [True, False],
                                "x": [plot_df["Continent"]],
                                "y": [plot_df["Births in 2026 (M)"]],
                                "r": [],
                                "theta": []},
                                {"yaxis.showgrid": True,
                                "yaxis.showticklabels": True}
                            ],
                        label="Bar Plot",
                        method="update"
                    ),
                    dict(
                        args=[
                                {"visible": [False, True],
                                "x": [],
                                "y": [],
                                "r": [plot_df["Births in 2026 (M)"]],
                                "theta": [plot_df["Continent"]]},
                                {"yaxis.showgrid": False,
                                "yaxis.showticklabels": False}
                            ],
                        label="Radar Plot",
                        method="update"
                    )
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0,
                xanchor="left",
                y=1.15,
                yanchor="top",
            ),
        ]
    )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(bubble_fig)
    with right:
        st.plotly_chart(fig)