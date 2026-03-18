import pandas as pd
import streamlit as st

from pages.physical.config import DATA_PATH, ATTRIBUTES


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    return df.dropna(subset=ATTRIBUTES)


def filter_players(df: pd.DataFrame, competition: str, position: str) -> pd.DataFrame:
    filtered = df.copy()
    if competition != "All Competitions":
        filtered = filtered[filtered["Competition"] == competition]
    if position != "All Positions":
        filtered = filtered[filtered["Position Group"] == position]
    return filtered


def get_position_group_df(df: pd.DataFrame, player_row: pd.Series) -> pd.DataFrame:
    return df[df["Position Group"] == player_row["Position Group"]]
