"""
Bet Value Engine
Compares model probability against bookmaker implied probability.
Value gap = model_prob - implied_prob (percentage points).
"""
from dataclasses import dataclass


VALUE_RATING_LABELS = {
    (0, 3):   (1.5, "Poor value"),
    (3, 5):   (4.5, "Weak value"),
    (5, 8):   (6.5, "Fair value"),
    (8, 12):  (8.5, "Strong value"),
    (12, 999): (10.0, "Exceptional value"),
}


@dataclass
class ValueInput:
    model_probability: float    # 0–100
    bookmaker_odds: float       # decimal odds, e.g. 2.50


def compute_value(inp: ValueInput) -> dict:
    if inp.bookmaker_odds <= 1.0:
        return {
            "implied_probability": 100.0,
            "value_gap": inp.model_probability - 100.0,
            "value_rating": 1.0,
            "value_label": "Poor value",
            "is_value_bet": False,
        }

    implied_prob = round(100 / inp.bookmaker_odds, 2)
    value_gap = round(inp.model_probability - implied_prob, 2)

    rating = 1.0
    label = "Poor value"
    for (lo, hi), (r, l) in VALUE_RATING_LABELS.items():
        if lo <= value_gap < hi:
            rating = r
            label = l
            break

    return {
        "implied_probability": implied_prob,
        "value_gap": value_gap,
        "value_rating": rating,
        "value_label": label,
        "is_value_bet": value_gap >= 3.0,
    }
