# 05 — API

Base URL: `/api/v1`. FastAPI, Swagger на `/docs`. Все данные читаются из
`data/processed/` в память при старте (`backend/app/services/store.py`) —
во время запроса ничего не вычисляется, только фильтрация.

## Эндпоинты

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/health` | Проверка живости, флаг загрузки данных |
| GET | `/meta` | Версия данных, методология, источники, лицензии |
| GET | `/bootstrap` | Всё для старта фронтенда одним ответом (gzip) |
| GET | `/shorelines` | Список лет с метаданными снимка (сенсор, облачность, качество) |
| GET | `/shorelines/{year}` | Линия берега за год; 404 `YEAR_NOT_AVAILABLE` для 2012 |
| GET | `/transects` | Все сегменты; фильтры `confidence`, `min_speed`, `max_speed` |
| GET | `/transects/{id}` | Полный ряд позиций по годам + регрессия для графика |
| GET | `/objects` | Все объекты инфраструктуры |
| GET | `/objects/{id}` | Карточка объекта: расстояния, риск, прогноз, рекомендация |
| GET | `/objects/{id}/risk` | Разложение оценки риска по компонентам |
| GET | `/objects/{id}/forecast` | Три сценария (optimistic/baseline/pessimistic) |
| GET | `/statistics` | Агрегаты: средняя скорость, топ-сегменты, риск по объектам |
| GET | `/dust` | Зоны пылевого риска (индикативная модель) |
| GET | `/exposed-seabed` | Полигон осушенного дна |
| GET | `/reports` | Список гражданских заявок |
| POST | `/reports` | Приём заявки (201), лимит 5/час по IP-хешу |

## Формат ошибок

```json
{ "detail": "человекочитаемое описание", "code": "MACHINE_CODE" }
```

`YEAR_NOT_AVAILABLE` (404), `OBJECT_NOT_FOUND` (404), `TRANSECT_NOT_FOUND`
(404), `OUT_OF_AOI` (400), `RATE_LIMITED` (429).

## `POST /reports`

```json
{
  "latitude": 43.641, "longitude": 51.192,
  "category": "shoreline_change",
  "description": "Вода отошла от старого причала примерно на 50 метров",
  "contact": null
}
```

`category`: `shoreline_change` | `pollution` | `dust_storm` | `infrastructure` | `other`.
Координаты проверяются на попадание в AOI Мангистау, описание — 10–1000
символов. Ответ 201 содержит `nearest_transect_id`, найденный по ближайшему
якорю трансекты.
