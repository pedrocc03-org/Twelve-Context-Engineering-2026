from typing import List, Dict

import pandas as pd
from scipy.stats import zscore

from classes.description import Description
from pages.physical.config import ATTRIBUTES, ATTRIBUTE_INFO


def physical_level(percentile: float) -> str:
    """Convert a 0-100 percentile to a descriptive word."""
    if percentile >= 90:
        return "exceptional"
    if percentile >= 80:
        return "elite"
    if percentile >= 65:
        return "well above average"
    if percentile >= 50:
        return "above average"
    if percentile >= 40:
        return "average"
    if percentile >= 25:
        return "below average"
    if percentile >= 10:
        return "well below average"
    return "very poor"


def metric_level(z: float) -> str:
    """Convert a z-score to a descriptive word using course thresholds."""
    if z > 1.5:
        return "outstanding"
    if z > 1.0:
        return "excellent"
    if z > 0.5:
        return "good"
    if z > -0.5:
        return "average"
    if z > -1.0:
        return "below average"
    return "poor"


def _is_notable(z: float) -> bool:
    """Return True if z-score is notably good or bad (outside ±0.5)."""
    return abs(z) > 0.5


def _raw_col_name(config_metric: str) -> str:
    """Strip the (INV) suffix used in config to get the actual CSV column name."""
    return config_metric.replace(" (INV)", "")


class PhysicalDescription(Description):
    output_token_limit = 250

    @property
    def gpt_examples_path(self):
        return f"{self.gpt_examples_base}/Physical.xlsx"

    @property
    def describe_paths(self):
        return [f"{self.describe_base}/Physical.xlsx"]

    def __init__(
        self,
        player_row: pd.Series,
        position_df: pd.DataFrame,
        raw_position_df: pd.DataFrame,
    ):
        self.player_row = player_row
        self.position_df = position_df
        self.raw_position_df = raw_position_df
        super().__init__()

    def get_intro_messages(self) -> List[Dict[str, str]]:
        intro = [
            {
                "role": "system",
                "content": (
                    "You are an experienced physical performance analyst working in elite football. "
                    "You write concise physical profiles for coaching staff and recruitment departments. "
                    "You focus on what physical data means for how a player actually performs on the pitch — "
                    "not just reciting numbers, but interpreting what those numbers imply about playing style, "
                    "tactical suitability, and areas for physical development. "
                    "You write in British English and refer to the sport as football."
                ),
            },
            {
                "role": "user",
                "content": "Do you refer to the sport as soccer or football?",
            },
            {
                "role": "assistant",
                "content": (
                    "I always refer to the sport as football. "
                    "I am a physical performance analyst based in the UK and work with elite football clubs."
                ),
            },
        ]
        if len(self.describe_paths) > 0:
            intro += [
                {
                    "role": "user",
                    "content": "First, could you answer some questions about physical performance data in football?",
                },
                {"role": "assistant", "content": "Of course."},
            ]
        return intro

    def synthesize_text(self) -> str:
        p = self.player_row
        raw_df = self.raw_position_df
        n_peers = len(self.position_df)

        description = (
            f"Here is a physical profile of {p['Player']}, "
            f"who plays as a {p['Position Group']} for {p['Team']} in the {p['Competition']}. "
            f"All ratings are compared against {n_peers} {p['Position Group']} players.\n\n"
        )

        # High-level attribute summary using word labels
        for attr in ATTRIBUTES:
            score = p[attr]
            description += (
                f"He was {physical_level(score)} in {attr} "
                f"compared to other players in the same position group. "
            )
        description += "\n"

        # Find the player in the raw data for notable metric call-outs
        raw_player = raw_df[raw_df["Player"] == p["Player"]]
        if raw_player.empty:
            return description

        raw_player = raw_player.iloc[0]

        # Only mention metrics that are notably good or bad
        notable_strengths = []
        notable_weaknesses = []

        for attr in ATTRIBUTES:
            info = ATTRIBUTE_INFO[attr]
            for config_metric, weight in info["metrics"].items():
                col = _raw_col_name(config_metric)
                is_inverted = "(INV)" in config_metric

                if col not in raw_df.columns:
                    continue

                val = raw_player[col]
                if pd.isna(val):
                    continue

                col_data = raw_df[col].dropna()
                z_arr = zscore(col_data.values, nan_policy="omit")
                player_mask = raw_df["Player"] == p["Player"]
                player_indices = raw_df.loc[player_mask].index
                matching = [i for i in player_indices if i in col_data.index]
                if not matching:
                    continue

                pos = list(col_data.index).index(matching[0])
                z = float(z_arr[pos])
                if is_inverted:
                    z = -z

                if not _is_notable(z):
                    continue

                level = metric_level(z)
                entry = f"In {col}, which contributes to {attr}, he was {level}."

                if z > 0.5:
                    notable_strengths.append(entry)
                else:
                    notable_weaknesses.append(entry)

        if notable_strengths:
            description += "\nNotable strengths in underlying metrics: "
            description += " ".join(notable_strengths)

        if notable_weaknesses:
            description += "\nNotable weaknesses in underlying metrics: "
            description += " ".join(notable_weaknesses)

        return description

    def get_prompt_messages(self) -> List[Dict[str, str]]:
        prompt = (
            "Please use the physical profile description enclosed with ``` to give a concise, 4 sentence summary "
            "of the player's physical profile, strengths and weaknesses. "
            "The first sentence should use varied language to give an overview of what kind of athlete this player is. "
            "The second sentence should describe the player's physical strengths, referencing specific underlying metrics only where they are notably good or excellent. "
            "The third sentence should describe physical limitations or areas where the player is average or weak. "
            "Finally, summarise what kind of role or tactical system would suit this player's physical profile. "
            "Do not mention z-scores, percentile numbers, or ranks. Use natural language throughout. "
            "Write as a performance analyst would in a report to coaching staff."
        )
        return [{"role": "user", "content": prompt}]
