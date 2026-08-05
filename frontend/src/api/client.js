const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api/v1";
const FALLBACK_URL = "/fallback/bootstrap.json";

export async function fetchBootstrap() {
  try {
    const res = await fetch(`${API_BASE}/bootstrap`, { signal: AbortSignal.timeout(4000) });
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

export { API_BASE };
