import pandas as pd

from pages.physical.config import ATTRIBUTES, ATTRIBUTE_INFO


def z_score_color(z: float) -> str:
    if z >= 0.5:
        return "#009940"
    elif z >= -0.5:
        return "#f4a62a"
    return "#e05c5c"


def player_header_html(player_row: pd.Series, position_df: pd.DataFrame) -> str:
    # Compute best attribute (highest z-score)
    best_attr, best_z = None, -999.0
    for attr in ATTRIBUTES:
        mean = position_df[attr].mean()
        std  = position_df[attr].std()
        z    = (player_row[attr] - mean) / std if std > 0 else 0.0
        if z > best_z:
            best_z, best_attr = z, attr

    best_color = z_score_color(best_z)
    best_icon  = ATTRIBUTE_INFO[best_attr]["icon"] if best_attr else ""
    best_badge = (
        f'<div style="text-align:right;">'
        f'<div style="font-size:10px;font-weight:700;color:#888;letter-spacing:1.5px;'
        f'text-transform:uppercase;margin-bottom:4px;">Top Attribute</div>'
        f'<div style="display:inline-flex;align-items:center;gap:6px;'
        f'background:rgba(255,255,255,0.06);border:1px solid {best_color}44;'
        f'border-radius:6px;padding:6px 14px;">'
        f'<span style="font-size:18px;">{best_icon}</span>'
        f'<span style="font-size:14px;font-weight:700;color:{best_color};">{best_attr}</span>'
        f'<span style="font-size:15px;font-weight:700;color:{best_color};">{best_z:+.1f}</span>'
        f'</div></div>'
    ) if best_attr else ""

    return (
        '<div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 60%,#0f3460 100%);'
        'border:1px solid rgba(0,180,120,0.3);border-radius:12px;padding:22px 28px;margin-bottom:8px;'
        'display:flex;justify-content:space-between;align-items:center;">'
        '<div>'
        '<div style="font-size:10px;font-weight:700;color:#009940;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:8px;">Player Profile</div>'
        '<div style="font-size:28px;font-weight:800;color:#ffffff;letter-spacing:0.3px;margin-bottom:8px;">'
        + player_row["Player"] +
        '</div>'
        '<div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;">'
        '<span style="color:#00b478;font-size:14px;font-weight:600;">' + player_row["Team"] + "</span>"
        '<span style="color:#555;font-size:14px;">·</span>'
        '<span style="color:#aaa;font-size:13px;">' + player_row["Position Group"] + "</span>"
        '<span style="color:#555;font-size:14px;">·</span>'
        '<span style="color:#888;font-size:13px;font-style:italic;">' + player_row["Competition"] + "</span>"
        "</div>"
        "</div>"
        + best_badge +
        "</div>"
    )


def score_cards_html(player_row: pd.Series, position_df: pd.DataFrame) -> str:
    cards = []
    for attr in ATTRIBUTES:
        mean = position_df[attr].mean()
        std = position_df[attr].std()
        z = (player_row[attr] - mean) / std if std > 0 else 0.0
        color = z_score_color(z)
        # Map z-score to a 0-100 bar width (clamp between -3 and +3)
        bar_pct = int(max(0, min(100, (z + 3) / 6 * 100)))
        cards.append(
            f'<div style="background:#ffffff;border:1px solid #ddd;border-left:4px solid {color};'
            f'border-radius:8px;padding:14px 16px;margin-bottom:10px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
            f'<span style="font-size:14px;color:#222;font-weight:600;">'
            f'{ATTRIBUTE_INFO[attr]["icon"]} {attr}</span>'
            f'<div><span style="font-size:22px;font-weight:700;color:{color};">{z:+.1f}</span></div></div>'
            f'<div style="background:#e8e8e8;border-radius:4px;height:6px;width:100%;overflow:hidden;">'
            f'<div style="background:{color};height:100%;width:{bar_pct}%;border-radius:4px;"></div></div>'
            f'</div>'
        )
    return "".join(cards)


def glossary_html() -> str:
    total_metrics = sum(len(info["metrics"]) for info in ATTRIBUTE_INFO.values())

    inv_badge = (
        '<span style="background:#3d2e0a;color:#f4a62a;font-size:10px;'
        'padding:2px 7px;border-radius:3px;margin-left:8px;font-weight:600;">INV</span>'
    )

    blocks = []
    for attr, info in ATTRIBUTE_INFO.items():
        rows = []
        for metric, weight in info["metrics"].items():
            is_inv = "(INV)" in metric
            label  = metric.replace(" (INV)", "")
            rows.append(
                "<tr>"
                '<td style="padding:9px 14px;color:#e8e8e8;font-size:13px;border-bottom:1px solid #2a2a2a;">'
                + label + (inv_badge if is_inv else "") + "</td>"
                '<td style="padding:9px 14px;text-align:right;font-weight:700;color:#00b478;'
                'font-size:14px;border-bottom:1px solid #2a2a2a;">'
                + f"{weight*100:.0f}%" + "</td>"
                "</tr>"
            )

        blocks.append(
            '<div style="background:#1c1c1c;border:1px solid #333;border-radius:10px;'
            'padding:20px 22px;margin-bottom:14px;">'
            '<div style="font-size:17px;font-weight:700;color:#ffffff;margin-bottom:8px;">'
            + info["icon"] + "&nbsp;&nbsp;" + attr + "</div>"
            '<div style="font-size:13px;color:#b0b0b0;line-height:1.7;margin-bottom:16px;">'
            + info["definition"] + "</div>"
            '<table style="width:100%;border-collapse:collapse;background:#141414;">'
            '<thead><tr style="background:#0d2b1f;">'
            '<th style="padding:8px 14px;text-align:left;color:#00b478;font-size:11px;'
            'text-transform:uppercase;letter-spacing:1px;">Metric</th>'
            '<th style="padding:8px 14px;text-align:right;color:#00b478;font-size:11px;'
            'text-transform:uppercase;letter-spacing:1px;">Weight</th>'
            "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
        )

    intro = (
        '<div style="background:#0d2b1f;border:1px solid #00b478;border-left:4px solid #00b478;'
        'border-radius:8px;padding:16px 20px;margin-bottom:22px;font-size:13px;color:#c8c8c8;line-height:1.8;">'
        "Players are rated on <strong style='color:#fff;'>4 physical attributes</strong> built from "
        "<strong style='color:#fff;'>" + str(total_metrics) + " SkillCorner</strong> tracking metrics. "
        "Each metric is converted to a <strong style='color:#fff;'>within-position-group percentile</strong> "
        "(0&nbsp;=&nbsp;worst, 100&nbsp;=&nbsp;best) before being weighted into the attribute score.<br><br>"
        "Metrics tagged "
        '<span style="background:#3d2e0a;color:#f4a62a;font-size:11px;padding:2px 8px;'
        'border-radius:3px;font-weight:600;">INV</span>'
        " are <strong style='color:#fff;'>inverted</strong> — lower raw value = better performance."
        "</div>"
    )

    return (
        '<div style="background:#111;border:1px solid #2a2a2a;border-radius:12px;padding:24px 28px;margin:8px 0 16px 0;">'
        '<div style="font-size:19px;font-weight:700;color:#ffffff;margin-bottom:16px;">'
        "Physical Analyst &mdash; Glossary</div>"
        + intro + "".join(blocks) + "</div>"
    )
