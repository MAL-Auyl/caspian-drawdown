import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAppStore } from "../../store/useAppStore";
import { t } from "../../i18n/translations";
import Section from "./components/Section";
import Card, { CardGrid } from "./components/Card";
import FlowDiagram from "./components/FlowDiagram";
import RoadmapTimeline from "./components/RoadmapTimeline";
import "./about.css";

const TECH_KEYS = ["gee", "fastapi", "react", "leaflet", "python", "geojson", "sqlite", "osm"];
const TECH_ICONS = { gee: "🛰️", fastapi: "⚡", react: "⚛️", leaflet: "🗺️", python: "🐍", geojson: "📐", sqlite: "🗄️", osm: "🌍" };

const SOURCE_KEYS = ["landsat", "sentinel", "jrc", "osm", "meteo", "dsas"];
const SOURCE_ICONS = { landsat: "🛰️", sentinel: "🛰️", jrc: "🌊", osm: "🗺️", meteo: "🌬️", dsas: "📏" };

const ACCURACY_KEYS = ["open", "transparent", "scientific", "repro"];

const FEATURE_KEYS = ["timeline", "risk", "heatmap", "analysis", "offline", "pdf", "citizen"];
const FEATURE_ICONS = { timeline: "📅", risk: "🏗️", heatmap: "🔥", analysis: "📊", offline: "📡", pdf: "📄", citizen: "📢" };

const ROAD_KEYS = [
  { key: "heatmap", year: "2026" },
  { key: "forecast", year: "2026" },
  { key: "notify", year: "2027" },
  { key: "twin", year: "2027" },
  { key: "mobile", year: "2027" },
];

