import pandas as pd
import plotly.graph_objects as go

from pages.physical.config import ATTRIBUTES


def radar_chart(player_row: pd.Series) -> go.Figure:
    labels = ATTRIBUTES + [ATTRIBUTES[0]]
    values = [player_row[a] for a in ATTRIBUTES] + [player_row[ATTRIBUTES[0]]]

    fig = go.Figure(go.Scatterpolar(
        r=values,
        theta=labels,
        fill="toself",
        fillcolor="rgba(0, 180, 120, 0.18)",
        line=dict(color="#00b478", width=2.5),
        name=player_row["Short Name"],
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[25, 50, 75, 100],
                tickfont=dict(size=9),
                gridcolor="rgba(150,150,150,0.25)",
            ),
            angularaxis=dict(gridcolor="rgba(150,150,150,0.25)"),
        ),
        showlegend=False,
        margin=dict(t=30, b=30, l=50, r=50),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def distribution_chart(df: pd.DataFrame, player_row: pd.Series, attribute: str) -> go.Figure:
    player_score = player_row[attribute]

    fig = go.Figure(go.Histogram(
        x=df[attribute],
        nbinsx=20,
        marker_color="rgba(100, 150, 210, 0.5)",
        marker_line=dict(color="rgba(100, 150, 210, 0.85)", width=0.5),
    ))
    fig.add_vline(
        x=player_score,
        line_width=2.5,
        line_color="#009940",
        annotation_text=f"  {player_score:.0f}",
        annotation_position="top right",
        annotation_font=dict(color="#009940", size=13, family="monospace"),
    )
    fig.update_layout(
        title=dict(text=attribute, font=dict(size=14, color="#333"), x=0),
        xaxis=dict(range=[0, 100], title="Percentile score", gridcolor="rgba(150,150,150,0.15)"),
        yaxis=dict(title="Players", gridcolor="rgba(150,150,150,0.15)"),
        showlegend=False,
        margin=dict(t=40, b=36, l=44, r=16),
        height=230,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
