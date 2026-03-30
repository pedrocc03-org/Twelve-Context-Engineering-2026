import pandas as pd
import numpy as np
import plotly.graph_objects as go

from pages.physical.config import ATTRIBUTES


def radar_chart(player_row: pd.Series, position_df: pd.DataFrame) -> go.Figure:
    """Radar chart using z-scores computed within position group."""
    z_values = []
    for a in ATTRIBUTES:
        mean = position_df[a].mean()
        std = position_df[a].std()
        z = (player_row[a] - mean) / std if std > 0 else 0
        z_values.append(z)

    labels = ATTRIBUTES + [ATTRIBUTES[0]]
    values = z_values + [z_values[0]]

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
                range=[-3, 3],
                tickvals=[-2, -1, 0, 1, 2],
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
    """Distribution chart using z-scores computed within the filtered group."""
    mean = df[attribute].mean()
    std = df[attribute].std()
    if std > 0:
        z_all = (df[attribute] - mean) / std
        z_player = (player_row[attribute] - mean) / std
    else:
        z_all = df[attribute] * 0
        z_player = 0

    fig = go.Figure(go.Histogram(
        x=z_all,
        nbinsx=20,
        marker_color="rgba(100, 150, 210, 0.5)",
        marker_line=dict(color="rgba(100, 150, 210, 0.85)", width=0.5),
    ))
    fig.add_vline(
        x=z_player,
        line_width=2.5,
        line_color="#009940",
        annotation_text=f"  {z_player:+.1f}",
        annotation_position="top right",
        annotation_font=dict(color="#009940", size=13, family="monospace"),
    )
    fig.update_layout(
        title=dict(text=attribute, font=dict(size=14, color="#333"), x=0),
        xaxis=dict(range=[-4, 4], title="Z-score", gridcolor="rgba(150,150,150,0.15)"),
        yaxis=dict(title="Players", gridcolor="rgba(150,150,150,0.15)"),
        showlegend=False,
        margin=dict(t=40, b=36, l=44, r=16),
        height=230,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _hex_to_rgba(hex_color: str, opacity: float = 1.0) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{opacity})"


DARK_GREEN = "#002c1c"
MEDIUM_GREEN = "#003821"
BRIGHT_GREEN = "#00A938"
WHITE = "#ffffff"


