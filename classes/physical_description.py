from typing import List, Dict

import pandas as pd
from scipy.stats import zscore

from classes.description import Description
from pages.physical.config import ATTRIBUTES, ATTRIBUTE_INFO, FRIENDLY_NAMES, METRIC_PHRASES


def describe_level(z: float) -> str:
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


STYLE_TEMPLATES = {
    "Speed": {
        "outstanding": ["boasts elite top speed", "maximal sprint pace is exceptional"],
        "excellent": ["runs very fast", "top speed is high"],
        "good": ["above-average speed", "speeds ahead of many peers"],
        "average": ["speed is average", "acceleration is typical"],
        "below average": ["slower than many peers", "speed is a little under average"],
        "poor": ["struggles to reach high speed", "speed is weak"],
    },
    "Acceleration": {
        "outstanding": ["accelerates like a shot", "burst acceleration is explosive"],
        "excellent": ["accelerates really fast", "acceleration bursts are powerful"],
        "good": ["has very strong acceleration", "fast starting speed"],
        "average": ["acceleration is competent", "acceleration is reasonable"],
        "below average": ["acceleration is sluggish", "takes time to reach speed"],
        "poor": ["struggles to accelerate", "acceleration is weak"],
    },
    "Agility": {
        "outstanding": ["turns and changes direction brilliantly", "agility is elite"],
        "excellent": ["very agile", "sharp and responsive changes of direction"],
        "good": ["above-average agility", "quick with direction changes"],
        "average": ["adequate agility", "moves with standard agility"],
        "below average": ["lacks quickness in tight turns", "agility can be improved"],
        "poor": ["slow to change direction", "agility is poor"],
    },
    "Endurance": {
        "outstanding": ["maintains peak output all game", "elite stamina"],
        "excellent": ["strong endurance", "rarely fatigues"],
        "good": ["good stamina", "maintains pace well"],
        "average": ["average endurance", "sufficient match fitness"],
        "below average": ["tends to tire sooner than most", "stamina is a weak point"],
        "poor": ["struggles with longer minutes", "endurance is poor"],
    },
}


def describe_style(attr: str, level: str) -> str:
    """Pick a phrasing variant for the attribute + level.

    This is the wordalisation style mapping layer. It keeps the label logic
    in `describe_level` but provides more natural variation for output sentences.
    """
    options = STYLE_TEMPLATES.get(attr, {}).get(level)
    if not options:
        return f"is {level} in {attr.lower()}"
    return options[0]



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
        detailed: bool = False,
    ):
        self.player_row = player_row
        self.position_df = position_df
        self.raw_position_df = raw_position_df
        self.detailed = detailed
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
        return self._synthesize_text(detailed=self.detailed)

    def _synthesize_text(self, detailed: bool = False) -> str:
        p = self.player_row
        raw_df = self.raw_position_df
        n_peers = len(self.position_df)

        description = (
            f"Here is a physical profile of {p['Player']}, "
            f"who plays as a {p['Position Group']} for {p['Team']} in the {p['Competition']}. "
            f"All ratings are compared against {n_peers} {p['Position Group']} players.\n\n"
        )

        # Compute z-scores for each attribute within position group
        pos_df = self.position_df
        for attr in ATTRIBUTES:
            attr_mean = pos_df[attr].mean()
            attr_std = pos_df[attr].std()
            if attr_std == 0:
                z = 0.0
            else:
                z = (p[attr] - attr_mean) / attr_std

            level = describe_level(z)
            style = describe_style(attr, level)

            description += (
                f"He {style} compared to other players in the same position group. "
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

                level = describe_level(z)
                friendly = FRIENDLY_NAMES.get(col, col)
                if detailed:
                    phrase = METRIC_PHRASES.get(friendly, {}).get(level) or describe_style(attr, level)
                    if z > 1.0:
                        standouts.append(f"He {phrase}.")
                    elif z < -0.5:
                        concerns.append(f"He {phrase}.")
                else:
                    if z > 1.0:
                        standouts.append(f"His {friendly} was {level}.")
                    elif z < -0.5:
                        concerns.append(f"His {friendly} was {level}.")

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
