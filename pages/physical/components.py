import pandas as pd

from pages.physical.config import ATTRIBUTES, ATTRIBUTE_INFO


def score_color(score: float) -> str:
    if score >= 66:
        return "#009940"
    elif score >= 33:
        return "#f4a62a"
    return "#e05c5c"


def score_label(score: float) -> str:
    if score >= 80: return "Elite"
    if score >= 60: return "Good"
    if score >= 40: return "Average"
    if score >= 20: return "Below avg"
    return "Low"


def player_header_html(player_row: pd.Series) -> str:
    return (
        '<div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 60%,#0f3460 100%);'
        'border:1px solid rgba(0,180,120,0.3);border-radius:12px;padding:20px 28px;margin-bottom:8px;">'
        '<div style="font-size:26px;font-weight:700;color:#ffffff;letter-spacing:0.3px;">'
        + player_row["Player"] +
        '</div><div style="margin-top:6px;display:flex;gap:16px;flex-wrap:wrap;">'
        '<span style="color:#00b478;font-size:14px;font-weight:600;">' + player_row["Team"] + "</span>"
        '<span style="color:#888;font-size:14px;">·</span>'
        '<span style="color:#aaa;font-size:14px;">' + player_row["Position Group"] + "</span>"
        '<span style="color:#888;font-size:14px;">·</span>'
        '<span style="color:#aaa;font-size:14px;font-style:italic;">' + player_row["Competition"] + "</span>"
        "</div></div>"
    )


def score_cards_html(player_row: pd.Series) -> str:
    cards = []
    for attr in ATTRIBUTES:
        score = player_row[attr]
        color = score_color(score)
        pct   = int(score)
        cards.append(
            f'<div style="background:#ffffff;border:1px solid #ddd;border-left:4px solid {color};'
            f'border-radius:8px;padding:14px 16px;margin-bottom:10px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
            f'<span style="font-size:14px;color:#222;font-weight:600;">'
            f'{ATTRIBUTE_INFO[attr]["icon"]} {attr}</span>'
            f'<div><span style="font-size:22px;font-weight:700;color:{color};">{score:.0f}</span>'
            f'<span style="font-size:11px;color:#999;margin-left:4px;">/100</span></div></div>'
            f'<div style="background:#e8e8e8;border-radius:4px;height:6px;width:100%;overflow:hidden;">'
            f'<div style="background:{color};height:100%;width:{pct}%;border-radius:4px;"></div></div>'
            f'<div style="font-size:11px;color:#888;margin-top:5px;text-align:right;">'
            f'{score_label(score)}</div></div>'
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
        "Physical Analyst &mdash; Layer 1 Glossary</div>"
        + intro + "".join(blocks) + "</div>"
    )
