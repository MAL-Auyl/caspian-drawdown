"""Загрузка предрасчитанных GeoJSON/JSON в память при старте.

Никаких пространственных запросов в рантайме — только фильтрация того,
что уже посчитал пайплайн. См. ADR в docs/00_DECISIONS.md.
"""
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "processed"


class DataStore:
    def __init__(self, base: Path = DEFAULT_DATA_DIR):
        self.base = Path(base)
        self.shorelines: dict[int, dict] = {}
        self.transects: dict | None = None
        self.objects: dict | None = None
        self.dust: dict | None = None
        self.seabed: dict | None = None
        self.stats: dict | None = None
        self.meta: dict | None = None
        self.is_loaded = False

    def load(self) -> None:
        shoreline_dir = self.base / "shorelines"
        for p in sorted(shoreline_dir.glob("shoreline_*.geojson")):
            year = int(p.stem.split("_")[1])
            self.shorelines[year] = json.loads(p.read_text(encoding="utf-8"))

        self.transects = self._read("transects.geojson")
        self.objects = self._read("objects.geojson")
        self.dust = self._read("dust_zones.geojson")
        self.seabed = self._read("exposed_seabed.geojson")
        self.stats = self._read("statistics.json")
        self.meta = self._read("meta.json")
        self.is_loaded = True

    def _read(self, name: str):
        p = self.base / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def object_by_id(self, oid: int):
        if not self.objects:
            return None
        return next((f for f in self.objects["features"]
                     if f["properties"]["object_id"] == oid), None)

    def transect_by_id(self, tid: int):
        if not self.transects:
            return None
        return next((f for f in self.transects["features"]
                     if f["properties"]["transect_id"] == tid), None)

    def nearest_transect(self, lon: float, lat: float):
        if not self.transects:
            return None
        best, best_d = None, math.inf
        for f in self.transects["features"]:
            anchor = f["properties"].get("anchor")
            if not anchor:
                anchor = f["geometry"]["coordinates"][0]
            d = math.hypot(anchor[0] - lon, anchor[1] - lat)
            if d < best_d:
                best, best_d = f, d
        return best

    def available_years(self) -> list[int]:
        return sorted(self.shorelines.keys())


store = DataStore()
