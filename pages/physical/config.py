DATA_PATH = "data/physical/Layer1_Attribute_Results.csv"
RAW_DATA_PATH = "data/physical/SkillCorner-2026-02-10.csv"

ATTRIBUTES = ["Speed", "Acceleration", "Agility", "Endurance"]

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
