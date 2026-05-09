import random
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


def _raw_col_name(config_metric: str) -> str:
    """Strip the (INV) suffix used in config to get the actual CSV column name."""
    return config_metric.replace(" (INV)", "")


STYLE_TEMPLATES = {
    "Speed": {
        "outstanding": ["boasts elite top speed", "maximal sprint pace is exceptional", "has top-end pace that few peers can match"],
        "excellent": ["runs very fast", "top speed is high", "has strong pace over distance"],
        "good": ["above-average speed", "speeds ahead of many peers", "has a useful edge in top-end pace"],
        "average": ["speed is average", "pace is typical for the position", "sits around the middle of the pack for speed"],
        "below average": ["slower than many peers", "speed is a little under average", "lacks the pace of most positional peers"],
        "poor": ["struggles to reach high speed", "speed is weak", "has notably low top-end pace"],
    },
    "Acceleration": {
        "outstanding": ["accelerates like a shot", "burst acceleration is explosive", "gets to speed almost instantly"],
        "excellent": ["accelerates really fast", "acceleration bursts are powerful", "reaches speed quickly and sharply"],
        "good": ["has very strong acceleration", "fast starting speed", "gets up to pace well"],
        "average": ["acceleration is competent", "acceleration is reasonable", "reaches speed at a typical rate"],
        "below average": ["acceleration is sluggish", "takes time to reach speed", "is slow to get up to pace"],
        "poor": ["struggles to accelerate", "acceleration is weak", "takes significantly longer than peers to reach speed"],
    },
    "Agility": {
        "outstanding": ["turns and changes direction brilliantly", "agility is elite", "is exceptionally sharp through direction changes"],
        "excellent": ["very agile", "sharp and responsive changes of direction", "executes turns with real quality"],
        "good": ["above-average agility", "quick with direction changes", "handles direction changes well"],
        "average": ["adequate agility", "moves with standard agility", "changes direction at a typical rate"],
        "below average": ["lacks quickness in tight turns", "agility can be improved", "is a little stiff through direction changes"],
        "poor": ["slow to change direction", "agility is poor", "struggles to turn and adjust quickly"],
    },
    "Endurance": {
        "outstanding": ["maintains peak output all game", "elite stamina", "covers an exceptional amount of ground across a full match"],
        "excellent": ["strong endurance", "rarely fatigues", "sustains high physical output throughout matches"],
        "good": ["good stamina", "maintains pace well", "keeps up a solid work rate over 90 minutes"],
        "average": ["average endurance", "sufficient match fitness", "covers a typical amount of ground for the position"],
        "below average": ["tends to tire sooner than most", "stamina is a weak point", "physical output drops off compared to peers"],
        "poor": ["struggles with longer minutes", "endurance is poor", "covers noticeably less ground than most peers"],
    },
}


