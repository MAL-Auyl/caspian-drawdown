"""Модуль 1 (инновационный, после часа 36): критический уровень моря.

Связывает позицию берега на трансекте с абсолютной отметкой уровня Каспия
(альтиметрия) и решает обратную задачу: при каком уровне объект достигает
критического расстояния до воды. См. docs/11_INNOVATION_MODULES.md.

Запуск:
    python3 -m pipeline.postprocess.critical_level
"""
import csv
import json
from pathlib import Path

from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
LEVEL_CSV = REPO_ROOT / "pipeline" / "data" / "manual" / "caspian_level.csv"


def load_levels(path: Path = LEVEL_CSV) -> dict[int, float]:
    levels = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            levels[int(row["year"])] = float(row["level_m"])
    return levels


def level_response(positions: dict[int, float | None], levels: dict[int, float]) -> dict | None:
    """Связь «уровень моря -> положение берега» для одной трансекты.
    Возвращает None, если наблюдений мало или связь статистически слабая —
    такую трансекту в модуль критического уровня не включаем."""
    pairs = [(levels[y], p) for y, p in positions.items() if p is not None and y in levels]
    if len(pairs) < 12:
        return None

    xs = [lv for lv, _ in pairs]
    ys = [ps for _, ps in pairs]
    res = stats.linregress(xs, ys)
    if res.rvalue ** 2 < 0.3:
        return None

    return {
        "slope_m_per_m": round(float(res.slope), 1),
        "intercept": round(float(res.intercept), 1),
        "r_squared": round(float(res.rvalue ** 2), 3),
        "std_error": round(float(res.stderr or 0.0), 2),
        "n_points": len(pairs),
    }


def critical_level_for(response: dict, position_crit_m: float) -> float:
    """Отметка уровня, при которой берег достигнет критической позиции."""
    return round((position_crit_m - response["intercept"]) / response["slope_m_per_m"], 2)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--transects", default="data/processed/transects.geojson")
    parser.add_argument("--objects", default="data/processed/objects.geojson")
    parser.add_argument("--out", default="data/processed/critical_level.json")
    args = parser.parse_args()

    levels = load_levels()
    transects = json.loads((REPO_ROOT / args.transects).read_text(encoding="utf-8"))
    objects = json.loads((REPO_ROOT / args.objects).read_text(encoding="utf-8"))

    by_id = {f["properties"]["transect_id"]: f for f in transects["features"]}
    results = {}
    for obj in objects["features"]:
        p = obj["properties"]
        tf = by_id.get(p["nearest_transect_id"])
        if not tf:
            continue
        positions = {int(y): v for y, v in tf["properties"]["positions"].items()}
        resp = level_response(positions, levels)
        if resp is None:
            results[p["object_id"]] = {"available": False}
            continue
        position_crit = positions.get(max(positions), p["distance_to_shore_2026_m"])
        crit_level = critical_level_for(resp, position_crit)
        current_level = levels[max(levels)]
        results[p["object_id"]] = {
            "available": True,
            "current_level_m": current_level,
            "critical_level_m": crit_level,
            "margin_m": round(current_level - crit_level, 2),
            "sensitivity_m_per_m": resp["slope_m_per_m"],
            "r_squared": resp["r_squared"],
        }

    out_path = REPO_ROOT / args.out
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: критический уровень посчитан для {sum(1 for r in results.values() if r['available'])}/"
          f"{len(results)} объектов -> {out_path}")


if __name__ == "__main__":
    main()
