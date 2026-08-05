"""Общая статистика по трансектам — используется и моком, и реальным пайплайном,
чтобы оба считали риск и уверенность одинаково (грабля #3 из прошлого прогона:
разные методы сопоставления давали разные метрики для одних и тех же данных)."""
from scipy import stats


def regression_for(years: list[int], positions: dict[int, float | None]) -> dict:
    xs = [y for y in years if positions.get(y) is not None]
    ys = [positions[y] for y in years if positions.get(y) is not None]
    if len(xs) < 3:
        return {
            "model": "linear", "slope_m_per_year": 0.0, "intercept": 0.0,
            "r_squared": 0.0, "std_error": 0.0, "ci_95_low": 0.0, "ci_95_high": 0.0,
            "n": len(xs),
        }
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
    }


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
