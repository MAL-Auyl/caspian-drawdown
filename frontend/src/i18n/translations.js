export const translations = {
  ru: {
    title: "Caspian Pulse",
    subtitle: "Отступление берега Каспия и риск для инфраструктуры Мангистау",
    play: "Воспроизвести", pause: "Пауза",
    yearMissing: "Нет данных за этот год",
    layers: "Слои", dust: "Пылевой риск", seabed: "Осушенное дно", transects: "Сегменты",
    objects: "Объекты", riskScore: "Оценка риска", speed: "Скорость отступления",
    distance: "Расстояние до воды", forecast: "Прогноз", exportPdf: "Экспорт в PDF",
    report: "Сообщить о проблеме", reportSend: "Отправить", reportSent: "Заявка принята",
    reportDescription: "Опишите, что вы заметили", reportCategory: "Категория",
    offlineNotice: "Backend недоступен — показаны сохранённые данные",
    methodNote: "MNDWI + порог Оцу, трансекты DSAS. Аналитический инструмент, не заменяет официальные изыскания.",
  },
  kk: {
    title: "Caspian Pulse",
    subtitle: "Каспий жағалауының кейін шегінуі және Маңғыстау инфрақұрылымына қауіп",
    play: "Ойнату", pause: "Кідірту",
    yearMissing: "Бұл жыл бойынша деректер жоқ",
    layers: "Қабаттар", dust: "Шаң қаупі", seabed: "Құрғаған түп", transects: "Сегменттер",
    objects: "Нысандар", riskScore: "Қауіп бағасы", speed: "Шегіну жылдамдығы",
    distance: "Суға дейінгі қашықтық", forecast: "Болжам", exportPdf: "PDF-ге экспорттау",
    report: "Мәселе туралы хабарлау", reportSend: "Жіберу", reportSent: "Өтініш қабылданды",
    reportDescription: "Не байқағаныңызды сипаттаңыз", reportCategory: "Санат",
    offlineNotice: "Backend қолжетімсіз — сақталған деректер көрсетілді",
    methodNote: "MNDWI + Оцу шегі, DSAS трансекттері. Талдау құралы, ресми зерттеулерді алмастырмайды.",
  },
  en: {
    title: "Caspian Pulse",
    subtitle: "Caspian shoreline retreat and infrastructure risk in Mangystau",
    play: "Play", pause: "Pause",
    yearMissing: "No data for this year",
    layers: "Layers", dust: "Dust risk", seabed: "Exposed seabed", transects: "Segments",
    objects: "Objects", riskScore: "Risk score", speed: "Retreat speed",
    distance: "Distance to water", forecast: "Forecast", exportPdf: "Export PDF",
    report: "Report an issue", reportSend: "Submit", reportSent: "Report received",
    reportDescription: "Describe what you noticed", reportCategory: "Category",
    offlineNotice: "Backend unavailable — showing saved data",
    methodNote: "MNDWI + Otsu threshold, DSAS-style transects. A decision-support tool, not a substitute for official surveys.",
  },
};

export function t(lang, key) {
  return translations[lang]?.[key] ?? translations.ru[key] ?? key;
}
