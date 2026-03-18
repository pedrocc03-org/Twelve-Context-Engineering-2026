import streamlit as st

from utils.page_components import add_common_page_elements
from pages.physical.config import ATTRIBUTES
from pages.physical.data import load_data, filter_players, get_position_group_df
from pages.physical.charts import radar_chart, distribution_chart
from pages.physical.components import player_header_html, score_cards_html, glossary_html

add_common_page_elements()

st.divider()

df = load_data()

if "glossary_open" not in st.session_state:
    st.session_state.glossary_open = False

# Title + glossary toggle
col_title, col_btn = st.columns([5, 1])
with col_title:
    st.markdown(
        "<h2 style='margin-bottom:2px;'>Physical Analyst</h2>"
        "<p style='color:#888;margin-top:0;font-size:14px;'>"
        "Layer 1 &nbsp;&middot;&nbsp; Speed &nbsp;&middot;&nbsp; Acceleration"
        " &nbsp;&middot;&nbsp; Agility &nbsp;&middot;&nbsp; Endurance</p>",
        unsafe_allow_html=True,
    )
with col_btn:
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    label = "✕ Close" if st.session_state.glossary_open else "ℹ Glossary"
    if st.button(label, use_container_width=True):
        st.session_state.glossary_open = not st.session_state.glossary_open

if st.session_state.glossary_open:
    st.markdown(glossary_html(), unsafe_allow_html=True)
    st.divider()

# Filters
f1, f2, f3 = st.columns([2, 2, 3])
with f1:
    competitions = ["All Competitions"] + sorted(df["Competition"].unique().tolist())
    competition  = st.selectbox("Competition", competitions)
with f2:
    position_options = ["All Positions"] + sorted(df["Position Group"].unique().tolist())
    position         = st.selectbox("Position Group", position_options)

filtered = filter_players(df, competition, position)
if filtered.empty:
    st.warning("No players match the selected filters.")
    st.stop()

with f3:
    selected_name = st.selectbox("Player", sorted(filtered["Player"].unique().tolist()))

player_row  = filtered[filtered["Player"] == selected_name].iloc[0]
position_df = get_position_group_df(df, player_row)

st.divider()
st.markdown(player_header_html(player_row), unsafe_allow_html=True)

# Tabs
tab_overview, tab_distributions, tab_rankings = st.tabs([
    "Overview", "Distributions", "Position Group Rankings"
])

with tab_overview:
    col_radar, col_scores = st.columns([3, 2])
    with col_radar:
        st.plotly_chart(radar_chart(player_row), use_container_width=True)
    with col_scores:
        st.markdown(
            "<div style='font-size:15px;font-weight:600;color:#111;margin-bottom:4px;'>Attribute Scores</div>"
            "<div style='font-size:12px;color:#666;margin-bottom:16px;'>Percentile vs position group peers</div>",
            unsafe_allow_html=True,
        )
        st.markdown(score_cards_html(player_row), unsafe_allow_html=True)

with tab_distributions:
    st.markdown(
        f"<div style='font-size:13px;color:#555;margin-bottom:16px;'>"
        f"All <strong style='color:#111;'>{player_row['Position Group']}</strong> players "
        f"(all competitions) &nbsp;&mdash;&nbsp; "
        f"<span style='color:#009940;'>green line</span> = "
        f"<strong style='color:#111;'>{player_row['Short Name']}</strong></div>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    for i, attr in enumerate(ATTRIBUTES):
        with (col1 if i % 2 == 0 else col2):
            st.plotly_chart(distribution_chart(position_df, player_row, attr), use_container_width=True)

with tab_rankings:
    rank_df = (
        position_df[["Player", "Team", "Competition"] + ATTRIBUTES]
        .copy()
        .sort_values("Speed", ascending=False)
        .reset_index(drop=True)
    )
    st.markdown(
        f"<div style='font-size:13px;color:#555;margin-bottom:16px;'>"
        f"All <strong style='color:#111;'>{player_row['Position Group']}</strong> players "
        f"across all competitions &nbsp;&mdash;&nbsp; sorted by Speed</div>",
        unsafe_allow_html=True,
    )

    def highlight_player(row):
        style = "background-color:#e6f4ee;" if row["Player"] == player_row["Player"] else ""
        return [style] * len(row)

    styled = (
        rank_df.style
        .apply(highlight_player, axis=1)
        .format({attr: "{:.1f}" for attr in ATTRIBUTES})
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)
