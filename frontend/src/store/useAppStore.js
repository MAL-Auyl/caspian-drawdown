import { create } from "zustand";

export const useAppStore = create((set, get) => ({
  status: "loading", // loading | ready | error
  source: null, // "backend" | "fallback"
  error: null,

  meta: null,
  shorelines: {},
  transects: null,
  objects: null,
  dustZones: null,
  exposedSeabed: null,
  statistics: null,

  years: [],
  missingYears: [],
  currentYear: 2026,
  playing: false,

  lang: "ru",
  selectedObjectId: null,
  showDust: false,
  showSeabed: false,
  showTransects: true,

  setBootstrap(data, source) {
    const years = data.meta?.years ?? [];
    set({
      status: "ready",
      source,
      meta: data.meta,
      shorelines: data.shorelines,
      transects: data.transects,
      objects: data.objects,
      dustZones: data.dust_zones,
      exposedSeabed: data.exposed_seabed,
      statistics: data.statistics,
      years,
      missingYears: data.meta?.missing_years ?? [],
      currentYear: years[years.length - 1] ?? 2026,
    });
  },

  setError(error) {
    set({ status: "error", error: String(error) });
  },

  setYear(year) {
    set({ currentYear: year });
  },

  stopPlayback() {
    set({ playing: false });
  },

  togglePlayback() {
    set((s) => ({ playing: !s.playing }));
  },

  stepYear() {
    const { years, currentYear, missingYears } = get();
    if (!years.length) return;
    let idx = years.indexOf(currentYear);
    let next;
    do {
      idx = (idx + 1) % years.length;
      next = years[idx];
    } while (missingYears.includes(next) && years.length > 1);
    set({ currentYear: next });
  },

  selectObject(id) {
    set({ selectedObjectId: id });
  },

  setLang(lang) {
    set({ lang });
  },

  toggleLayer(name) {
    set((s) => ({ [name]: !s[name] }));
  },
}));