def describe_style(attr: str, level: str) -> str:
    """Pick a random phrasing variant for the attribute + level."""
    options = STYLE_TEMPLATES.get(attr, {}).get(level)
    if not options:
        return f"is {level} in {attr.lower()}"
    return random.choice(options)



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
        self.attr_zscores = self._compute_attr_zscores()
        self.metric_zscores = self._compute_metric_zscores()
        super().__init__()

    def _compute_attr_zscores(self) -> dict:
        p = self.player_row
        pos_df = self.position_df
        result = {}
        for attr in ATTRIBUTES:
            mean = pos_df[attr].mean()
            std = pos_df[attr].std()
            result[attr] = 0.0 if std == 0 else (p[attr] - mean) / std
        return result

    def _compute_metric_zscores(self) -> dict:
        """Precompute z-scores for every raw metric for the selected player."""
        p = self.player_row
        raw_df = self.raw_position_df
        raw_player_rows = raw_df[raw_df["Player"] == p["Player"]]
        if raw_player_rows.empty:
            return {}

        raw_player = raw_player_rows.iloc[0]
        result = {}

        for attr in ATTRIBUTES:
            for config_metric in ATTRIBUTE_INFO[attr]["metrics"]:
                col = _raw_col_name(config_metric)
                is_inverted = "(INV)" in config_metric
                if col not in raw_df.columns:
                    continue
                val = raw_player[col]
                if pd.isna(val):
                    continue
                col_data = raw_df[col].dropna()
                z_series = pd.Series(
                    zscore(col_data.values, nan_policy="omit"), index=col_data.index
                )
                player_idx = raw_player.name
                if player_idx not in z_series.index:
                    continue
                z = float(z_series.loc[player_idx])
                result[config_metric] = -z if is_inverted else z

        return result

    def get_intro_messages(self) -> List[Dict[str, str]]:
        intro = [
            {
                "role": "system",
                "content": (
                    "You are an experienced physical performance analyst working in elite football. "
                    "You write concise physical profiles for coaching staff and recruitment departments. "
                    "You focus only on tracked physical data and what it says about the player's movement capacity, "
                    "speed, acceleration, agility, endurance, distance, intensity, and physical limitations. "
                    "You do not discuss tactics, technical quality, mentality, team fit, or broader football interpretation. "
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
        n_peers = len(self.position_df)

        description = (
            f"Here is a physical profile of {p['Player']}, "
            f"who plays as a {p['Position Group']} for {p['Team']} in the {p['Competition']}. "
            f"All ratings are compared against {n_peers} {p['Position Group']} players.\n\n"
        )

        for attr in ATTRIBUTES:
            z = self.attr_zscores[attr]
            level = describe_level(z)
            style = describe_style(attr, level)
            description += (
                f"The player {style} compared to other players in the same position group. "
            )
        description += "\n"

        if not self.metric_zscores:
            return description

        # Only call out metrics that are outstanding/excellent or below average/poor
        standouts = []
        concerns = []

        for attr in ATTRIBUTES:
            for config_metric in ATTRIBUTE_INFO[attr]["metrics"]:
                if config_metric not in self.metric_zscores:
                    continue

                z = self.metric_zscores[config_metric]
                col = _raw_col_name(config_metric)
                level = describe_level(z)
                friendly = FRIENDLY_NAMES.get(col, col)
                if detailed:
                    phrase = METRIC_PHRASES.get(friendly, {}).get(level) or describe_style(attr, level)
                    if z > 1.0:
                        standouts.append(phrase.capitalize() + ".")
                    elif z < -0.5:
                        concerns.append(phrase.capitalize() + ".")
                else:
                    phrase = METRIC_PHRASES.get(friendly, {}).get(level)
                    if not phrase:
                        phrase = f"shows {level} {friendly}"
                    if z > 1.0:
                        standouts.append(phrase.capitalize() + ".")
                    elif z < -0.5:
                        concerns.append(phrase.capitalize() + ".")

        if standouts:
            description += "\nStrengths:\n" + "\n".join(f"- {s}" for s in standouts)

        if concerns:
            description += "\nAreas of concern:\n" + "\n".join(f"- {c}" for c in concerns)

        return description

    def get_prompt_messages(self) -> List[Dict[str, str]]:
        shared_rules = (
            "Critical rules: "
            "- Write in short, simple clauses. Do not stack multiple qualifiers into one clause. "
            "  Bad: 'combining average top speed and sluggish acceleration with strong endurance'. "
            "  Good: 'he has average top speed and is slow to accelerate, but covers large distances'. "
            "- Use direct language. Say 'he is a speed-focused midfielder' not 'he shows a speed-focused profile'. "
            "  Say 'he has good pace' not 'he combines solid pace'. "
            "  Say 'he is quick' not 'his speed is good'. Say 'allows him to' not 'enables'. "
            "- Only describe what the physical data shows. Do not infer tactics, role suitability, "
            "  technical quality, mentality, football intelligence, or team context. "
            "- You can say what the player's body can and cannot do physically. "
            "  Do not say how he plays, how he fits a system, or what he would do in match situations. "
            "- Frame output as what the player's physicality allows or limits. "
            "  Say 'his agility allows him to change direction quickly' not 'he frequently changes direction in games'. "
            "- Never capitalise any word mid-sentence. "
            "- Do not mention z-scores, percentile numbers, or ranks. "
            "- Do not start with the player's name — start with the profile description."
        )

        if self.detailed:
            prompt = (
                "Please use the physical profile description enclosed with ``` to write a detailed physical report "
                "of three to four sentences. "
                "The first sentence should characterise the overall physical profile as an athlete. "
                "The remaining sentences should reference the specific metric strengths and concerns listed under "
                "'Strengths' and 'Areas of concern' in the profile, explaining in plain language what each means "
                "for the player's physical capability. Cover both standout qualities and notable weaknesses. "
                "Describe only what the player's body can or cannot do physically. "
                "Never mention pressing, transitions, counter-attacks, tactical roles, match actions, technical actions, or mentality. "
                + shared_rules
            )
        else:
            prompt = (
                "Please use the physical profile description enclosed with ``` to write a short, plain summary "
                "of the player's physical profile. Two sentences maximum. "
                "The first sentence should describe what type of physical athlete this is — e.g. "
                "'a relentless, non-explosive forward who covers large distances and changes direction a lot "
                "but has average top speed and is slow to accelerate.' "
                "If needed, a second sentence can add what this physically allows or limits, staying strictly within physical capacity. "
                + shared_rules
            )

        return [{"role": "user", "content": prompt}]
