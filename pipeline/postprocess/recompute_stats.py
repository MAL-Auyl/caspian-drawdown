"""Пересчитывает регрессию/уверенность/класс риска по уже собранным
позициям трансект — без повторного обращения к Earth Engine. Полезно
после изменений в pipeline/common/stats.py (например, добавление защиты
от выбросов) — сырые позиции менять не нужно, только статистику поверх них.

Запуск:
    python3 -m pipeline.postprocess.recompute_stats --in data/real/transects.geojson
"""
import argparse
import json
from pathlib import Path

from pipeline.common.stats import confidence_of, regression_for, risk_class_of

REPO_ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", default="data/real/transects.geojson")
    args = parser.parse_args()

    path = REPO_ROOT / args.in_path
    fc = json.loads(path.read_text(encoding="utf-8"))

    changed, total_outliers = 0, 0
    for f in fc["features"]:
        p = f["properties"]
        positions = {int(y): v for y, v in p["positions"].items()}
        years = sorted(positions.keys())
        reg = regression_for(years, positions)

        old_speed = p["speed_m_per_year"]
        valid = [y for y in years if positions.get(y) is not None]
        total_retreat = round(positions[valid[0]] - positions[valid[-1]], 1) if len(valid) >= 2 else None

        p["speed_m_per_year"] = reg["slope_m_per_year"]
        p["r_squared"] = reg["r_squared"]
        p["std_error"] = reg["std_error"]
        p["ci_95_low"] = reg["ci_95_low"]
        p["ci_95_high"] = reg["ci_95_high"]
        p["confidence"] = confidence_of(reg["r_squared"], reg["n"])
        p["risk_class"] = risk_class_of(reg["slope_m_per_year"])
        p["total_retreat_m"] = total_retreat
        p["outliers_removed"] = reg["n_outliers_removed"]

        if reg["n_outliers_removed"] > 0:
            total_outliers += reg["n_outliers_removed"]
        if old_speed != reg["slope_m_per_year"]:
            changed += 1

    path.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    print(f"OK: {len(fc['features'])} трансект пересчитано, "
          f"{changed} изменили скорость, {total_outliers} выбросов отфильтровано -> {path}")


if __name__ == "__main__":
    main()
