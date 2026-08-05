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

  const currentYear = useAppStore((s) => s.currentYear);
  const shorelines = useAppStore((s) => s.shorelines);
  const transects = useAppStore((s) => s.transects);
  const objects = useAppStore((s) => s.objects);
  const dustZones = useAppStore((s) => s.dustZones);
  const exposedSeabed = useAppStore((s) => s.exposedSeabed);
  const showDust = useAppStore((s) => s.showDust);
  const showSeabed = useAppStore((s) => s.showSeabed);
  const showTransects = useAppStore((s) => s.showTransects);
  const selectObject = useAppStore((s) => s.selectObject);

  useEffect(() => {
    if (mapRef.current) return;
    const map = L.map(mapElRef.current, {
      preferCanvas: true,
      center: [43.65, 51.2],
      zoom: 10,
      minZoom: 7,
      maxZoom: 14,
    });
    L.tileLayer("/tiles/{z}/{x}/{y}.png", {
      maxZoom: 14,
      maxNativeZoom: 11, // тайлы скачаны только до 11 зума — дальше Leaflet
      // растягивает имеющиеся, вместо того чтобы запрашивать несуществующие
      errorTileUrl: "",
      attribution: "Caspian Pulse — локальные тайлы",
    }).addTo(map);
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Береговая линия текущего года — старый слой снимается ДО добавления нового,
  // иначе Leaflet копит слои в DOM (грабля #5).
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

  return <div ref={mapElRef} className="map-view" />;
}
