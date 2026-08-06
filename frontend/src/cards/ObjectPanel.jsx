import { useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { t } from "../i18n/translations";

const RISK_LABEL = { high: "высокий", medium: "средний", low: "низкий" };

const SCENARIOS = [
  { key: "optimistic", label: "Оптимистичный" },
  { key: "baseline", label: "Базовый" },
  { key: "pessimistic", label: "Пессимистичный" },
];

function ObjectListItem({ feature, active, onSelect }) {
  const p = feature.properties;
  return (
    <li className={`object-item risk-${p.risk_level} ${active ? "active" : ""}`} onClick={() => onSelect(p.object_id)}>
      <span className="object-name">{p.name_ru}</span>
      <span className="object-risk-badge">{p.risk_score}</span>
    </li>
  );
}

function ScenarioForecast({ forecast }) {
  const [scenario, setScenario] = useState("baseline");
  const values = forecast[scenario];

  return (
    <div className="scenario-block">
      <div className="scenario-toggle">
        {SCENARIOS.map((s) => (
          <button
            key={s.key}
            className={scenario === s.key ? "active" : ""}
            onClick={() => setScenario(s.key)}
          >
            {s.label}
          </button>
        ))}
      </div>
      <dl className="object-metrics">
        <dt>2030</dt>
        <dd>{values["2030"]} м</dd>
        <dt>2035</dt>
        <dd>{values["2035"]} м</dd>
        <dt>2040</dt>
        <dd>{values["2040"]} м</dd>
      </dl>
    </div>
  );
}

function ObjectDetail({ feature, lang }) {
  const p = feature.properties;
  const nameField = `name_${lang}`;
  const descField = `description_${lang}`;
  return (
    <div className="object-detail">
      <h3>{p[nameField] || p.name_ru}</h3>
      <p className="object-description">{p[descField] || p.description_ru}</p>
      <dl className="object-metrics">
        <dt>{t(lang, "riskScore")}</dt>
        <dd>{p.risk_score} ({RISK_LABEL[p.risk_level]})</dd>
        <dt>{t(lang, "speed")}</dt>
        <dd>{p.speed_m_per_year} м/год</dd>
        <dt>{t(lang, "distance")} (2000 → 2026)</dt>
        <dd>{p.distance_to_shore_2000_m} м → {p.distance_to_shore_2026_m} м</dd>
      </dl>
      <h4 className="scenario-heading">{t(lang, "forecast")} — расстояние до воды, м</h4>
      <ScenarioForecast forecast={p.forecast} />
      {p.recommendation_ru && (
        <p className="object-recommendation">{p.recommendation_ru}</p>
      )}
    </div>
  );
}

export default function ObjectPanel() {
  const objects = useAppStore((s) => s.objects);
  const selectedObjectId = useAppStore((s) => s.selectedObjectId);
  const selectObject = useAppStore((s) => s.selectObject);
  const lang = useAppStore((s) => s.lang);

  if (!objects) return null;
  const features = [...objects.features].sort((a, b) => b.properties.risk_score - a.properties.risk_score);
  const selected = features.find((f) => f.properties.object_id === selectedObjectId) || features[0];

  return (
    <div className="object-panel">
      <h2>{t(lang, "objects")}</h2>
      <ul className="object-list">
        {features.map((f) => (
          <ObjectListItem
            key={f.properties.object_id}
            feature={f}
            active={f.properties.object_id === selected?.properties.object_id}
            onSelect={selectObject}
          />
        ))}
      </ul>
      {selected && <ObjectDetail feature={selected} lang={lang} key={selected.properties.object_id} />}
    </div>
  );
}
