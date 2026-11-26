import React from "react";
import { apiOrigin } from "./apiOrigin";
import rachelChatbotIcon from "./assets/rachel-chatbot-icon.svg";

type ChatLine = { role: "user" | "rachel"; text: string };

function MessageText({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <>
      {parts.map((part, index) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={index}>{part.slice(2, -2)}</strong>;
        }
        return <React.Fragment key={index}>{part}</React.Fragment>;
      })}
    </>
  );
}

export default function RachelChat({ onClose }: { onClose: () => void }) {
  const [question, setQuestion] = React.useState("");
  const [lines, setLines] = React.useState<ChatLine[]>([
    { role: "rachel", text: "Ask me about a class. I search the program name and the saved description." },
  ]);
  const [conditions, setConditions] = React.useState<string[]>([]);
  const [busy, setBusy] = React.useState(false);
  const listRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [lines, busy]);

  const ask = async (raw?: string) => {
    const text = (raw ?? question).trim();
    if (!text || busy) return;
    const earlier = lines.filter((line) => line.role === "user").slice(-8).map((line) => line.text);
    setQuestion("");
    setLines((current) => [...current, { role: "user", text }]);
    setBusy(true);
    try {
      const response = await fetch(`${apiOrigin()}/api/rachel/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, history: earlier }),
      });
      const data = await response.json();
      const answer = String(data.answer || "I could not search the class list just now.");
      setConditions(Array.isArray(data.conditions) ? data.conditions.map(String) : []);
      setLines((current) => [...current, { role: "rachel", text: answer }]);
    } catch {
      setLines((current) => [...current, { role: "rachel", text: "I could not search the class list just now. Please try again." }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ textAlign: "left", display: "flex", flexDirection: "column", maxHeight: "70vh" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px", flex: "0 0 auto" }}>
        <img src={rachelChatbotIcon} alt="" style={{ width: "48px", height: "48px" }} />
        <div>
          <h2 style={{ color: "#0072ce", margin: 0, fontSize: "1.5rem" }}>Rachel</h2>
          <p style={{ margin: "4px 0 0", color: "#555" }}>Class search</p>
        </div>
      </div>
      <div ref={listRef} style={{ flex: "1 1 auto", minHeight: "140px", overflow: "auto", background: "#f4f8fb", borderRadius: "8px", padding: "12px", marginBottom: "12px" }}>
        {lines.map((line, index) => (
          <p key={index} style={{ margin: "0 0 12px", whiteSpace: "pre-wrap", textAlign: line.role === "user" ? "right" : "left", color: line.role === "user" ? "#0072ce" : "#222" }}>
            <MessageText text={line.text} />
          </p>
        ))}
        {busy && <p style={{ margin: 0, color: "#555" }}>Looking through the class list...</p>}
      </div>
      {conditions.length > 0 && (
        <div aria-label="Current search" style={{ display: "flex", flexWrap: "wrap", gap: "8px", alignItems: "center", marginBottom: "12px" }}>
          <span style={{ color: "#333", fontWeight: 700 }}>Current search</span>
          {conditions.map((label) => (
            <button
              key={label}
              type="button"
              onClick={() => ask(`remove ${label}`)}
              disabled={busy}
              aria-label={`Remove ${label}`}
              style={{ background: "#e7f1fa", color: "#0072ce", border: "1px solid #b9d4ea", borderRadius: "999px", padding: "6px 10px", cursor: "pointer" }}
            >
              {label} ×
            </button>
          ))}
        </div>
      )}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          ask();
        }}
        style={{ display: "flex", gap: "8px", flex: "0 0 auto" }}
      >
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Gentle exercise on Tuesday morning"
          aria-label="Ask Rachel"
          style={{ flex: 1, padding: "10px", border: "1px solid #ccd6e0", borderRadius: "6px", fontSize: "1rem" }}
        />
        <button type="submit" disabled={busy || !question.trim()} style={{ background: "#0072ce", color: "white", border: "none", borderRadius: "6px", padding: "10px 14px", cursor: busy ? "wait" : "pointer", fontWeight: 700 }}>
          Ask
        </button>
      </form>
      <button type="button" onClick={onClose} style={{ marginTop: "12px", flex: "0 0 auto", alignSelf: "flex-start", background: "white", color: "#333", border: "1px solid #ccd6e0", borderRadius: "6px", padding: "8px 14px", cursor: "pointer" }}>
        Close
      </button>
    </div>
  );
}
