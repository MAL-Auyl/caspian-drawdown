"""Оценка риска объекта — формула из docs/00_DECISIONS.md / 05_API.md:
score = Σ(normalized_i × weight_i), нормировка компонент обязательна."""
import numpy as np

from pipeline.gee import config as cfg


def normalize(value: float, lo: float, hi: float) -> float:
    return float(np.clip((value - lo) / (hi - lo) * 100, 0, 100))


def years_to_threshold(distance_m: float, speed_m_per_year: float, critical_distance_m: float) -> float:
    if speed_m_per_year >= 0:
        return 99.0
    return max((critical_distance_m - distance_m) / abs(speed_m_per_year), 0)


def compute_risk(speed_m_per_year: float, distance_m: float, category: str) -> dict:
    crit_base = cfg.CATEGORY_CRITICALITY[category]["base"]
    crit_dist = cfg.CRITICAL_DISTANCE_M.get(category, 300)
    ttt = years_to_threshold(distance_m, speed_m_per_year, crit_dist)

    norm_speed = normalize(abs(speed_m_per_year), 0, 50)
    norm_dist = normalize(distance_m, 0, 1000)
    norm_crit = normalize(crit_base, 0, 10)
    norm_ttt = normalize(30 - min(ttt, 30), 0, 30)

    w = cfg.RISK_WEIGHTS
    score = round(
        norm_speed * w["retreat_speed"] + norm_dist * w["current_distance"]
        + norm_crit * w["criticality"] + norm_ttt * w["years_to_threshold"]
    )
    level = "high" if score >= 67 else "medium" if score >= 34 else "low"

    return {
        "score": score,
        "level": level,
        "criticality": crit_base,
        "years_to_threshold": round(ttt, 1),
        "components": {
            "speed": {"raw": speed_m_per_year, "normalized": round(norm_speed), "weight": w["retreat_speed"]},
            "distance": {"raw": distance_m, "normalized": round(norm_dist), "weight": w["current_distance"]},
            "criticality": {"raw": crit_base, "normalized": round(norm_crit), "weight": w["criticality"]},
            "years_to_threshold": {"raw": round(ttt, 1), "normalized": round(norm_ttt), "weight": w["years_to_threshold"]},
        },
    }
