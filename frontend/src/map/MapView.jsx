import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useAppStore } from "../store/useAppStore";

const RISK_COLORS = { high: "#dc2626", medium: "#d97706", low: "#16a34a" };
const CATEGORY_COLORS = {
  water_supply: "#dc2626", energy: "#ea580c", port: "#d97706",
  industry: "#65a30d", transport: "#0891b2", tourism: "#7c3aed", recreation: "#db2777",
};

export default function MapView() {
  const mapElRef = useRef(null);
  const mapRef = useRef(null);
  const shorelineLayerRef = useRef(null);
  const transectLayerRef = useRef(null);
  const objectLayerRef = useRef(null);
  const dustLayerRef = useRef(null);
  const seabedLayerRef = useRef(null);
  const beforeLayerRef = useRef(null);

  const currentYear = useAppStore((s) => s.currentYear);
  const shorelines = useAppStore((s) => s.shorelines);
  const transects = useAppStore((s) => s.transects);
  const objects = useAppStore((s) => s.objects);
  const dustZones = useAppStore((s) => s.dustZones);
  const exposedSeabed = useAppStore((s) => s.exposedSeabed);
  const showDust = useAppStore((s) => s.showDust);
  const showSeabed = useAppStore((s) => s.showSeabed);
  const showTransects = useAppStore((s) => s.showTransects);
  const showBeforeAfter = useAppStore((s) => s.showBeforeAfter);
  const beforeAfterSplit = useAppStore((s) => s.beforeAfterSplit);
  const setBeforeAfterSplit = useAppStore((s) => s.setBeforeAfterSplit);
  const selectObject = useAppStore((s) => s.selectObject);

  useEffect(() => {
    if (mapRef.current) return;
    const map = L.map(mapElRef.current, {
      preferCanvas: true,
      center: [43.65, 51.2],
      zoom: 10,
      minZoom: 7,
      maxZoom: 19,
    });

    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      {
        maxZoom: 19,
        attribution: "Tiles &copy; Esri — Source: Esri, Maxar, Earthstar Geographics",
      }
    ).addTo(map);

    const beforePane = map.createPane("before2000");
    beforePane.style.zIndex = 450; // Поднимаем zIndex выше основного слоя, но ниже маркеров

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Береговая линия текущего года
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const fc = shorelines[String(currentYear)] || shorelines[currentYear];
    if (shorelineLayerRef.current) {
      map.removeLayer(shorelineLayerRef.current);
      shorelineLayerRef.current = null;
    }
    if (!fc) return;
    const layer = L.geoJSON(fc, { style: { color: "#0ea5e9", weight: 3 } }).addTo(map);
    shorelineLayerRef.current = layer;
  }, [currentYear, shorelines]);

  // Трансекты
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (transectLayerRef.current) {
      map.removeLayer(transectLayerRef.current);
      transectLayerRef.current = null;
    }
    if (!transects || !showTransects) return;
    const layer = L.geoJSON(transects, {
      style: (f) => ({
        color: RISK_COLORS[f.properties.risk_class] || "#94a3b8",
        weight: 1.5,
        opacity: f.properties.confidence === "low" ? 0.35 : 0.8,
      }),
    }).addTo(map);
    transectLayerRef.current = layer;
  }, [transects, showTransects]);

  // Объекты
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (objectLayerRef.current) {
      map.removeLayer(objectLayerRef.current);
      objectLayerRef.current = null;
    }
    if (!objects) return;
    const layer = L.geoJSON(objects, {
      pointToLayer: (feature, latlng) =>
        L.circleMarker(latlng, {
          radius: 7,
          fillColor: CATEGORY_COLORS[feature.properties.category] || "#334155",
          color: "#0f172a",
          weight: 1,
          fillOpacity: 0.9,
        }),
      onEachFeature: (feature, lyr) => {
        lyr.on("click", () => selectObject(feature.properties.object_id));
        lyr.bindTooltip(feature.properties.name_ru);
      },
    }).addTo(map);
    objectLayerRef.current = layer;
  }, [objects, selectObject]);

  // Пылевые зоны
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (dustLayerRef.current) {
      map.removeLayer(dustLayerRef.current);
      dustLayerRef.current = null;
    }
    if (!dustZones || !showDust) return;
    const layer = L.geoJSON(dustZones, {
      style: { color: "#b45309", weight: 1, fillOpacity: 0.25 },
    }).addTo(map);
    dustLayerRef.current = layer;
  }, [dustZones, showDust]);

  // Осушенное дно
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (seabedLayerRef.current) {
      map.removeLayer(seabedLayerRef.current);
      seabedLayerRef.current = null;
    }
    if (!exposedSeabed || !showSeabed) return;
    const layer = L.geoJSON(exposedSeabed, {
      style: { color: "#a16207", weight: 1, fillColor: "#fde68a", fillOpacity: 0.4 },
    }).addTo(map);
    seabedLayerRef.current = layer;
  }, [exposedSeabed, showSeabed]);

  // Векторный слой 2000 года для режима «Было/Стало»
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (beforeLayerRef.current) {
      map.removeLayer(beforeLayerRef.current);
      beforeLayerRef.current = null;
    }
    if (!showBeforeAfter) return;

    const fc2000 = shorelines["2000"] || shorelines[2000];
    if (!fc2000) return;

    const layer = L.geoJSON(fc2000, {
      pane: "before2000",
      style: { color: "#ef4444", weight: 4.5, dashArray: "6, 6" },
    }).addTo(map);

    beforeLayerRef.current = layer;
    return () => {
      if (beforeLayerRef.current) {
        map.removeLayer(beforeLayerRef.current);
        beforeLayerRef.current = null;
      }
    };
  }, [showBeforeAfter, shorelines]);

  // Динамическая обрезка слоя 2000 года по позиции ползунка
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !showBeforeAfter) return;
    const pane = map.getPane("before2000");
    if (pane) {
      const rightCut = 100 - beforeAfterSplit;
      pane.style.clipPath = `inset(0 ${rightCut}% 0 0)`;
      pane.style.webkitClipPath = `inset(0 ${rightCut}% 0 0)`;
    }
  }, [showBeforeAfter, beforeAfterSplit]);

  return (
    <div className="map-view-wrap" style={{ position: "relative", width: "100%", height: "100%", overflow: "hidden" }}>
      <div ref={mapElRef} className="map-view" style={{ width: "100%", height: "100%" }} />
      {showBeforeAfter && (
  <div style={{ position: "absolute", inset: 0, pointerEvents: "none", zIndex: 1000 }}>
    {/* Красная разделительная черта */}
    <div
      style={{
        position: "absolute",
        top: 0,
        bottom: 0,
        left: `${beforeAfterSplit}%`,
        width: "2px",
        backgroundColor: "#ef4444",
        boxShadow: "0 0 10px rgba(239, 68, 68, 0.9)",
      }}
    />

    {/* Кнопка-слайдер по центру линии */}
    <div
      style={{
        position: "absolute",
        top: "50%",
        left: `${beforeAfterSplit}%`,
        transform: "translate(-50%, -50%)",
        width: "32px",
        height: "32px",
        borderRadius: "50%",
        backgroundColor: "#1e293b",
        border: "2px solid #ef4444",
        color: "#fff",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "12px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.5)",
      }}
    >
      ↔
    </div>

    {/* Узкий интерактивный ползунок по центру линии — не блокирует клики по карте! */}
    <input
      type="range"
      min={0}
      max={100}
      value={beforeAfterSplit}
      onChange={(e) => setBeforeAfterSplit(Number(e.target.value))}
      style={{
        position: "absolute",
        top: 0,
        left: `calc(${beforeAfterSplit}% - 20px)`,
        width: "40px",
        height: "100%",
        opacity: 0,
        cursor: "ew-resize",
        pointerEvents: "auto",
        margin: 0,
      }}
    />
  </div>
)}
    </div>
  );
}