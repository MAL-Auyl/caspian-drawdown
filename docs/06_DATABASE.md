# 06 — Модель данных

Статические GeoJSON/JSON в `data/processed/` (см. `docs/00_DECISIONS.md`
про выбор в пользу файлов, а не PostGIS) + SQLite для гражданских заявок.

```
data/processed/
├── shorelines/shoreline_YYYY.geojson   # LineString, 1 файл на год (нет для 2012)
├── transects.geojson                    # ~450–540 сегментов
├── objects.geojson                      # 8 объектов инфраструктуры
├── dust_zones.geojson
├── exposed_seabed.geojson
├── statistics.json
└── meta.json
backend/storage/reports.db               # SQLite, гражданские заявки
```

## `transects.geojson` — свойства фичи

| Поле | Тип | Описание |
|---|---|---|
| `transect_id` | int | Номер вдоль берега |
| `baseline_distance_m` | float | Позиция вдоль baseline |
| `positions` | dict | `{"2000": 12480.5, ..., "2012": null, ...}` — явный `null`, не пропуск ключа |
| `speed_m_per_year` | float | Наклон регрессии; отрицательное = отступление |
| `r_squared`, `std_error`, `ci_95_low`, `ci_95_high` | float | Качество регрессии |
| `valid_years` | int | Число ненулевых наблюдений |
| `confidence` | enum | `high` \| `medium` \| `low` |
| `risk_class` | enum | по скорости: `high` (≤ −20 м/год), `medium` (≤ −8), `low` |

## `objects.geojson` — свойства фичи

`object_id`, `name_ru/kk/en`, `category`, `criticality` (1–10),
`nearest_transect_id`, `distance_to_shore_*_m`, `speed_m_per_year`,
`risk_score` (0–100), `risk_level`, `risk_components` (разложение по
формуле из `08_AI_ANALYTICS.md`), `forecast` (три сценария),
`description_*`, `recommendation_*`.

Справочник категорий (`pipeline/gee/config.py::CATEGORY_CRITICALITY`):

| category | базовая критичность | критическое расстояние, м |
|---|---|---|
| water_supply | 10 | 300 |
| energy | 9 | 400 |
| port | 8 | 200 |
| industry | 6 | 500 |
| transport | 5 | 150 |
| tourism | 4 | 100 |
| recreation | 3 | 100 |

## SQLite — `citizen_reports`

```sql
CREATE TABLE citizen_reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    contact TEXT,
    nearest_transect_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    ip_hash TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
);
```

IP хранится только как соль+хеш (`backend/app/services/reports_db.py`) —
для лимита частоты (5/час), не для идентификации. Персональные данные не
собираются; `contact` опционален.

## Загрузка в память

`backend/app/services/store.py::DataStore.load()` читает все файлы один раз
при старте FastAPI (`lifespan`). Эндпоинты — это фильтрация уже загруженного,
без файлового I/O на каждый запрос.
