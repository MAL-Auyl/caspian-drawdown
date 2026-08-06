import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Section from "./components/Section";
import Card, { CardGrid } from "./components/Card";
import FlowDiagram from "./components/FlowDiagram";
import RoadmapTimeline from "./components/RoadmapTimeline";
import "./about.css";

const TECHNOLOGIES = [
  { icon: "🛰️", title: "Google Earth Engine", desc: "Fetching and processing Landsat and Sentinel satellite imagery at planetary scale." },
  { icon: "⚡", title: "FastAPI", desc: "REST API layer serving precomputed shoreline, transect and risk data." },
  { icon: "⚛️", title: "React", desc: "Interactive dashboard interface with real-time layer controls." },
  { icon: "🗺️", title: "Leaflet", desc: "Rendering GIS vector and raster layers on an interactive map." },
  { icon: "🐍", title: "Python", desc: "Geospatial processing — MNDWI, Otsu thresholding, transect sampling." },
  { icon: "📐", title: "GeoJSON", desc: "Open standard format for storing shoreline and transect geometry." },
  { icon: "🗄️", title: "SQLite", desc: "Lightweight storage for citizen-submitted reports." },
  { icon: "🌍", title: "OpenStreetMap / Esri", desc: "Basemap tiles for real-world geographic context." },
];

const DATA_SOURCES = [
  { icon: "🛰️", title: "Landsat", desc: "USGS archive, 2000–2013 coverage." },
  { icon: "🛰️", title: "Sentinel-2", desc: "ESA Copernicus, 10m resolution, 2015–present." },
  { icon: "🌊", title: "JRC Global Surface Water", desc: "Reference water occurrence dataset." },
  { icon: "🗺️", title: "OpenStreetMap", desc: "Roads, settlements, infrastructure context." },
  { icon: "🌬️", title: "Open-Meteo", desc: "Historical wind data for dust-transport modeling." },
  { icon: "📏", title: "USGS DSAS", desc: "Digital Shoreline Analysis System methodology." },
];

const ACCURACY = [
  { title: "Open Satellite Data", desc: "Every measurement traces back to a public Landsat or Sentinel scene." },
  { title: "Transparent Algorithms", desc: "MNDWI + Otsu thresholding — documented, not a black box." },
  { title: "Scientific Methods", desc: "DSAS-style transects, the same approach used in published coastal research." },
  { title: "Reproducible Results", desc: "Same inputs, same pipeline, same outputs — every time." },
];

const FEATURES = [
  { icon: "📅", title: "Interactive Timeline", desc: "Scrub through 26 years of shoreline change, 2000–2026." },
  { icon: "🔀", title: "Shoreline Comparison", desc: "Before/after split view of any two years." },
  { icon: "🏗️", title: "Infrastructure Risk", desc: "Distance-to-shore and retreat speed for critical objects." },
  { icon: "🔥", title: "Heat Map", desc: "Color-coded retreat intensity along the entire coast." },
  { icon: "📊", title: "Risk Analysis", desc: "Weighted scoring across speed, distance, and criticality." },
  { icon: "📡", title: "Offline Mode", desc: "Falls back to a bundled snapshot if the API is unreachable." },
  { icon: "📄", title: "PDF Reports", desc: "One-click export of the current dashboard view." },
  { icon: "📢", title: "Citizen Reporting", desc: "Let residents flag coastal issues directly on the map." },
];

const ROADMAP = [
  { year: "2026", label: "Heat Map risk layer" },
  { year: "2026", label: "Forecast model refinement" },
  { year: "2027", label: "Automated notifications" },
  { year: "2027", label: "3D digital twin of the coastline" },
  { year: "2027", label: "Mobile version" },
];

