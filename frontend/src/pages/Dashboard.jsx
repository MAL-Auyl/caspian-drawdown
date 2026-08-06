import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { fetchBootstrap } from "../api/client";
import { useAppStore } from "../store/useAppStore";
import { t } from "../i18n/translations";
import MapView from "../map/MapView";
import TimeSlider from "../map/TimeSlider";
import KpiPanel from "../cards/KpiPanel";
import ObjectPanel from "../cards/ObjectPanel";
import ReportForm from "../report/ReportForm";

export default function Dashboard() {
  const status = useAppStore((s) => s.status);
  const source = useAppStore((s) => s.source);
  const error = useAppStore((s) => s.error);
  const lang = useAppStore((s) => s.lang);
  const setLang = useAppStore((s) => s.setLang);
  const setBootstrap = useAppStore((s) => s.setBootstrap);
  const setError = useAppStore((s) => s.setError);
  const showDust = useAppStore((s) => s.showDust);
  const showSeabed = useAppStore((s) => s.showSeabed);
  const showTransects = useAppStore((s) => s.showTransects);
  const showHeatMap = useAppStore((s) => s.showHeatMap);
  const showBeforeAfter = useAppStore((s) => s.showBeforeAfter);
  const toggleLayer = useAppStore((s) => s.toggleLayer);
  const dashboardRef = useRef(null);

  useEffect(() => {
    fetchBootstrap()
      .then(({ data, source }) => setBootstrap(data, source))
      .catch((err) => setError(err.message || err));
  }, [setBootstrap, setError]);

  if (status === "loading") {
    return <div className="app-loading">Загрузка данных…</div>;
  }
  if (status === "error") {
    return <div className="app-error">Не удалось загрузить данные: {error}</div>;
  }

  return (
    <div className="app-root" ref={dashboardRef}>
      <header className="app-header">
        <div>
          <h1>{t(lang, "title")}</h1>
          <p className="subtitle">{t(lang, "subtitle")}</p>
        </div>
        <div className="header-controls">
          <Link to="/about" className="nav-link">About</Link>
          <select value={lang} onChange={(e) => setLang(e.target.value)}>
            <option value="ru">Русский</option>
            <option value="kk">Қазақша</option>
            <option value="en">English</option>
          </select>
          <button onClick={() => import("../pdf/exportPdf").then((m) => m.exportDashboardToPdf(dashboardRef.current))}>
            {t(lang, "exportPdf")}
          </button>
        </div>
      </header>

      {source === "fallback" && <div className="offline-banner">{t(lang, "offlineNotice")}</div>}

      <KpiPanel />

      <main className="app-main">
        <section className="map-section">
          <MapView />
          <TimeSlider />
          <div className="layer-toggles">
            <label><input type="checkbox" checked={showTransects} onChange={() => toggleLayer("showTransects")} /> {t(lang, "transects")}</label>
            <label><input type="checkbox" checked={showHeatMap} onChange={() => toggleLayer("showHeatMap")} /> {t(lang, "heatMap")}</label>
            <label><input type="checkbox" checked={showDust} onChange={() => toggleLayer("showDust")} /> {t(lang, "dust")}</label>
            <label><input type="checkbox" checked={showSeabed} onChange={() => toggleLayer("showSeabed")} /> {t(lang, "seabed")}</label>
            <label><input type="checkbox" checked={showBeforeAfter} onChange={() => toggleLayer("showBeforeAfter")} /> Было / стало (2000 → 2026)</label>
          </div>
        </section>
        <aside className="side-panel">
          <ObjectPanel />
        </aside>
      </main>

      <footer className="app-footer">
        <p>{t(lang, "methodNote")}</p>
        <ReportForm />
      </footer>
    </div>
  );
}
