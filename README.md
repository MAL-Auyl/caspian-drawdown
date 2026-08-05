# Caspian Pulse

Веб-платформа, которая по открытым спутниковым снимкам измеряет отступление
береговой линии Каспия у берегов Мангистау за 2000–2026 годы и связывает его
с критической инфраструктурой (в первую очередь — водозаборным каналом МАЭК,
источником питьевой воды Актау).

**Caspian Hackathon 2026** · Актау, 10–11 августа · Rixos Water World Aktau

Репозиторий создан 5 августа 2026, после публикации ТЗ, с нуля — см.
[`docs/10_RULES_COMPLIANCE.md`](docs/10_RULES_COMPLIANCE.md).

---

## Структура

```
pipeline/   геообработка: конфиг, мок-генератор, извлечение береговой линии из
            Earth Engine (Landsat/Sentinel-2), трансекты DSAS, регрессии, риск
backend/    FastAPI — 15 GET + 1 POST эндпоинт, данные читаются из
            pipeline/data (памяти процесса), гражданские заявки — в SQLite
frontend/   Vite + React (JavaScript, без TypeScript) + Leaflet
data/       предрасчитанные GeoJSON/JSON, которые отдаёт backend
docs/       техническая документация проекта
```

## Технические решения

Полный список с обоснованием — [`docs/00_DECISIONS.md`](docs/00_DECISIONS.md).
Коротко: статические GeoJSON вместо PostGIS, Leaflet с `preferCanvas`,
локальные тайлы карты, EPSG:32639 для метрических расчётов, трансекты DSAS,
MNDWI + порог Оцу, только июльские снимки, линейная регрессия вместо нейросетей,
JavaScript вместо TypeScript, PDF собирается на фронтенде через снимок DOM.

## Быстрый старт

### 1. Мок-данные (не требует Earth Engine)

```bash
cd pipeline
pip install -r requirements.txt
cd ..
python3 -m pipeline.mock.generate --out data/processed --fallback frontend/public/fallback
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
# Swagger: http://localhost:8000/docs
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

Если backend недоступен, фронтенд сам переключается на
`frontend/public/fallback/bootstrap.json` — офлайн-режим для демо без сети.

## Деплой

### Backend — Render

Через Blueprint: New → Blueprint → указать этот репозиторий, Render сам
прочитает `render.yaml` из корня. Вручную — те же настройки:

| Параметр | Значение |
|---|---|
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

Free-тариф Render использует эфемерную файловую систему — `backend/storage/reports.db`
(гражданские заявки) не переживёт передеплой. Для демо это не критично;
для продакшна нужен постоянный диск или внешняя БД.

После деплоя backend будет на `https://<app-name>.onrender.com`. Swagger — `/docs`.

### Frontend — Vercel

Framework Preset определяется автоматически (Vite). Единственное, что нужно
задать вручную — переменную окружения:

| Переменная | Значение |
|---|---|
| `VITE_API_BASE` | `https://<app-name>.onrender.com/api/v1` |

Без этой переменной фронтенд не упадёт — он сам переключится на
`public/fallback/bootstrap.json` (см. `src/api/client.js`), просто данные
будут не самые свежие. Root Directory в Vercel — `frontend`.

## API

Base URL: `/api/v1`. Полная спецификация — [`docs/05_API.md`](docs/05_API.md).

| Метод | Путь |
|---|---|
| GET | `/bootstrap`, `/health`, `/meta`, `/statistics`, `/dust`, `/exposed-seabed` |
| GET | `/shorelines`, `/shorelines/{year}` |
| GET | `/transects`, `/transects/{id}` |
| GET | `/objects`, `/objects/{id}`, `/objects/{id}/risk`, `/objects/{id}/forecast` |
| GET/POST | `/reports` |

## Источники данных и лицензии

| Источник | Провайдер | Лицензия |
|---|---|---|
| Landsat 5/7/8/9 Collection 2 L2 | USGS | Public Domain |
| Sentinel-2 MSI L2A | ESA Copernicus | Open |
| JRC Global Surface Water (Pekel et al., 2016, Nature) | EC Joint Research Centre | Open |
| Open-Meteo Historical Archive | Open-Meteo | CC BY 4.0 |
| OpenStreetMap | OSM Contributors | ODbL |
| Уровень Каспия: Hydroweb / DAHITI / G-REALM | LEGOS/CNES, TUM, USDA | Открытые данные |

Метод трансект: DSAS (Digital Shoreline Analysis System), опубликованная
методика USGS.

## Ограничения

Аналитический инструмент поддержки решений, не заменяет официальные
гидрографические и инженерные изыскания. Линейная регрессия — сценарная
экстраполяция наблюдаемого тренда, не гидродинамический прогноз.
