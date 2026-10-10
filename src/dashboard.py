import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
from math import pi, sqrt, pow
from typing import List
from enum import Enum
import streamlit as st

st.set_page_config(page_title="MiV P1", layout="wide")

# Helper functions

def treat_2026_dataset(filepath: str, total_bubble_size = 160):
    plot_df = pd.read_csv(filepath)
    plot_df['area'] = plot_df['Radius(px)'].apply(lambda r: pi * pow(r, 2))
    plot_df['Births in 2026 (M)'] = plot_df['Births in 2026 (thousands)'] / 1000

    plot_df['og_chart_size'] = distribute_sizes(plot_df["area"], total_bubble_size)
    plot_df['new_chart_size'] = distribute_sizes(plot_df["Births in 2026 (M)"], total_bubble_size)

    return plot_df

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

# Charts

#   Graph 1: Original bubble plot with correct proportions
def bubble_plot(plot_df: pd.DataFrame):
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

    return bubble_fig

#   Graph 2: Source data represented in different formats

class GraphType(Enum):
    BAR = "Bar"
    RADAR = "Radar"

#       Graph 2.1: Bar plot with source data
def bar_plot(plot_df: pd.DataFrame):
    bar_fig = px.bar(plot_df, x='Continent', y='Births in 2026 (M)')
    bar_fig.update_traces(hovertemplate="Births in 2026 (M): %{y}")

    return bar_fig

#       Graph 2.2: Radar plot with source data
def radar_plot(plot_df: pd.DataFrame):
    radar_fig = px.line_polar(plot_df, r="Births in 2026 (M)", theta="Continent", line_close=True)
    radar_fig.update_layout(
        polar=dict(
            bgcolor="#0E1117",
            radialaxis=dict(
                tickfont=dict(color="white")
            )
        )
    )
    radar_fig.update_traces(hovertemplate="Births in 2026 (M): %{r}")

    return radar_fig

if __name__ == "__main__":
    plot_df = treat_2026_dataset("data/global_births_full_data.csv")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(bubble_plot(plot_df))
    with right:
        option = st.selectbox("", (GraphType.BAR.value, GraphType.RADAR.value))
        
        match(option):
            case GraphType.BAR.value:
                fig = bar_plot(plot_df)
            case GraphType.RADAR.value:
                fig = radar_plot(plot_df)
            case _:
                fig = None

        st.plotly_chart(fig)