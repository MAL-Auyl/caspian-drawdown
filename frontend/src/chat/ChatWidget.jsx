import { useEffect, useRef, useState } from "react";
import { sendChatMessage } from "../api/client";
import { useAppStore } from "../store/useAppStore";
import { t } from "../i18n/translations";
import mascot from "../assets/mascot-seal.png";

export default function ChatWidget() {
  const lang = useAppStore((s) => s.lang);
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const listRef = useRef(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, sending]);

  async function handleSend(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setError(null);
    setSending(true);
    try {
      const reply = await sendChatMessage(text, history, lang);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className={`chat-widget ${open ? "open" : ""}`}>
      {open && (
        <div className="chat-panel">
          <div className="chat-panel-header">
            <img src={mascot} alt="" className="chat-mascot chat-mascot-small" />
            <div>
              <div className="chat-panel-title">{t(lang, "chatTitle")}</div>
              <div className="chat-panel-subtitle">{t(lang, "chatSubtitle")}</div>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close">×</button>
          </div>

          <div className="chat-messages" ref={listRef}>
            {messages.length === 0 && (
              <div className="chat-empty">{t(lang, "chatGreeting")}</div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble chat-bubble-${m.role}`}>
                {m.content}
              </div>
            ))}
            {sending && <div className="chat-bubble chat-bubble-assistant chat-typing">…</div>}
            {error && <div className="chat-error">{error}</div>}
          </div>

          <form className="chat-input-row" onSubmit={handleSend}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t(lang, "chatPlaceholder")}
              disabled={sending}
            />
            <button type="submit" disabled={sending || !input.trim()}>{t(lang, "chatSend")}</button>
          </form>
        </div>
      )}

      <button className="chat-toggle" onClick={() => setOpen((v) => !v)} aria-label="Chat">
        <img src={mascot} alt="" className="chat-mascot" />
      </button>
    </div>
  );
}