def scout_overview_chart(
    position_df: pd.DataFrame,
    player_row: pd.Series,
    player_name: str,
) -> go.Figure:
    """
    Scout-style strip chart showing all 4 composite attribute scores
    (Speed, Acceleration, Agility, Endurance) on a z-score axis.
    """
    attrs = ATTRIBUTES[::-1]  # bottom-to-top
    n_players = len(position_df)

    player_mask = position_df["Player"] == player_row["Player"]
    if not player_mask.any():
        return go.Figure()
    player_idx = position_df.index.get_loc(player_mask.idxmax())

    fig = go.Figure()
    show_group_legend = True
    show_player_legend = True

    for i, attr in enumerate(attrs):
        values = position_df[attr]
        mean = values.mean()
        std = values.std()
        if std == 0 or np.isnan(std):
            z = np.zeros(n_players)
        else:
            z = (values - mean) / std

        ranks = values.rank(ascending=False).fillna(0).astype(int)

        # Group dots
        fig.add_trace(go.Scatter(
            x=z.tolist(),
            y=(np.ones(n_players) * i).tolist(),
            mode="markers",
            marker=dict(
                color=_hex_to_rgba(DARK_GREEN, 0.2),
                size=10,
                line_width=1.5,
                line_color=_hex_to_rgba(BRIGHT_GREEN),
            ),
            hovertemplate="%{text}<br>Rank: %{customdata}/" + str(n_players) + "<extra></extra>",
            text=position_df["Player"].tolist(),
            customdata=ranks.tolist(),
            showlegend=show_group_legend,
            name="Other players  ",
        ))
        show_group_legend = False

        # Selected player
        p_z = z.iloc[player_idx]
        p_rank = ranks.iloc[player_idx]
        p_score = values.iloc[player_idx]

        fig.add_trace(go.Scatter(
            x=[p_z],
            y=[i],
            mode="markers",
            marker=dict(
                color=_hex_to_rgba(WHITE, 0.5),
                size=10,
                symbol="square",
                line_width=1.5,
                line_color=_hex_to_rgba(WHITE),
            ),
            hovertemplate="%{text}<br>Rank: %{customdata}/" + str(n_players) + "<extra></extra>",
            text=[player_name],
            customdata=[p_rank],
            name=player_name,
            showlegend=show_player_legend,
        ))
        show_player_legend = False

        # Label
        fig.add_annotation(
            x=0,
            y=i + 0.4,
            text=f"<span>{attr}: {p_score:.1f}</span>",
            showarrow=False,
            font=dict(color=WHITE, family="Gilroy-Light", size=12),
        )

    fig.update_layout(
        paper_bgcolor=_hex_to_rgba(DARK_GREEN),
        plot_bgcolor=_hex_to_rgba(DARK_GREEN),
        height=500,
        margin=dict(l=60, r=60, b=70, t=75, pad=16),
        title=dict(
            text=(
                f"<span style='font-size:15px'>Evaluation of {player_name}</span><br>"
                f"<span style='font-size:11px'>Compared to {n_players} {player_row['Position Group']} players</span>"
            ),
            font=dict(family="Gilroy-Medium", color=WHITE, size=12),
            x=0.05, xanchor="left", y=0.93, yanchor="top",
        ),
        xaxis=dict(
            range=[-4, 4],
            fixedrange=True,
            tickmode="array",
            tickvals=[-3, 0, 3],
            ticktext=["Worse", "Average", "Better"],
            tickfont=dict(color=_hex_to_rgba(WHITE, 0.5), family="Gilroy-Light", size=12),
        ),
        yaxis=dict(
            showticklabels=False,
            fixedrange=True,
            gridcolor=_hex_to_rgba(MEDIUM_GREEN),
            zerolinecolor=_hex_to_rgba(MEDIUM_GREEN),
        ),
        legend=dict(
            orientation="h",
            font=dict(color=WHITE, family="Gilroy-Light", size=11),
            itemclick=False, itemdoubleclick=False,
            x=0.5, xanchor="center", y=-0.2, yanchor="bottom",
            valign="middle",
        ),
    )

    fig.add_shape(
        type="line",
        x0=0, y0=0, x1=0, y1=len(attrs),
        line=dict(color="gray", width=1, dash="dot"),
    )

    return fig


def _config_metric_to_column(metric_name: str) -> tuple[str, bool]:
    """Convert a config metric name to (raw_column_name, is_inverted)."""
    inverted = "(INV)" in metric_name
    col = metric_name.replace(" (INV)", "").replace("\u00b0", "")
    return col, inverted