export default function AboutPage() {
  const lang = useAppStore((s) => s.lang);
  const setLang = useAppStore((s) => s.setLang);

  return (
    <div className="about-page">
      <nav className="about-nav">
        <Link to="/" className="about-nav-brand">Caspian Pulse</Link>
        <div className="about-nav-right">
          <select value={lang} onChange={(e) => setLang(e.target.value)} className="about-lang-select">
            <option value="ru">Русский</option>
            <option value="kk">Қазақша</option>
            <option value="en">English</option>
          </select>
          <Link to="/" className="about-nav-cta">{t(lang, "about_nav_explore")}</Link>
        </div>
      </nav>

      {/* Hero */}
      <header className="about-hero">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        >
          <span className="about-eyebrow">{t(lang, "about_eyebrow")}</span>
          <h1 className="about-hero-title">Caspian Pulse</h1>
          <p className="about-hero-lead">{t(lang, "about_hero_lead")}</p>
          <p className="about-hero-sub">{t(lang, "about_hero_sub")}</p>
          <div className="about-hero-actions">
            <Link to="/" className="about-btn about-btn-primary">{t(lang, "about_btn_explore")}</Link>
            <a
              href="https://github.com/MAL-Auyl/caspian-drawdown"
              target="_blank"
              rel="noreferrer"
              className="about-btn about-btn-ghost"
            >
              {t(lang, "about_btn_github")}
            </a>
          </div>
        </motion.div>
        <div className="about-hero-glow" aria-hidden />
      </header>

      {/* Mission */}
      <Section kicker={t(lang, "about_mission_kicker")} title={t(lang, "about_mission_title")}>
        <p className="about-lead-text">{t(lang, "about_mission_lead")}</p>
        <p className="about-body-text">{t(lang, "about_mission_body")}</p>
      </Section>

      {/* How it works */}
      <Section kicker={t(lang, "about_pipeline_kicker")} title={t(lang, "about_pipeline_title")} className="about-section-alt">
        <FlowDiagram
          steps={[
            t(lang, "about_step_satellite"), t(lang, "about_step_gee"), t(lang, "about_step_water"),
            t(lang, "about_step_shoreline"), t(lang, "about_step_transect"), t(lang, "about_step_risk"),
            t(lang, "about_step_dashboard"), t(lang, "about_step_reports"),
          ]}
        />
      </Section>

      {/* Technologies */}
      <Section kicker={t(lang, "about_tech_kicker")} title={t(lang, "about_tech_title")}>
        <CardGrid>
          {TECH_KEYS.map((key) => (
            <Card key={key} icon={TECH_ICONS[key]} title={t(lang, `about_tech_${key}_title`)}>
              {t(lang, `about_tech_${key}_desc`)}
            </Card>
          ))}
        </CardGrid>
      </Section>

      {/* Data Sources */}
      <Section kicker={t(lang, "about_sources_kicker")} title={t(lang, "about_sources_title")} className="about-section-alt">
        <CardGrid>
          {SOURCE_KEYS.map((key) => (
            <Card key={key} icon={SOURCE_ICONS[key]} title={t(lang, `about_src_${key}_title`)}>
              {t(lang, `about_src_${key}_desc`)}
            </Card>
          ))}
        </CardGrid>
      </Section>

      {/* Why shorelines look irregular */}
      <Section kicker={t(lang, "about_shoreline_kicker")} title={t(lang, "about_shoreline_title")}>
        <div className="about-split">
          <div>
            <p className="about-body-text">{t(lang, "about_shoreline_p1")}</p>
            <p className="about-body-text">{t(lang, "about_shoreline_p2")}</p>
            <p className="about-body-text">{t(lang, "about_shoreline_p3")}</p>
          </div>
          <FlowDiagram
            steps={[
              t(lang, "about_step_pixels"), t(lang, "about_step_classification"),
              t(lang, "about_step_extracted"), t(lang, "about_step_real"),
            ]}
          />
        </div>
      </Section>

      {/* Heat Map */}
      <Section kicker={t(lang, "about_heat_kicker")} title={t(lang, "about_heat_title")} className="about-section-alt">
        <p className="about-body-text">{t(lang, "about_heat_body")}</p>
        <div className="heat-legend">
          <div className="heat-legend-row"><span className="heat-dot heat-low" />{t(lang, "heat_low")}</div>
          <div className="heat-legend-row"><span className="heat-dot heat-medium" />{t(lang, "heat_medium")}</div>
          <div className="heat-legend-row"><span className="heat-dot heat-high" />{t(lang, "heat_high")}</div>
          <div className="heat-legend-row"><span className="heat-dot heat-critical" />{t(lang, "heat_critical")}</div>
        </div>
      </Section>

      {/* AI Analysis */}
      <Section kicker={t(lang, "about_ai_kicker")} title={t(lang, "about_ai_title")}>
        <p className="about-body-text">{t(lang, "about_ai_body1")}</p>
        <p className="about-body-text about-emphasis">{t(lang, "about_ai_body2")}</p>
      </Section>

      {/* Why GEE */}
      <Section kicker={t(lang, "about_gee_kicker")} title={t(lang, "about_gee_title")} className="about-section-alt">
        <p className="about-body-text">{t(lang, "about_gee_body1")}</p>
        <p className="about-body-text">{t(lang, "about_gee_body2")}</p>
      </Section>

      {/* Accuracy */}
      <Section kicker={t(lang, "about_accuracy_kicker")} title={t(lang, "about_accuracy_title")}>
        <CardGrid columns={4}>
          {ACCURACY_KEYS.map((key) => (
            <Card key={key} icon="✔" title={t(lang, `about_acc_${key}_title`)}>
              {t(lang, `about_acc_${key}_desc`)}
            </Card>
          ))}
        </CardGrid>
      </Section>

      {/* Architecture */}
      <Section kicker={t(lang, "about_arch_kicker")} title={t(lang, "about_arch_title")} className="about-section-alt">
        <FlowDiagram
          steps={[
            t(lang, "about_arch_frontend"), t(lang, "about_arch_api"), t(lang, "about_arch_pipeline"),
            t(lang, "about_step_gee"), t(lang, "about_step_satellite"),
          ]}
        />
      </Section>

      {/* Features */}
      <Section kicker={t(lang, "about_features_kicker")} title={t(lang, "about_features_title")}>
        <CardGrid>
          {FEATURE_KEYS.map((key) => (
            <Card key={key} icon={FEATURE_ICONS[key]} title={t(lang, `about_feat_${key}_title`)}>
              {t(lang, `about_feat_${key}_desc`)}
            </Card>
          ))}
        </CardGrid>
      </Section>

      {/* Roadmap */}
      <Section kicker={t(lang, "about_roadmap_kicker")} title={t(lang, "about_roadmap_title")} className="about-section-alt">
        <RoadmapTimeline items={ROAD_KEYS.map((r) => ({ year: r.year, label: t(lang, `about_road_${r.key}`) }))} />
      </Section>

      <footer className="about-footer">
        <div className="about-footer-links">
          <span>{t(lang, "about_footer_opendata")}</span>
          <a href="https://earthengine.google.com/" target="_blank" rel="noreferrer">Google Earth Engine</a>
          <a href="https://www.openstreetmap.org/" target="_blank" rel="noreferrer">OpenStreetMap</a>
          <a href="https://www.esa.int/" target="_blank" rel="noreferrer">ESA</a>
          <a href="https://www.usgs.gov/" target="_blank" rel="noreferrer">USGS</a>
        </div>
        <p>{t(lang, "about_footer_built")}</p>
      </footer>
    </div>
  );
}
