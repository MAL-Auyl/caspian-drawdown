"""Общая статистика по трансектам — используется и моком, и реальным пайплайном,
чтобы оба считали риск и уверенность одинаково (грабля #3 из прошлого прогона:
разные методы сопоставления давали разные метрики для одних и тех же данных).

Грабля #4 (обнаружена на полном 26-летнем прогоне реальных данных): единичный
ложный кроссинг в один год (например, 176 м вместо стабильных 5250-5280 м все
остальные 18 лет) утаскивает всю регрессию в абсурдную скорость. Перед финальной
регрессией отбрасываем такие выбросы по критерию Хампеля от residuals первого
прохода — не от сырых значений, иначе настоящий тренд тоже резался бы как "выброс".
"""
import numpy as np
from scipy import stats

MIN_OUTLIER_RESIDUAL_M = 50.0
HAMPEL_K = 3.0


def _linregress(xs: list[int], ys: list[float]) -> dict:
    res = stats.linregress(xs, ys)
    dof = max(len(xs) - 2, 1)
    tval = float(stats.t.ppf(0.975, dof))
    ci_half = tval * (res.stderr or 0.0)
    return {
        "model": "linear",
        "slope_m_per_year": round(float(res.slope), 2),
        "intercept": round(float(res.intercept), 1),
        "r_squared": round(float(res.rvalue ** 2), 3),
        "std_error": round(float(res.stderr or 0.0), 2),
        "ci_95_low": round(float(res.slope - ci_half), 2),
        "ci_95_high": round(float(res.slope + ci_half), 2),
        "n": len(xs),
        "slope_raw": res.slope, "intercept_raw": res.intercept,
    }


def _reject_outliers(xs: list[int], ys: list[float], first_pass: dict) -> tuple[list[int], list[float], int]:
    residuals = np.array(ys) - (first_pass["slope_raw"] * np.array(xs) + first_pass["intercept_raw"])
    mad = float(np.median(np.abs(residuals - np.median(residuals))))
    threshold = max(HAMPEL_K * 1.4826 * mad, MIN_OUTLIER_RESIDUAL_M)
    keep = np.abs(residuals) <= threshold
    xs_clean = [x for x, k in zip(xs, keep) if k]
    ys_clean = [y for y, k in zip(ys, keep) if k]
    return xs_clean, ys_clean, int((~keep).sum())


def regression_for(years: list[int], positions: dict[int, float | None]) -> dict:
    xs = [y for y in years if positions.get(y) is not None]
    ys = [positions[y] for y in years if positions.get(y) is not None]
    if len(xs) < 3:
        return {
            "model": "linear", "slope_m_per_year": 0.0, "intercept": 0.0,
            "r_squared": 0.0, "std_error": 0.0, "ci_95_low": 0.0, "ci_95_high": 0.0,
            "n": len(xs), "n_outliers_removed": 0,
        }

    first_pass = _linregress(xs, ys)
    xs_clean, ys_clean, n_removed = _reject_outliers(xs, ys, first_pass)

    if n_removed == 0 or len(xs_clean) < 3:
        result = first_pass
    else:
        result = _linregress(xs_clean, ys_clean)
        result["n"] = len(xs)  # valid_years считаем по исходным наблюдениям, не после чистки

    result = {k: v for k, v in result.items() if k not in ("slope_raw", "intercept_raw")}
    result["n_outliers_removed"] = n_removed
    return result


def confidence_of(r_squared: float, valid_years: int) -> str:
    if r_squared >= 0.8 and valid_years >= 20:
        return "high"
    if r_squared >= 0.5 and valid_years >= 15:
        return "medium"
    return "low"


def risk_class_of(speed_m_per_year: float) -> str:
    if speed_m_per_year <= -20:
        return "high"
    if speed_m_per_year <= -8:
        return "medium"
    return "low"
