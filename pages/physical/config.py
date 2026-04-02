DATA_PATH = "data/physical/Layer1_Attribute_Results.csv"
RAW_DATA_PATH = "data/physical/SkillCorner-2026-02-10.csv"

ATTRIBUTES = ["Speed", "Acceleration", "Agility", "Endurance"]

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

# Contextual phrases for individual metric call-outs, keyed by friendly name then level.
# Used in synthesize_text to replace generic "His X was outstanding" sentences.
METRIC_PHRASES = {
    "top speed": {
        "outstanding": "hits an elite top speed that few in his position can match",
        "excellent": "reaches very high top speeds",
        "good": "shows above-average top speed",
        "average": "reaches a typical top speed for his position",
        "below average": "falls short of the top speeds common at this level",
        "poor": "struggles to reach high top speed",
    },
    "average top speed": {
        "outstanding": "consistently hits elite sprint speeds across a full match",
        "excellent": "maintains very high speeds across his fastest efforts",
        "good": "shows strong average top speed across efforts",
        "average": "averages a typical top speed for his position",
        "below average": "average top speed is a little under par",
        "poor": "rarely reaches high speeds even at his fastest",
    },
    "time to reach sprint speed": {
        "outstanding": "explodes to sprint speed with exceptional quickness",
        "excellent": "reaches sprint speed very rapidly",
        "good": "accelerates to sprint speed well",
        "average": "reaches sprint speed in a typical time",
        "below average": "takes slightly longer than peers to hit sprint speed",
        "poor": "is slow to reach sprint speed",
    },
    "time to reach high-speed running": {
        "outstanding": "gets to high-speed running pace in an instant",
        "excellent": "transitions to high-speed running very quickly",
        "good": "reaches high-speed running pace faster than most",
        "average": "reaches high-speed running pace in a typical time",
        "below average": "takes longer than most to reach high-speed running",
        "poor": "struggles to build into high-speed running quickly",
    },
    "time to sprint after changing direction": {
        "outstanding": "recovers sprint speed after changing direction almost instantly",
        "excellent": "quickly regains sprint speed following a direction change",
        "good": "recovers well to sprint after changing direction",
        "average": "recovers to sprint pace after direction changes in a typical time",
        "below average": "takes longer than most to recover sprint speed after a turn",
        "poor": "struggles to regain sprint speed after changing direction",
    },
    "time to reach high-speed running after changing direction": {
        "outstanding": "instantly reaches high-speed running after direction changes",
        "excellent": "recovers to high-speed running very quickly after turning",
        "good": "gets back to high-speed running well after changing direction",
        "average": "recovers to high-speed running after turns in a normal time",
        "below average": "takes a little longer than peers to reach high-speed running after turns",
        "poor": "is slow to reach high-speed running after direction changes",
    },
    "explosive sprint burst volume": {
        "outstanding": "produces an exceptional number of explosive sprint bursts per match",
        "excellent": "generates a high volume of explosive sprint accelerations",
        "good": "produces above-average explosive sprint bursts",
        "average": "hits a typical number of explosive sprint bursts per match",
        "below average": "produces fewer explosive sprint bursts than most peers",
        "poor": "rarely produces explosive sprint bursts",
    },
    "explosive high-speed running burst volume": {
        "outstanding": "delivers an elite volume of explosive high-speed running bursts",
        "excellent": "produces a high number of explosive high-speed running efforts",
        "good": "above-average in explosive high-speed running bursts",
        "average": "averages a typical number of explosive high-speed running bursts",
        "below average": "produces fewer high-speed running bursts than most peers",
        "poor": "rarely bursts into high-speed running explosively",
    },
    "change of direction frequency": {
        "outstanding": "changes direction an exceptional number of times per match — elite agility output",
        "excellent": "executes a high volume of direction changes across a game",
        "good": "above-average in how often he changes direction",
        "average": "changes direction at a typical rate for his position",
        "below average": "fewer direction changes than most peers",
        "poor": "rarely makes sharp direction changes during matches",
    },
    "90-degree turning speed": {
        "outstanding": "turns at 90 degrees with elite sharpness and speed",
        "excellent": "executes 90-degree turns very quickly",
        "good": "above-average speed through 90-degree turns",
        "average": "completes 90-degree turns at a typical pace",
        "below average": "a little slow through 90-degree turns",
        "poor": "struggles to turn sharply at 90 degrees",
    },
    "180-degree turning speed": {
        "outstanding": "pivots 180 degrees with exceptional speed — elite directional reversal",
        "excellent": "very fast through 180-degree turns",
        "good": "above-average at completing tight 180-degree turns",
        "average": "takes a typical time to complete 180-degree turns",
        "below average": "slower than most through 180-degree turns",
        "poor": "struggles with tight 180-degree direction changes",
    },
    "metres per minute": {
        "outstanding": "covers ground at an elite intensity throughout matches — top stamina",
        "excellent": "maintains a very high work rate across full matches",
        "good": "above-average metres per minute — strong engine",
        "average": "covers a typical distance per minute for his position",
        "below average": "slightly below average in metres per minute",
        "poor": "covers ground at a low rate — endurance is a concern",
    },
    "total distance covered": {
        "outstanding": "covers an elite total distance per match — exceptional endurance",
        "excellent": "covers a very high total distance across matches",
        "good": "above-average total distance covered",
        "average": "covers a typical total distance for his position",
        "below average": "total distance covered is below average",
        "poor": "covers notably less ground than peers — fitness may limit contribution",
    },
    "running distance": {
        "outstanding": "running distance per match is at an elite level",
        "excellent": "logs a very high running distance per match",
        "good": "above-average running distance",
        "average": "running distance is typical for his position",
        "below average": "running distance is a little below average",
        "poor": "running distance is well below peers — endurance is limited",
    },
    "high-speed running distance": {
        "outstanding": "logs an elite volume of high-speed running — outstanding aerobic power",
        "excellent": "covers a very high distance at high speed across a match",
        "good": "above-average high-speed running distance",
        "average": "high-speed running distance is typical for his position",
        "below average": "below average in high-speed running distance",
        "poor": "low high-speed running distance — struggles to sustain intense efforts",
    },
}