export default function AboutPage() {
  return (
    <div className="about-page">
      <nav className="about-nav">
        <Link to="/" className="about-nav-brand">Caspian Pulse</Link>
        <Link to="/" className="about-nav-cta">Explore Map →</Link>
      </nav>

      {/* Hero */}
      <header className="about-hero">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        >
          <span className="about-eyebrow">Caspian Hackathon 2026</span>
          <h1 className="about-hero-title">Caspian Pulse</h1>
          <p className="about-hero-lead">AI-powered coastal monitoring platform for the Caspian Sea.</p>
          <p className="about-hero-sub">Turning satellite imagery into actionable environmental intelligence.</p>
          <div className="about-hero-actions">
            <Link to="/" className="about-btn about-btn-primary">Explore Map</Link>
            <a
              href="https://github.com/MAL-Auyl/caspian-drawdown"
              target="_blank"
              rel="noreferrer"
              className="about-btn about-btn-ghost"
            >
              GitHub
            </a>
          </div>
        </motion.div>
        <div className="about-hero-glow" aria-hidden />
      </header>

      {/* Mission */}
      <Section kicker="Why" title="The Caspian Sea is rapidly changing.">
        <p className="about-lead-text">
          Retreating coastlines affect drinking water infrastructure, ports, tourism and coastal ecosystems.
        </p>
        <p className="about-body-text">
          Caspian Pulse transforms satellite imagery into understandable information that helps governments,
          researchers and infrastructure operators make informed decisions — grounded in measurement, not guesswork.
        </p>
      </Section>

      {/* How it works */}
      <Section kicker="Pipeline" title="How it works" className="about-section-alt">
        <FlowDiagram
          steps={[
            "Satellite Imagery",
            "Google Earth Engine",
            "Water Detection (MNDWI)",
            "Shoreline Extraction",
            "Transect Analysis",
            "Risk Assessment",
            "Interactive Dashboard",
            "Reports",
          ]}
        />
      </Section>

      {/* Technologies */}
      <Section kicker="Stack" title="Technologies">
        <CardGrid>
          {TECHNOLOGIES.map((tItem) => (
            <Card key={tItem.title} icon={tItem.icon} title={tItem.title}>
              {tItem.desc}
            </Card>
          ))}
        </CardGrid>
      </Section>

      {/* Data Sources */}
      <Section kicker="Sources" title="Data Sources" className="about-section-alt">
        <CardGrid>
          {DATA_SOURCES.map((d) => (
            <Card key={d.title} icon={d.icon} title={d.title}>
              {d.desc}
            </Card>
          ))}
        </CardGrid>
      </Section>

      {/* Why shorelines look irregular */}
      <Section kicker="Data integrity" title="Why are shoreline lines irregular?">
        <div className="about-split">
          <div>
            <p className="about-body-text">
              The shoreline displayed in Caspian Pulse is generated automatically from real satellite imagery.
            </p>
            <p className="about-body-text">
              Unlike manually drawn maps, every shoreline follows actual pixel boundaries extracted from Landsat
              and Sentinel imagery.
            </p>
            <p className="about-body-text">
              Small irregularities reflect the true satellite observations rather than artistic smoothing. This
              approach preserves scientific accuracy and ensures transparent environmental analysis.
            </p>
          </div>
          <FlowDiagram
            steps={["Satellite Pixels", "Water Classification", "Extracted Shoreline", "Real Coastline"]}
          />
        </div>
      </Section>

      {/* Heat Map */}
      <Section kicker="Visualization" title="Heat Map / Risk Map" className="about-section-alt">
        <p className="about-body-text">
          The Heat Map highlights areas where shoreline retreat is most significant — a single glance replaces
          hundreds of individual transect readings.
        </p>
        <div className="heat-legend">
          <div className="heat-legend-row"><span className="heat-dot heat-low" />Low change</div>
          <div className="heat-legend-row"><span className="heat-dot heat-medium" />Moderate change</div>
          <div className="heat-legend-row"><span className="heat-dot heat-high" />High change</div>
          <div className="heat-legend-row"><span className="heat-dot heat-critical" />Critical change</div>
        </div>
      </Section>

      {/* AI Analysis */}
      <Section kicker="Analytics" title="AI Analysis">
        <p className="about-body-text">
          Artificial intelligence is used to automatically analyze shoreline changes, identify long-term spatial
          patterns, and estimate infrastructure risk.
        </p>
        <p className="about-body-text about-emphasis">
          The system does not generate fictional predictions. All analytics are based on real satellite
          observations and transparent algorithms.
        </p>
      </Section>

      {/* Why GEE */}
      <Section kicker="Infrastructure" title="Why Google Earth Engine?" className="about-section-alt">
        <p className="about-body-text">
          Google Earth Engine provides direct access to decades of satellite imagery without downloading
          terabytes of raw data.
        </p>
        <p className="about-body-text">
          It enables reproducible and scalable environmental analysis — the same query returns the same result,
          whether it's run once or a thousand times.
        </p>
      </Section>

      {/* Accuracy */}
      <Section kicker="Trust" title="Accuracy">
        <CardGrid columns={4}>
          {ACCURACY.map((a) => (
            <Card key={a.title} icon="✔" title={a.title}>
              {a.desc}
            </Card>
          ))}
        </CardGrid>
      </Section>

      {/* Architecture */}
      <Section kicker="Under the hood" title="Project Architecture" className="about-section-alt">
        <FlowDiagram steps={["Frontend", "REST API", "Processing Pipeline", "Google Earth Engine", "Satellite Imagery"]} />
      </Section>

      {/* Features */}
      <Section kicker="Capabilities" title="Features">
        <CardGrid>
          {FEATURES.map((f) => (
            <Card key={f.title} icon={f.icon} title={f.title}>
              {f.desc}
            </Card>
          ))}
        </CardGrid>
      </Section>

      {/* Roadmap */}
      <Section kicker="What's next" title="Future Roadmap" className="about-section-alt">
        <RoadmapTimeline items={ROADMAP} />
      </Section>

      <footer className="about-footer">
        <div className="about-footer-links">
          <span>Open Data:</span>
          <a href="https://earthengine.google.com/" target="_blank" rel="noreferrer">Google Earth Engine</a>
          <a href="https://www.openstreetmap.org/" target="_blank" rel="noreferrer">OpenStreetMap</a>
          <a href="https://www.esa.int/" target="_blank" rel="noreferrer">ESA</a>
          <a href="https://www.usgs.gov/" target="_blank" rel="noreferrer">USGS</a>
        </div>
        <p>Built for Caspian Hackathon 2026.</p>
      </footer>
    </div>
  );
}
