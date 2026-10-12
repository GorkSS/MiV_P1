import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
from plotly.subplots import make_subplots
from math import pi, sqrt, pow, ceil, floor
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

def treat_evo_dataset(filepath: str):
    evo_df = pd.read_csv(filepath)
    return evo_df.drop(["2024", "2025"], axis=1)

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

def proportion_between_years(evo_df, reference_year, target_year):
    return -((1 - (evo_df[target_year] / evo_df[reference_year])) * 100)

def max_min_proportions(evo_df):
    minimum = 0
    maximum = 0
    temp_series = None
    for col in evo_df.columns:
        if col != "Continent" and col != "2026":
            temp_series = proportion_between_years(evo_df, "2026", col)
            if temp_series.min() < minimum:
                minimum = temp_series.min()
            if temp_series.max() > maximum:
                maximum = temp_series.max()

    return [floor(minimum), ceil(maximum)]

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
    bubble_fig.update_layout(hovermode="x unified",
                             title={"text": "Original plot proportions vs correct ones", "x": 0.25})
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
    bar_fig = px.bar(plot_df, x='Continent', y='Births in 2026 (M)', height=10)
    bar_fig.update_traces(hovertemplate="Births in 2026 (M): %{y}")

    return bar_fig

#       Graph 2.2: Radar plot with source data
def radar_plot(plot_df: pd.DataFrame, r="Births in 2026 (M)", theta="Continent", hover="2026"):
    radar_fig = px.line_polar(plot_df, r=r, theta=theta, line_close=True)
    radar_fig.update_layout(
        polar=dict(
            bgcolor="#0E1117",
            radialaxis=dict(
                tickfont=dict(color="white")
            )
        )
    )
    radar_fig.update_traces(hovertemplate="Births in " + hover + ": %{r}M")

    return radar_fig

#   Graph 3: 3D
def threed_plot(evo_df: pd.DataFrame, year: str):
    new_df = evo_df.copy()
    new_df["proportion"] = round(proportion_between_years(new_df, "2026", year), 2)
    for col in set(("2026", year)):
        new_df[col] = new_df[col] / 1000
    fig = px.bar(new_df,
                 x='Continent',
                 y=year,
                 color="proportion",
                 range_color=[-45, 20],
                 custom_data=["proportion"])
    fig.update_traces(hovertemplate="Births in " + year + ": %{y} M<br>Increase of %{customdata[0]}% from 2026")

    fig.update_layout(yaxis_title=f"Births in {year} (M)", 
                      title={"text": f"Projected Total Births in {year} and Increase From 2026", "x": 0.1},
                      coloraxis=dict(
                      colorscale=[
                          [0, "rgb(94 111 251)"],
                          [0.707, "rgb(237 239 240)"],
                          [1, "rgb(251 234 94)"]
                      ],
                      colorbar_title="Births increase (%)",
                    ))

    return fig

if __name__ == "__main__":
    plot_df = treat_2026_dataset("data/global_births_full_data.csv", total_bubble_size=90)
    evo_df = treat_evo_dataset("data/global_births_evolution.csv")

    st.header("Projected Births Worldwide in 2026", text_alignment="center")
    up_zone = st.container(border=True)

    _, r0right = up_zone.columns(2)
    with r0right:
        _, _, _, _, btn = r0right.columns(5)
        with btn:
            option_2026_plot = st.selectbox("", (GraphType.BAR.value, GraphType.RADAR.value))

    r1left, r1right = up_zone.columns(2)
    with r1left:
        st.plotly_chart(bubble_plot(plot_df), height=350)
    with r1right:
        match(option_2026_plot):
            case GraphType.BAR.value:
                fig = bar_plot(plot_df)
            case GraphType.RADAR.value:
                fig = radar_plot(plot_df)
            case _:
                fig = None

        fig.update_layout(title={"text": "Births in 2026 by continent", "x": 0.35})
        st.plotly_chart(fig, height=350)



    st.header("UN Data for Projected Births Worldwide 2026-2100", text_alignment="center")
    bottom_zone = st.container(border=True)

    years = evo_df.columns.to_list()
    years.remove("Continent")
    option_evo_plot = bottom_zone.selectbox("", years)

    r2left, r2right = bottom_zone.columns(2)
    with r2left:
        st.plotly_chart(threed_plot(evo_df, option_evo_plot))
    with r2right:
        country_btn, left_btn = st.columns(2)
        with country_btn:
            option_country = st.selectbox("Continent", plot_df["Continent"])
        with left_btn:
            value = st.number_input("Nº of countries", min_value=1, max_value=15, value=5, step=1)

        countries_df = pd.read_csv("data/global_births_countries.csv")
        countries_df = countries_df[countries_df["Continent"] == option_country]
        
        countries_df.sort_values("2026", ascending=False, inplace=True)
        top_countries_df = countries_df.iloc[:value][["Region", "Continent", "2026"]]
        top_countries_df.loc[len(top_countries_df)] = ["Other", option_country, countries_df.iloc[value:]["2026"].sum()]
        donut = px.pie(top_countries_df, values="2026", names="Region", hole=0.3)

        countries_df.sort_values(option_evo_plot, ascending=False, inplace=True)
        top_countries_df = countries_df.iloc[:value][["Region", "Continent", option_evo_plot]]
        top_countries_df.loc[len(top_countries_df)] = ["Other", option_country, countries_df.iloc[value:][option_evo_plot].sum()]

        pie_fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'pie'}, {'type': 'pie'}]])
        pie_fig.add_trace(donut.data[0], row=1, col=1)
        pie_fig.add_trace(px.pie(top_countries_df, values=option_evo_plot, names="Region", hole=0.3).data[0],
                          row=1, col=2)

        pie_fig.add_annotation(
            x=0.17,
            y=0,
            text="2026",
            showarrow=False,
            xref="paper",
            yref="paper"
        )

        pie_fig.add_annotation(
            x=0.83,
            y=0,
            text=option_evo_plot,
            showarrow=False,
            xref="paper",
            yref="paper"
        )

        pie_fig.update_layout(title={"text": f"% of Births by Country in {option_country}", "x": 0.25})

        st.plotly_chart(pie_fig, height="content")