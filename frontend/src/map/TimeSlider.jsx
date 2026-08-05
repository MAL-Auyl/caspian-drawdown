import { useEffect, useRef } from "react";
import { useAppStore } from "../store/useAppStore";
import { t } from "../i18n/translations";

const AUTOPLAY_INTERVAL_MS = 700;

export default function TimeSlider() {
  const years = useAppStore((s) => s.years);
  const currentYear = useAppStore((s) => s.currentYear);
  const missingYears = useAppStore((s) => s.missingYears);
  const playing = useAppStore((s) => s.playing);
  const lang = useAppStore((s) => s.lang);
  const setYear = useAppStore((s) => s.setYear);
  const stopPlayback = useAppStore((s) => s.stopPlayback);
  const togglePlayback = useAppStore((s) => s.togglePlayback);
  const stepYear = useAppStore((s) => s.stepYear);

  const timerRef = useRef(null);

  useEffect(() => {
    if (!playing) {
      clearInterval(timerRef.current);
      return;
    }
    timerRef.current = setInterval(() => stepYear(), AUTOPLAY_INTERVAL_MS);
    return () => clearInterval(timerRef.current);
  }, [playing, stepYear]);

  if (!years.length) return null;
  const min = years[0];
  const max = years[years.length - 1];
  const isMissing = missingYears.includes(currentYear);

  function handleChange(e) {
    // stop() ДО установки года — иначе таймер автоплея перезаписывает
    // выбранное вручную значение на следующем тике (грабля #4).
    stopPlayback();
    setYear(Number(e.target.value));
  }

  return (
    <div className="time-slider">
      <button className="play-btn" onClick={togglePlayback}>
        {playing ? t(lang, "pause") : t(lang, "play")}
      </button>
      <input
        type="range"
        min={min}
        max={max}
        step={1}
        value={currentYear}
        onChange={handleChange}
      />
      <span className={`year-label ${isMissing ? "year-missing" : ""}`}>
        {currentYear}
        {isMissing && <em className="missing-note"> — {t(lang, "yearMissing")}</em>}
      </span>
    </div>
  );
}
