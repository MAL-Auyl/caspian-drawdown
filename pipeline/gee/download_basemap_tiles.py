"""Скачивает офлайн-тайлы подложки карты — реальный композит Sentinel-2
(тот же снимок, что использует пайплайн для измерений) через
ee.Image.getMapId(), сохраняет как статические PNG в frontend/public/tiles/.

Своя, а не сторонняя подложка: используется уже авторизованный GEE-аккаунт,
а не внешний тайл-сервис. Офлайн-режим требует локальных файлов — живой
GEE-тайл-URL по токену не подходит для демо без интернета
(см. docs/00_DECISIONS.md).

Запуск:
    python3 -m pipeline.gee.download_basemap_tiles --zoom-min 8 --zoom-max 12
"""
import argparse
import math
import time
from pathlib import Path

import ee
import requests

from pipeline.gee import config as cfg
from pipeline.gee.composite import build_year_composite

REPO_ROOT = Path(__file__).resolve().parents[2]


def deg2tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def tile_range(zoom: int):
    lon0, lat0 = cfg.AOI_MANGYSTAU["coordinates"][0][0]
    lon1, lat1 = cfg.AOI_MANGYSTAU["coordinates"][0][2]
    x0, y0 = deg2tile(lat1, lon0, zoom)  # северо-запад
    x1, y1 = deg2tile(lat0, lon1, zoom)  # юго-восток
    return range(min(x0, x1), max(x0, x1) + 1), range(min(y0, y1), max(y0, y1) + 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zoom-min", type=int, default=8)
    parser.add_argument("--zoom-max", type=int, default=12)
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--project", default="caspian-pulse-ee")
    parser.add_argument("--out", default="frontend/public/tiles")
    args = parser.parse_args()

    ee.Initialize(project=args.project)
    aoi = ee.Geometry.Rectangle([
        cfg.AOI_MANGYSTAU["coordinates"][0][0][0], cfg.AOI_MANGYSTAU["coordinates"][0][0][1],
        cfg.AOI_MANGYSTAU["coordinates"][0][2][0], cfg.AOI_MANGYSTAU["coordinates"][0][2][1],
    ])
    composite, coll_id, n_scenes, window = build_year_composite(args.year, aoi)
    print(f"Композит: {coll_id}, {n_scenes} сцен, окно {window}")

    # Истинный цвет: разные спутники — разные номера каналов под red/green/blue.
    rgb_bands = {
        "LANDSAT/LT05/C02/T1_L2": ["SR_B3", "SR_B2", "SR_B1"],
        "LANDSAT/LE07/C02/T1_L2": ["SR_B3", "SR_B2", "SR_B1"],
        "LANDSAT/LC08/C02/T1_L2": ["SR_B4", "SR_B3", "SR_B2"],
        "LANDSAT/LC09/C02/T1_L2": ["SR_B4", "SR_B3", "SR_B2"],
        "COPERNICUS/S2_SR_HARMONIZED": ["B4", "B3", "B2"],
    }[coll_id]
    vis = composite.select(rgb_bands).visualize(min=0.0, max=0.3, gamma=1.2)
    map_id = vis.getMapId()
    url_format = map_id["tile_fetcher"].url_format
    print(f"Tile URL: {url_format}")

    out_dir = REPO_ROOT / args.out
    session = requests.Session()
    total, saved, failed = 0, 0, 0

    for zoom in range(args.zoom_min, args.zoom_max + 1):
        xs, ys = tile_range(zoom)
        print(f"zoom {zoom}: {len(xs)}x{len(ys)} = {len(xs)*len(ys)} тайлов")
        for x in xs:
            for y in ys:
                total += 1
                dest = out_dir / str(zoom) / str(x)
                dest.mkdir(parents=True, exist_ok=True)
                fpath = dest / f"{y}.png"
                if fpath.exists():
                    saved += 1
                    continue
                url = url_format.format(z=zoom, x=x, y=y)
                for attempt in range(3):
                    try:
                        r = session.get(url, timeout=20)
                        if r.status_code == 200:
                            fpath.write_bytes(r.content)
                            saved += 1
                            break
                        time.sleep(1)
                    except requests.RequestException:
                        time.sleep(1)
                else:
                    failed += 1

    print(f"\nГотово: {saved}/{total} тайлов сохранено в {out_dir}, {failed} ошибок")


if __name__ == "__main__":
    main()
