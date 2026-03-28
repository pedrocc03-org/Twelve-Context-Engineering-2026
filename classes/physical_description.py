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


FRIENDLY_NAMES = {
    "PSV-99": "top speed",
    "TOP 5 PSV-99": "average top speed",
    "TOP 3 Time to Sprint": "time to reach sprint speed",
    "TOP 3 Time to HSR": "time to reach high-speed running",
    "TOP 3 Time to Sprint post-COD": "time to sprint after changing direction",
    "TOP 3 Time to HSR post-COD": "time to reach high-speed running after changing direction",
    "Explosive Acceleration to Sprint Count P90": "explosive sprint burst volume",
    "Explosive Acceleration to HSR Count P90": "explosive high-speed running burst volume",
    "Change of Direction Count P90": "change of direction frequency",
    "TOP 3 Time to 505 around 90": "90-degree turning speed",
    "TOP 3 Time to 505 around 180": "180-degree turning speed",
    "M/min P90": "metres per minute",
    "Distance P90": "total distance covered",
    "Running Distance P90": "running distance",
    "HSR Distance P90": "high-speed running distance",
}


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

        # Only call out metrics that are outstanding/excellent or below average/poor
        standouts = []
        concerns = []

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

                level = metric_level(z)
                friendly = FRIENDLY_NAMES.get(col, col)
                # Only include outstanding/excellent or below average/poor
                if z > 1.0:
                    standouts.append(f"His {friendly} ({attr}) was {level}.")
                elif z < -0.5:
                    concerns.append(f"His {friendly} ({attr}) was {level}.")

        if standouts:
            description += "\n" + " ".join(standouts)

        if concerns:
            description += "\n" + " ".join(concerns)

        return description

    def get_prompt_messages(self) -> List[Dict[str, str]]:
        prompt = (
            "Please use the physical profile description enclosed with ``` to give a concise summary "
            "of the player's physical profile, strengths and weaknesses. "
            "Lead with the four qualities — Speed, Acceleration, Agility, and Endurance. "
            "You may reference specific underlying metrics only when they are a clear standout or a clear concern — do not list them all. "
            "The first sentence should give an overview of what kind of athlete this player is, mentioning the competition and team. "
            "The second sentence should describe the player's physical strengths. "
            "The third sentence should describe physical limitations or areas where the player is average or weak. "
            "Finally, summarise what this physical profile means for the player overall. "
            "Do not mention z-scores, percentile numbers, or ranks. "
            "Write as a performance analyst would in a report to coaching staff."
        )
        return [{"role": "user", "content": prompt}]
