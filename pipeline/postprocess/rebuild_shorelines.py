"""Перестраивает shoreline_YYYY.geojson из уже собранных позиций трансект —
без повторного обращения к Earth Engine.

Грабля #5 (обнаружена после интеграции в веб): линия берега на карте
зигзагит. Причина — линия строилась из сырых точек пересечения по годам,
а не из отфильтрованных: Hampel-фильтр в pipeline/common/stats.py защищает
только регрессию скорости в transects.geojson, а не саму геометрию линии.
Здесь — тот же принцип, но по соседям ВДОЛЬ БЕРЕГА (не по годам для одной
трансекты): единичная трансекта с аномальным расстоянием на фоне соседей
сглаживается или отбрасывается.

Запуск:
    python3 -m pipeline.postprocess.rebuild_shorelines --in data/processed
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pyproj
from shapely.geometry import LineString, Point
from shapely.ops import transform

from pipeline.gee import config as cfg

REPO_ROOT = Path(__file__).resolve().parents[2]
_TO_METRIC = pyproj.Transformer.from_crs(cfg.CRS_OUTPUT, cfg.CRS_METRIC, always_xy=True).transform
_TO_OUTPUT = pyproj.Transformer.from_crs(cfg.CRS_METRIC, cfg.CRS_OUTPUT, always_xy=True).transform

WINDOW = 8
HAMPEL_K = 2.5
FLOOR_M = 400.0


def spatial_filter(ordered_distances: list[float], passes: int = 3) -> list[float | None]:
    """Точки, сильно отличающиеся от локальной медианы соседей вдоль берега,
    заменяются на None (пропуск в линии) вместо того, чтобы давать скачок.

    Несколько проходов подряд: если два-три плохих значения стоят рядом,
    за один проход локальная медиана окна сама смещена ими — и часть
    кластера проходит фильтр. Повторные проходы (уже без ранее отброшенных
    точек в окне) дочищают такие кластеры."""
    out: list[float | None] = list(ordered_distances)
    for _ in range(passes):
        changed = False
        current = list(out)
        for i in range(len(current)):
            if current[i] is None:
                continue
            lo, hi = max(0, i - WINDOW), min(len(current), i + WINDOW + 1)
            neighborhood = [current[j] for j in range(lo, hi) if j != i and current[j] is not None]
            if len(neighborhood) < 3:
                continue
            med = float(np.median(neighborhood))
            mad = float(np.median(np.abs(np.array(neighborhood) - med)))
            threshold = max(HAMPEL_K * 1.4826 * mad, FLOOR_M)
            if abs(current[i] - med) > threshold:
                out[i] = None
                changed = True
        if not changed:
            break
    return out


# Если между соседними реально измеренными точками пропущено больше этого
# числа трансект подряд (при шаге 500м это ~2.5км без единого детектированного
# пересечения хоть в один год), не соединяем их прямой хордой — честнее
# показать разрыв линии, чем нарисовать выдуманный отрезок через город
# (грабля #6: 18-километровая "диагональ через Актау" получалась именно так,
# когда весь портовый залив ни разу не дал ни одного валидного пересечения).
MAX_GAP_TRANSECTS = 5


def _split_on_gaps(valid_idx: list[int]) -> list[list[int]]:
    segments: list[list[int]] = []
    current: list[int] = []
    for i in valid_idx:
        if current and i - current[-1] > MAX_GAP_TRANSECTS:
            segments.append(current)
            current = []
        current.append(i)
    if current:
        segments.append(current)
    return segments


def rebuild(base: Path):
    transects = json.loads((base / "transects.geojson").read_text(encoding="utf-8"))["features"]
    transects.sort(key=lambda f: f["properties"]["transect_id"])

    metric_lines = [transform(_TO_METRIC, LineString(f["geometry"]["coordinates"])) for f in transects]
    years = [y for y in cfg.YEARS if y not in cfg.MISSING_YEARS]

    out_dir = base / "shorelines"
    out_dir.mkdir(parents=True, exist_ok=True)
    written, skipped = 0, 0

    for year in years:
        raw = [f["properties"]["positions"].get(str(year)) for f in transects]
        distances = [abs(v) if v is not None else None for v in raw]

        valid_idx = [i for i, d in enumerate(distances) if d is not None]
        if len(valid_idx) < 2:
            skipped += 1
            continue
        valid_distances = [distances[i] for i in valid_idx]
        filtered = spatial_filter(valid_distances)
        filtered_by_idx = dict(zip(valid_idx, filtered))
        kept_idx = [i for i in valid_idx if filtered_by_idx[i] is not None]

        segments_idx = _split_on_gaps(kept_idx)
        line_segments = []
        for seg in segments_idx:
            if len(seg) < 2:
                continue
            coords = []
            for idx in seg:
                pt_metric = metric_lines[idx].interpolate(filtered_by_idx[idx])
                coords.append(list(transform(_TO_OUTPUT, pt_metric).coords)[0])
            line_segments.append(coords)

        if not line_segments:
            skipped += 1
            continue

        n_removed = sum(1 for d in filtered if d is None)
        total_len_km = sum(LineString(c).length for c in line_segments) * 96
        geometry = (
            {"type": "LineString", "coordinates": line_segments[0]}
            if len(line_segments) == 1
            else {"type": "MultiLineString", "coordinates": line_segments}
        )
        fc = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": [{
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "year": year, "data_quality": "good",
                    "length_km": round(total_len_km, 1),
                    "spatial_outliers_removed": n_removed,
                    "n_segments": len(line_segments),
                },
            }],
        }
        (out_dir / f"shoreline_{year}.geojson").write_text(
            json.dumps(fc, ensure_ascii=False), encoding="utf-8")
        written += 1
        print(f"  {year}: {sum(len(s) for s in line_segments)} точек, {len(line_segments)} сегмент(ов), {n_removed} выбросов убрано")

    print(f"\nOK: {written} лет перестроено, {skipped} пропущено -> {out_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_dir", default="data/processed")
    args = parser.parse_args()
    rebuild(REPO_ROOT / args.in_dir)


if __name__ == "__main__":
    main()
