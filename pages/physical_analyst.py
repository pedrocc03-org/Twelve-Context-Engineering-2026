import streamlit as st

from classes.chat import PhysicalChat
from utils.page_components import add_common_page_elements
from pages.physical.config import ATTRIBUTES, ATTRIBUTE_INFO
from pages.physical.data import load_data, load_raw_data, filter_players, get_position_group_df
from pages.physical.charts import radar_chart, scout_overview_chart, scout_strip_chart
from pages.physical.components import player_header_html, score_cards_html, glossary_html
from classes.physical_description import PhysicalDescription
from utils.utils import create_chat

add_common_page_elements()

# Wider layout override for this page
st.markdown(
    """
    <style>
    section[tabindex="0"] > div[data-testid="stAppViewBlockContainer"] {
        max-width: 1600px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.divider()

df = load_data()

if "glossary_open" not in st.session_state:
    st.session_state.glossary_open = False

# ── Page header ────────────────────────────────────────────────────────────────
col_header, col_btn = st.columns([6, 1], vertical_alignment="center")

with col_header:
    st.markdown(
        """
        <div style="border-left:4px solid #009940;padding:10px 18px;">
          <div style="
            display:inline-block;
            font-size:10px;font-weight:700;color:#009940;
            letter-spacing:2.5px;text-transform:uppercase;
            background:#e8f7ee;border:1px solid #b3dfc3;
            border-radius:4px;padding:2px 8px;margin-bottom:8px;
          ">Physical Analysis &nbsp;·&nbsp; SkillCorner</div>
          <div style="font-size:30px;font-weight:800;color:#111;line-height:1.1;margin-bottom:4px;">
            Physical Analyst
          </div>
          <div style="font-size:13px;color:#888;">
            Speed &nbsp;&middot;&nbsp; Acceleration &nbsp;&middot;&nbsp;
            Agility &nbsp;&middot;&nbsp; Endurance
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_btn:
    label = "✕ Close" if st.session_state.glossary_open else "ℹ Glossary"
    if st.button(label, use_container_width=True):
        st.session_state.glossary_open = not st.session_state.glossary_open

if st.session_state.glossary_open:
    st.markdown(glossary_html(), unsafe_allow_html=True)

st.divider()

st.markdown(
    "<div style='font-size:11px;font-weight:700;color:#009940;"
    "letter-spacing:1.8px;text-transform:uppercase;margin-bottom:6px;'>"
    "View</div>",
    unsafe_allow_html=True,
)

selected_view = st.radio(
    "Physical Analyst View",
    ["Player Profile", "Chat"],
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

# ── Filters ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:11px;font-weight:700;color:#009940;"
    "letter-spacing:1.8px;text-transform:uppercase;margin-bottom:6px;'>"
    "Select Player</div>",
    unsafe_allow_html=True,
)

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

if selected_view == "Player Profile":
    st.divider()

    # ── Player identity card ───────────────────────────────────────────────────
    st.markdown(player_header_html(player_row, position_df), unsafe_allow_html=True)

    st.divider()

    tab_overview, tab_scout, tab_rankings = st.tabs([
        "Overview", "Scout View", "Position Group Rankings"
    ])

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

    st.divider()

    col_report_title, col_report_mode, col_regen = st.columns([2, 2, 2], vertical_alignment="center")
    with col_report_title:
        st.markdown(
            "<div style='font-size:11px;font-weight:700;color:#009940;"
            "letter-spacing:1.8px;text-transform:uppercase;margin-bottom:4px;'>"
            "AI Report</div>"
            "<div style='font-size:20px;font-weight:700;color:#111;'>Physical Summary</div>",
            unsafe_allow_html=True,
        )
    with col_report_mode:
        profile_report_mode = st.radio(
            "Profile Mode",
            ["Basic", "Detailed"],
            index=0,
            horizontal=True,
            label_visibility="collapsed",
            key="profile_report_mode",
        )
    with col_regen:
        profile_regenerate = st.button("🔄 Regenerate", key="profile_regenerate")

    profile_report_key = (
        selected_name,
        competition,
        position,
        "physical_profile_report",
        profile_report_mode,
    )

    if profile_regenerate and profile_report_key in st.session_state:
        del st.session_state[profile_report_key]

    profile_detailed = profile_report_mode == "Detailed"
    profile_description = PhysicalDescription(
        player_row,
        position_df,
        raw_position_df,
        detailed=profile_detailed,
    )

    if profile_report_key not in st.session_state:
        profile_report_text = st.write_stream(profile_description.stream_gpt(stream=True))
        st.session_state[profile_report_key] = profile_report_text
    else:
        st.markdown(st.session_state[profile_report_key])
else:
    st.divider()

    col_report_title, col_regen = st.columns([4, 2], vertical_alignment="center")
    with col_report_title:
        st.markdown(
            "<div style='font-size:11px;font-weight:700;color:#009940;"
            "letter-spacing:1.8px;text-transform:uppercase;margin-bottom:4px;'>"
            "AI Report</div>"
            "<div style='font-size:20px;font-weight:700;color:#111;'>Physical Chat</div>",
            unsafe_allow_html=True,
        )
    with col_regen:
        regenerate = st.button("🔄 Regenerate")

    if "physical_chat_nonce" not in st.session_state:
        st.session_state.physical_chat_nonce = 0

    if regenerate:
        st.session_state.physical_chat_nonce += 1

    to_hash = (
        selected_name,
        competition,
        position,
        st.session_state.physical_chat_nonce,
        "physical_analyst",
    )

    chat = create_chat(
        to_hash,
        PhysicalChat,
        player_row,
        position_df,
        raw_position_df,
        detailed=False,
    )

    if chat.state == "empty":
        chat.add_message(
            "Hello. Ask about speed, acceleration, agility, endurance, or any of the raw physical metrics."
        )
        chat.state = "default"

    chat.get_input()
    chat.display_messages()
    chat.save_state()
