"""Official-ish team colors, keyed by Jolpica constructor_ref.

Jolpica/Ergast doesn't provide brand colors, and this is purely cosmetic
for the frontend's team-color accents, so it's a small static map rather
than something worth pulling from another API.
"""

TEAM_COLORS: dict[str, tuple[str, str]] = {
    "red_bull": ("#3671C6", "#1E3A8A"),
    "ferrari": ("#F91536", "#8C0B1E"),
    "mercedes": ("#6CD3BF", "#27F4D2"),
    "mclaren": ("#FF8000", "#B35900"),
    "aston_martin": ("#358C75", "#1F5C4C"),
    "alpine": ("#2293D1", "#FF87BC"),
    "williams": ("#37BEDD", "#1C6E82"),
    "alphatauri": ("#5E8FAA", "#2B4C5E"),
    "alfa": ("#C92D4B", "#701A2C"),
    "haas": ("#B6BABD", "#6E7072"),
    "rb": ("#6692FF", "#2C3E9E"),  # 2024+ rename of alphatauri
    "sauber": ("#52E252", "#1E7A1E"),  # 2024+ rename of alfa
}
