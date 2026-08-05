import { useAppStore } from "../store/useAppStore";

export default function KpiPanel() {
  const stats = useAppStore((s) => s.statistics);
  if (!stats) return null;

  return (
    <div className="kpi-panel">
      <div className="kpi-tile">
        <div className="kpi-value">{stats.retreat.mean_speed_m_per_year}</div>
        <div className="kpi-label">м/год, средняя скорость отступления</div>
      </div>
      <div className="kpi-tile">
        <div className="kpi-value">{stats.coastline.transects_total}</div>
        <div className="kpi-label">сегментов проанализировано</div>
      </div>
      <div className="kpi-tile">
        <div className="kpi-value">{stats.exposed_seabed_km2}</div>
        <div className="kpi-label">км² осушенного дна</div>
      </div>
      <div className="kpi-tile">
        <div className="kpi-value">{stats.objects.high_risk}</div>
        <div className="kpi-label">объектов высокого риска</div>
      </div>
    </div>
  );
}