def scout_strip_chart(
    raw_position_df: pd.DataFrame,
    player_name: str,
    attribute: str,
    attribute_info: dict,
) -> go.Figure:
    """
    Football-scout style strip plot for a single attribute's raw metrics.
    One row per underlying metric, all position-group peers as green dots,
    selected player as a white square. X-axis is z-score (-4 to +4).
    """
    metrics_config = attribute_info["metrics"]  # {metric_name: weight}
    metric_items = list(metrics_config.items())
    metric_items_reversed = metric_items[::-1]  # bottom-to-top

    fig = go.Figure()
    n_players = len(raw_position_df)

    player_mask = raw_position_df["Player"] == player_name
    if not player_mask.any():
        return fig
    player_idx = raw_position_df.index.get_loc(player_mask.idxmax())

    show_group_legend = True
    show_player_legend = True

    for i, (metric_name, weight) in enumerate(metric_items_reversed):
        col, inverted = _config_metric_to_column(metric_name)

        if col not in raw_position_df.columns:
            continue

        values = pd.to_numeric(raw_position_df[col], errors="coerce")
        mean = values.mean()
        std = values.std()
        if std == 0 or np.isnan(std):
            z = np.zeros(n_players)
        else:
            z = (values - mean) / std

        # For inverted metrics, flip the z-score (lower raw = better)
        if inverted:
            z = -z

        ranks = values.rank(ascending=not inverted).fillna(0).astype(int)

        # --- group dots ---
        fig.add_trace(go.Scatter(
            x=z.tolist(),
            y=(np.ones(n_players) * i).tolist(),
            mode="markers",
            marker=dict(
                color=_hex_to_rgba(DARK_GREEN, 0.2),
                size=10,
                line_width=1.5,
                line_color=_hex_to_rgba(BRIGHT_GREEN),
            ),
            hovertemplate="%{text}<br>Rank: %{customdata}/" + str(n_players) + "<extra></extra>",
            text=raw_position_df["Player"].tolist(),
            customdata=ranks.tolist(),
            showlegend=show_group_legend,
            name="Other players  ",
        ))
        show_group_legend = False

        # --- selected player ---
        p_z = z.iloc[player_idx]
        p_rank = ranks.iloc[player_idx]
        p_raw = values.iloc[player_idx]

        fig.add_trace(go.Scatter(
            x=[p_z],
            y=[i],
            mode="markers",
            marker=dict(
                color=_hex_to_rgba(WHITE, 0.5),
                size=10,
                symbol="square",
                line_width=1.5,
                line_color=_hex_to_rgba(WHITE),
            ),
            hovertemplate="%{text}<br>Rank: %{customdata}/" + str(n_players) + "<extra></extra>",
            text=[player_name],
            customdata=[p_rank],
            name=player_name,
            showlegend=show_player_legend,
        ))
        show_player_legend = False

        # Label: metric name + raw value + weight
        display_name = metric_name.replace(" (INV)", "")
        fig.add_annotation(
            x=0,
            y=i + 0.4,
            text=f"<span>{display_name}: {p_raw:.2f}  (wt {weight*100:.0f}%)</span>",
            showarrow=False,
            font=dict(color=WHITE, family="Gilroy-Light", size=12),
        )

    n_metrics = len(metric_items)

    fig.update_layout(
        paper_bgcolor=_hex_to_rgba(DARK_GREEN),
        plot_bgcolor=_hex_to_rgba(DARK_GREEN),
        height=max(300, 120 * n_metrics),
        margin=dict(l=60, r=60, b=70, t=75, pad=16),
        title=dict(
            text=(
                f"<span style='font-size:15px'>{attribute_info['icon']} {attribute}</span><br>"
                f"<span style='font-size:11px'>{player_name} vs {n_players} position-group peers</span>"
            ),
            font=dict(family="Gilroy-Medium", color=WHITE, size=12),
            x=0.05, xanchor="left", y=0.93, yanchor="top",
        ),
        xaxis=dict(
            range=[-4, 4],
            fixedrange=True,
            tickmode="array",
            tickvals=[-3, 0, 3],
            ticktext=["Worse", "Average", "Better"],
            tickfont=dict(color=_hex_to_rgba(WHITE, 0.5), family="Gilroy-Light", size=12),
        ),
        yaxis=dict(
            showticklabels=False,
            fixedrange=True,
            gridcolor=_hex_to_rgba(MEDIUM_GREEN),
            zerolinecolor=_hex_to_rgba(MEDIUM_GREEN),
        ),
        legend=dict(
            orientation="h",
            font=dict(color=WHITE, family="Gilroy-Light", size=11),
            itemclick=False, itemdoubleclick=False,
            x=0.5, xanchor="center", y=-0.2, yanchor="bottom",
            valign="middle",
        ),
    )

    fig.add_shape(
        type="line",
        x0=0, y0=0, x1=0, y1=n_metrics,
        line=dict(color="gray", width=1, dash="dot"),
    )

    return fig
