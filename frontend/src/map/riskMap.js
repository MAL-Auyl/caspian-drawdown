import L from "leaflet";

// Цветовая шкала Heat Map (риск отступления берега) — отдельная от
// RISK_COLORS в MapView.jsx (та красит слой "Трансекты" по risk_class
// из бэкенда и её трогать не нужно).
export const HEAT_COLORS = { low: "#00C853", medium: "#FFD600", high: "#FF6D00", critical: "#D50000" };
export const HEAT_WEIGHTS = { low: 4, medium: 4.7, high: 5.3, critical: 6 };
export const NEAR_OBJECT_RADIUS_M = 3000;

// Отступление трансекта к currentYear — берём только уже посчитанные
// пайплайном точки positions_clean (без интерполяции и новых измерений),
// сравниваем первую и последнюю валидную точку в пределах currentYear.
function retreatAtYear(feature, currentYear) {
  const positions = feature.properties.positions_clean || feature.properties.positions;
  if (!positions) return null;
  const entries = Object.entries(positions)
    .map(([year, value]) => [Number(year), value])
    .filter(([year, value]) => year <= currentYear && value != null)
    .sort((a, b) => a[0] - b[0]);
  if (entries.length < 2) return null;
  const [firstYear, firstValue] = entries[0];
  const [lastYear, lastValue] = entries[entries.length - 1];
  const retreatM = Math.abs(lastValue - firstValue);
  const years = lastYear - firstYear;
  return { retreatM, rateM: years > 0 ? retreatM / years : 0 };
}

// risk_score в данных трансектов отсутствует, поэтому нормализуем
// retreat_rate по всем трансектам с валидными данными на currentYear
// и делим на 4 равных диапазона (0-25 / 25-50 / 50-75 / 75-100%).
export function buildHeatMapData(transects, currentYear) {
  if (!transects?.features) return null;

  const withMetrics = transects.features
    .map((feature) => ({ feature, metrics: retreatAtYear(feature, currentYear) }))
    .filter((x) => x.metrics);

  if (!withMetrics.length) return { type: "FeatureCollection", features: [] };

  const rates = withMetrics.map((x) => x.metrics.rateM);
  const min = Math.min(...rates);
  const max = Math.max(...rates);
  const range = max - min || 1;

  const features = withMetrics.map(({ feature, metrics }) => {
    const normalized = (metrics.rateM - min) / range;
    const level =
      normalized <= 0.25 ? "low" : normalized <= 0.5 ? "medium" : normalized <= 0.75 ? "high" : "critical";
    return {
      ...feature,
      properties: {
        ...feature.properties,
        retreat_m: Math.round(metrics.retreatM * 10) / 10,
        retreat_rate: Math.round(metrics.rateM * 100) / 100,
        risk_level: level,
        risk_color: HEAT_COLORS[level],
        risk_weight: HEAT_WEIGHTS[level],
      },
    };
  });

  return { type: "FeatureCollection", features };
}

export function isNearPoint(feature, point) {
  if (!point) return false;
  return feature.geometry.coordinates.some(
    ([lng, lat]) => L.CRS.Earth.distance(point, L.latLng(lat, lng)) <= NEAR_OBJECT_RADIUS_M
  );
}