ATTRIBUTE_INFO = {
    "Speed": {
        "icon": "⚡",
        "definition": "Peak velocity capability — how fast can the player run at maximum effort?",
        "metrics": {
            "PSV-99": 0.55,
            "TOP 5 PSV-99": 0.45,
        },
    },
    "Acceleration": {
        "icon": "🚀",
        "definition": (
            "Overall acceleration profile — how quickly does a player reach high speeds, "
            "how explosive are their bursts, and how well do they recover speed after changing direction?"
        ),
        "metrics": {
            "TOP 3 Time to Sprint (INV)": 0.30,
            "TOP 3 Time to HSR (INV)": 0.20,
            "TOP 3 Time to Sprint post-COD (INV)": 0.20,
            "TOP 3 Time to HSR post-COD (INV)": 0.10,
            "Explosive Acceleration to Sprint Count P90": 0.10,
            "Explosive Acceleration to HSR Count P90": 0.10,
        },
    },
    "Agility": {
        "icon": "🔄",
        "definition": (
            "Change of direction quality — how quickly and effectively "
            "can the player execute sharp turns?"
        ),
        "metrics": {
            "Change of Direction Count P90": 0.50,
            "TOP 3 Time to 505 around 90° (INV)": 0.25,
            "TOP 3 Time to 505 around 180° (INV)": 0.25,
        },
    },
    "Endurance": {
        "icon": "🏃",
        "definition": (
            "Sustained physical output — how much distance and sustained effort "
            "does the player produce across a full match?"
        ),
        "metrics": {
            "M/min P90": 0.30,
            "Distance P90": 0.25,
            "Running Distance P90": 0.25,
            "HSR Distance P90": 0.20,
        },
    },
}
