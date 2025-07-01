import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

CLEANED_DATA_FOLDER = "cleaned_data"
CSV_NAME_PITCHERS = "American_League_Pitcher_Review"
CSV_NAME_PLAYERS = "American_League_Player_Review"
PITCHING = "Pitching (Pitchers)"
HITTING = "Hitting (Players)"
DATASET_OPTIONS = [PITCHING, HITTING]
DATASET_NAME_TO_FILE_MAP = {PITCHING: CSV_NAME_PITCHERS, HITTING: CSV_NAME_PLAYERS}

# As I use both datasets here (Players hitting and Pitchers pitching) we need a selector to switch between them
st.sidebar.header("Dataset Selection")
dataset_choice = st.sidebar.radio(
    "Choose which dataset to explore:",
    options=DATASET_OPTIONS
)


# Using function here to cache the data. It will work much faster on Render.
@st.cache_data
def load_data(file_name):
    return pd.read_csv(f"{os.getcwd()}/{CLEANED_DATA_FOLDER}/{file_name}_cleaned.csv")


df = load_data(DATASET_NAME_TO_FILE_MAP[dataset_choice])

st.title(f"American League {dataset_choice} Review Dashboard")
st.write(
    f"""
    You can explore historical {dataset_choice} performance with interactive visualizations.
    
    Please, select statistics, years and/or players from filters to the left to filter the data below.
    """
)

# Sidebar filters section
years = sorted(df["Year"].unique())
stats = sorted(df["Statistic Name"].unique())

st.sidebar.header("Filters")
selected_years = st.sidebar.multiselect("Select Years", options=years, default=years)
selected_stats = st.sidebar.multiselect("Select Statistics", options=stats, default=["Strikeouts"])

filtered_df_base = df[df["Year"].isin(selected_years) & df["Statistic Name"].isin(selected_stats)]
# Players' list will change according to selected year and statistics' filters
available_players = sorted(filtered_df_base["Name(s)"].unique())

selected_players = st.sidebar.multiselect("Select Players (optional)", options=available_players,
                                          help="Players available based on current year/stat filters.")
# Player filter works only if any player is selected
if selected_players:
    filtered_df = filtered_df_base[filtered_df_base["Name(s)"].isin(selected_players)]
else:
    filtered_df = filtered_df_base

# Data preview section
st.subheader("Filtered Data")
if filtered_df.empty:
    st.warning("No data matches the selected filters. Please adjust your selections on the sidebar to the left.")
else:
    st.dataframe(filtered_df)

    st.subheader("Average Statistic Value by Statistic Name")
    avg_per_stat = filtered_df.groupby("Statistic Name")["Statistic Value"].mean().sort_values(ascending=False)
    fig_avg_stat, ax_avg_stat = plt.subplots(figsize=(15, 8))
    avg_per_stat.plot(kind="bar", ax=ax_avg_stat)
    ax_avg_stat.set_ylabel("Average Statistic Value")
    st.pyplot(fig_avg_stat)

    # Works only if single statistic name is selected
    if len(selected_stats) == 1:
        stat_df = filtered_df[filtered_df["Statistic Name"] == selected_stats[0]]
        if not stat_df.empty:
            st.subheader(f"Average {selected_stats[0]} Over Time")
            stat_by_year = stat_df.groupby("Year")["Statistic Value"].mean()
            fig_avg_stat_over_time, ax_avg_stat_over_time = plt.subplots(figsize=(15, 8))
            stat_by_year.plot(kind="line", marker="o", ax=ax_avg_stat_over_time)
            ax_avg_stat_over_time.set_xlabel("Year")
            ax_avg_stat_over_time.set_ylabel(f"Average {selected_stats[0]}")
            st.pyplot(fig_avg_stat_over_time)

        st.write(
            """
            An interesting observation about impact of Covid-19 times:
            
            Try to filter (Select Statistics filter) by one of Strikeouts, Games, Saves, Wins.
            You will see a huge drop on a line chart on season 2020.
            """
        )

    st.subheader(f"Top {dataset_choice} by Frequency")
    top_players = filtered_df["Name(s)"].value_counts().head(10)
    fig_top_players, ax_top_players = plt.subplots(figsize=(15, 8))
    top_players.plot(kind="bar", ax=ax_top_players)
    ax_top_players.set_ylabel("Number of Records")
    st.pyplot(fig_top_players)

st.write("Data source: [American League Pitcher Review](https://www.baseball-almanac.com/yearmenu.shtml)")
