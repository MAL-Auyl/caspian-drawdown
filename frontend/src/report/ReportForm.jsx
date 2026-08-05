import { useState } from "react";
import { submitReport } from "../api/client";
import { useAppStore } from "../store/useAppStore";
import { t } from "../i18n/translations";

const CATEGORIES = ["shoreline_change", "pollution", "dust_storm", "infrastructure", "other"];
const CATEGORY_LABELS_RU = {
  shoreline_change: "Изменение береговой линии", pollution: "Загрязнение",
  dust_storm: "Пыльная буря", infrastructure: "Инфраструктура", other: "Другое",
};

export default function ReportForm() {
  const lang = useAppStore((s) => s.lang);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    latitude: 43.64, longitude: 51.19, category: "shoreline_change", description: "", contact: "",
  });
  const [status, setStatus] = useState("idle"); // idle | sending | sent | error
  const [errorMsg, setErrorMsg] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus("sending");
    setErrorMsg("");
    try {
      await submitReport({
        ...form,
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
        contact: form.contact || null,
      });
      setStatus("sent");
    } catch (err) {
      setStatus("error");
      setErrorMsg(err.message);
    }
  }

  if (!open) {
    return (
      <button className="report-toggle" onClick={() => setOpen(true)}>
        {t(lang, "report")}
      </button>
    );
  }

  return (
    <div className="report-form-wrap">
      <button className="report-close" onClick={() => setOpen(false)}>×</button>
      {status === "sent" ? (
        <p className="report-sent">{t(lang, "reportSent")}</p>
      ) : (
        <form className="report-form" onSubmit={handleSubmit}>
          <label>
            {t(lang, "reportCategory")}
            <select
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{CATEGORY_LABELS_RU[c]}</option>
              ))}
            </select>
          </label>
          <label>
            {t(lang, "reportDescription")}
            <textarea
              minLength={10}
              maxLength={1000}
              required
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </label>
          <label>
            Контакт (необязательно)
            <input
              type="text"
              value={form.contact}
              onChange={(e) => setForm({ ...form, contact: e.target.value })}
            />
          </label>
          {status === "error" && <p className="report-error">{errorMsg}</p>}
          <button type="submit" disabled={status === "sending"}>
            {t(lang, "reportSend")}
          </button>
        </form>
      )}
    </div>
  );
}
