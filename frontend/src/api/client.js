const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api/v1";
const FALLBACK_URL = "/fallback/bootstrap.json";

export async function fetchBootstrap() {
  try {
    // Render free-tier может "спать" и просыпаться до 50с, плюс сам bootstrap
    // на слабом CPU (0.1 vCPU) отвечает не мгновенно — щедрый таймаут вместо
    // преждевременного отката на офлайн-мок.
    const res = await fetch(`${API_BASE}/bootstrap`, { signal: AbortSignal.timeout(45000) });
    if (!res.ok) throw new Error(`bootstrap ${res.status}`);
    const data = await res.json();
    return { data, source: "backend" };
  } catch (err) {
    const res = await fetch(FALLBACK_URL);
    if (!res.ok) throw err;
    const data = await res.json();
    return { data, source: "fallback" };
  }
}

export async function submitReport(payload) {
  const res = await fetch(`${API_BASE}/reports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const message = body?.detail?.detail || body?.detail || "Не удалось отправить сообщение";
    throw new Error(message);
  }
  return body;
}

export async function sendChatMessage(message, history, lang) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history, lang }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const errMessage = body?.detail?.detail || body?.detail || "Не удалось получить ответ";
    throw new Error(errMessage);
  }
  return body.reply;
}

export { API_BASE };
