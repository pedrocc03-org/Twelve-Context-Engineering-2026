import streamlit as st

from utils.page_components import add_common_page_elements
from pages.physical.config import ATTRIBUTES, ATTRIBUTE_INFO
from pages.physical.data import load_data, load_raw_data, filter_players, get_position_group_df
from pages.physical.charts import radar_chart, distribution_chart, scout_overview_chart, scout_strip_chart
from pages.physical.components import player_header_html, score_cards_html, glossary_html
from classes.physical_description import PhysicalDescription

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
position_df = filtered.reset_index(drop=True)

# Load raw SkillCorner data and apply the same filters
raw_df = load_raw_data()
raw_position_df = filter_players(raw_df, competition, position).reset_index(drop=True)

_comp_label = competition if competition != "All Competitions" else "all competitions"
_pos_label = position if position != "All Positions" else "all positions"

st.divider()
st.markdown(player_header_html(player_row), unsafe_allow_html=True)

# Tabs
tab_report, tab_overview, tab_distributions, tab_scout, tab_rankings = st.tabs([
    "Physical Report", "Overview", "Distributions", "Scout View", "Position Group Rankings"
])

with tab_report:
    report_key = (selected_name, competition, position, "physical_report")
    col_gen, col_regen = st.columns([4, 1])
    with col_regen:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        regenerate = st.button("🔄 Regenerate", use_container_width=True)

    if regenerate and report_key in st.session_state:
        del st.session_state[report_key]

    if report_key not in st.session_state:
        description = PhysicalDescription(player_row, position_df, raw_position_df)
        with col_gen:
            report_text = st.write_stream(description.stream_gpt(stream=True))
        st.session_state[report_key] = report_text
    else:
        st.markdown(st.session_state[report_key])

with tab_overview:
    col_radar, col_scores = st.columns([3, 2])
    with col_radar:
        st.plotly_chart(radar_chart(player_row, position_df), use_container_width=True)
    with col_scores:
        st.markdown(
            "<div style='font-size:15px;font-weight:600;color:#111;margin-bottom:4px;'>Attribute Scores</div>"
            "<div style='font-size:12px;color:#666;margin-bottom:16px;'>Z-score vs position group peers</div>",
            unsafe_allow_html=True,
        )
        st.markdown(score_cards_html(player_row, position_df), unsafe_allow_html=True)

with tab_distributions:
    st.markdown(
        f"<div style='font-size:13px;color:#555;margin-bottom:16px;'>"
        f"<strong style='color:#111;'>{_pos_label}</strong> players "
        f"({_comp_label}) &nbsp;&mdash;&nbsp; "
        f"<span style='color:#009940;'>green line</span> = "
        f"<strong style='color:#111;'>{player_row['Short Name']}</strong></div>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    for i, attr in enumerate(ATTRIBUTES):
        with (col1 if i % 2 == 0 else col2):
            st.plotly_chart(distribution_chart(position_df, player_row, attr), use_container_width=True)

with tab_scout:
    st.plotly_chart(
        scout_overview_chart(position_df, player_row, selected_name),
        use_container_width=True,
    )
    st.divider()
    st.markdown(
        f"<div style='font-size:13px;color:#ccc;margin-bottom:16px;'>"
        f"Raw metric breakdowns for <strong style='color:#fff;'>{player_row['Short Name']}</strong> "
        f"vs <strong style='color:#fff;'>{len(raw_position_df)}</strong> filtered peers "
        f"&nbsp;&mdash;&nbsp; <span style='color:#fff;'>white square</span> = selected player"
        f"</div>",
        unsafe_allow_html=True,
    )
    for attr in ATTRIBUTES:
        st.plotly_chart(
            scout_strip_chart(raw_position_df, selected_name, attr, ATTRIBUTE_INFO[attr]),
            use_container_width=True,
        )

with tab_rankings:
    rank_df = (
        position_df[["Player", "Team", "Competition"] + ATTRIBUTES]
        .copy()
        .sort_values("Speed", ascending=False)
        .reset_index(drop=True)
    )
    st.markdown(
        f"<div style='font-size:13px;color:#555;margin-bottom:16px;'>"
        f"<strong style='color:#111;'>{_pos_label}</strong> players "
        f"({_comp_label}) &nbsp;&mdash;&nbsp; sorted by Speed</div>",
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
