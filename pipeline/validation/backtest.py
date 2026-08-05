"""Синтетическая валидация: генерируем позиции трансекты с ИЗВЕСТНОЙ
скоростью и шумом, прогоняем через ту же регрессию, что и реальный
пайплайн (pipeline/common/stats.py), сравниваем восстановленную скорость
с истинной. Проверяет корректность статистики, а не качество снимков —
отдельный этап от валидации на контрольных участках с реальными данными.

Запуск:
    python3 -m pipeline.validation.backtest
"""
import numpy as np

from pipeline.common.stats import regression_for

RNG = np.random.default_rng(123)


def synth_positions(years: list[int], true_speed: float, noise_std: float, missing: set[int] = frozenset()) -> dict[int, float | None]:
    p0 = 12000.0
    positions = {}
    for y in years:
        if y in missing:
            positions[y] = None
            continue
        positions[y] = round(p0 + true_speed * (y - years[0]) + RNG.normal(0, noise_std), 1)
    return positions


def run(n_trials: int = 200) -> dict:
    years = list(range(2000, 2027))
    missing = {2012}
    errors, correls = [], []
    for _ in range(n_trials):
        true_speed = float(RNG.uniform(-40, 3))
        noise = float(RNG.uniform(1, 6))
        positions = synth_positions(years, true_speed, noise, missing)
        reg = regression_for(years, positions)
        errors.append(abs(reg["slope_m_per_year"] - true_speed))
        correls.append(reg["r_squared"])

    mae = round(float(np.mean(errors)), 3)
    mean_r2 = round(float(np.mean(correls)), 4)
    return {"n_trials": n_trials, "mae_m_per_year": mae, "mean_r_squared": mean_r2}


def main():
    result = run()
    print(f"Синтетическая валидация: {result['n_trials']} прогонов, "
          f"MAE={result['mae_m_per_year']} м/год, средний R²={result['mean_r_squared']}")
    assert result["mae_m_per_year"] < 1.0, "регрессия работает некорректно"
    print("OK: статистика пайплайна восстанавливает известную скорость с малой ошибкой")


if __name__ == "__main__":
    main()
