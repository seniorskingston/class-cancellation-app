import React from "react";
import { apiOrigin } from "./apiOrigin";

export type GuideField = {
  field: string;
  label: string;
  before: string;
  after: string;
  summary: string;
};

export type GuideProgram = {
  id?: string;
  program: string;
  program_id: string;
  session: string;
  day: string;
  date_range: string;
  time: string;
  location: string;
  room: string;
  instructor: string;
  fee: string;
  status: string;
  kind?: string;
  note?: string;
  source?: string;
  updated_at?: string;
  fields?: GuideField[];
};

export type GuideReport = {
  ready?: boolean;
  message?: string;
  baseline_saved_at?: string;
  baseline_source?: string;
  session?: string;
  additions?: GuideProgram[];
  changes?: GuideProgram[];
  cancelled?: GuideProgram[];
  counts?: { additions: number; changes: number; cancelled: number; total: number };
};

const emptyCounts = { additions: 0, changes: 0, cancelled: 0, total: 0 };

function place(program: GuideProgram): string {
  return [program.location, program.room].filter(Boolean).join(" — ");
}

function changed(program: GuideProgram, field: string): GuideField | undefined {
  return (program.fields || []).find((item) => item.field === field);
}

function Value({ program, field, text }: { program: GuideProgram; field: string; text: string }) {
  const change = changed(program, field);
  if (!change) {
    return <span>{text || "—"}</span>;
  }
  return (
    <span>
      <span style={{ display: "block", color: "#555" }}>Was {change.before}</span>
      <span style={{ background: "#fff3bf", color: "#3f3500", padding: "1px 4px" }}>{change.after}</span>
      <span style={{ display: "block", fontSize: "0.85rem" }}>{change.summary}</span>
    </span>
  );
}

function ProgramCard({ program, tone, onRemove }: { program: GuideProgram; tone: "add" | "change" | "cancel"; onRemove?: (program: GuideProgram) => void }) {
  const border = tone === "add" ? "#b7dfc4" : tone === "cancel" ? "#f0c2c2" : "#e4e7eb";
  return (
    <article style={{ border: `1px solid ${border}`, borderRadius: "8px", padding: "12px", marginBottom: "10px", background: "#fff" }}>
      <h3 style={{ margin: "0 0 6px", fontSize: "1.05rem" }}>
        {program.program || "Program"}{" "}
        <span style={{ color: "#555", fontWeight: 500 }}>{program.program_id}</span>
      </h3>
      {tone === "cancel" && <p style={{ margin: "0 0 8px", color: "#8a1f11", fontWeight: 700 }}>Cancelled</p>}
      {program.source === "admin" && <p style={{ margin: "0 0 8px", color: "#0c5460" }}>Added from the Admin page.</p>}
      {program.note && <p style={{ margin: "0 0 8px" }}>{program.note}</p>}
      <p style={{ margin: "4px 0" }}>Session {program.session} · {program.day}</p>
      <p style={{ margin: "4px 0" }}>{program.date_range || "Dates not listed"}</p>
      <p style={{ margin: "4px 0" }}><Value program={program} field="time" text={program.time} /></p>
      <p style={{ margin: "4px 0" }}><Value program={program} field="location" text={place(program)} /></p>
      {changed(program, "class_room") && (
        <p style={{ margin: "4px 0" }}><Value program={program} field="class_room" text={program.room} /></p>
      )}
      <p style={{ margin: "4px 0" }}>Instructor: <Value program={program} field="instructor" text={program.instructor} /></p>
      {(program.fee || changed(program, "fee")) && (
        <p style={{ margin: "4px 0" }}>Fee: <Value program={program} field="fee" text={program.fee} /></p>
      )}
      {changed(program, "program") && (
        <p style={{ margin: "4px 0" }}>Name: <Value program={program} field="program" text={program.program} /></p>
      )}
      {changed(program, "date_range") && (
        <p style={{ margin: "4px 0" }}>Dates: <Value program={program} field="date_range" text={program.date_range} /></p>
      )}
      {changed(program, "sheet") && (
        <p style={{ margin: "4px 0" }}>Day: <Value program={program} field="sheet" text={program.day} /></p>
      )}
      {changed(program, "program_status") && (
        <p style={{ margin: "4px 0" }}><Value program={program} field="program_status" text={program.status} /></p>
      )}
      {onRemove && (
        <button type="button" onClick={() => onRemove(program)} style={{ background: "#b42318", color: "white", border: "none", borderRadius: "6px", padding: "6px 10px", cursor: "pointer", marginTop: "8px" }}>
          Remove from list
        </button>
      )}
    </article>
  );
}

function Group({ title, tone, programs, onRemove }: { title: string; tone: "add" | "change" | "cancel"; programs: GuideProgram[]; onRemove?: (program: GuideProgram) => void }) {
  const kind = tone === "add" ? "addition" : tone === "cancel" ? "cancelled" : "change";
  return (
    <section style={{ marginTop: "16px" }}>
      <h2 style={{ fontSize: "1.15rem", marginBottom: "8px" }}>{title} ({programs.length})</h2>
      {programs.length === 0 ? <p>None.</p> : programs.map((program) => (
        <ProgramCard
          key={program.id || `${program.program_id}-${program.day}-${program.session}`}
          program={{ ...program, kind: program.kind || kind }}
          tone={tone}
          onRemove={onRemove}
        />
      ))}
    </section>
  );
}

function sessionLabel(report: GuideReport): string {
  const value = report.session || "";
  if (!value) return "Program Guide Updates";
  return /^session/i.test(value) ? value : `Session ${value}`;
}

function changeText(program: GuideProgram): string {
  const lines = (program.fields || []).map((field) => `${field.label} was ${field.before}, now ${field.after}`);
  if (program.note) lines.push(program.note);
  return lines.join("; ");
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function printCell(value: string): string {
  return `<td>${escapeHtml(value || "")}</td>`;
}

function printTable(title: string, programs: GuideProgram[], includeChange?: boolean): string {
  if (!programs.length) return "";
  const headings = ["Program", "ID", "Day", "Dates", "Time", "Location", "Instructor", "Fee"];
  if (includeChange) headings.push("What changed");
  const head = headings.map((heading) => `<th>${heading}</th>`).join("");
  const body = programs.map((program) => {
    const cells = [
      printCell(program.program),
      printCell(program.program_id),
      printCell(program.day),
      printCell(program.date_range),
      printCell(program.time),
      printCell(place(program)),
      printCell(program.instructor),
      printCell(program.fee),
    ];
    if (includeChange) cells.push(printCell(changeText(program)));
    return `<tr>${cells.join("")}</tr>`;
  }).join("");
  return `<h2>${escapeHtml(title)} (${programs.length})</h2><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function printUpdates(report: GuideReport) {
  const counts = report.counts || emptyCounts;
  const printedOn = new Date().toLocaleDateString("en-US", { timeZone: "America/Toronto", year: "numeric", month: "long", day: "numeric" });
  const tables = counts.total === 0
    ? `<p>${escapeHtml(report.message || "No Program Guide updates at this time.")}</p>`
    : [
        printTable("Additions", report.additions || []),
        printTable("Changes", report.changes || [], true),
        printTable("Cancelled", report.cancelled || []),
      ].join("");
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Program Guide Updates</title><style>
    @page { size: letter landscape; margin: 12mm; }
    html, body { margin: 0; padding: 0; }
    body { font-family: Arial, sans-serif; color: #111; font-size: 11px; }
    h1 { font-size: 18px; margin: 0 0 6px; }
    h2 { font-size: 14px; margin: 14px 0 6px; page-break-after: avoid; }
    p { margin: 0 0 8px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border-bottom: 1px solid #ccc; text-align: left; padding: 4px; vertical-align: top; }
    tr { break-inside: avoid; page-break-inside: avoid; }
  </style></head><body>
    <h1>Program Guide Updates — ${escapeHtml(sessionLabel(report))}</h1>
    <p>Printed ${escapeHtml(printedOn)}. Additions ${counts.additions}. Changes ${counts.changes}. Cancelled ${counts.cancelled}. Total ${counts.total}.</p>
    ${tables}
  </body></html>`;
  const iframe = document.createElement("iframe");
  iframe.setAttribute("style", "position:fixed;width:0;height:0;border:0;");
  document.body.appendChild(iframe);
  const frame = iframe.contentWindow;
  const doc = iframe.contentDocument;
  if (!frame || !doc) {
    document.body.removeChild(iframe);
    return;
  }
  doc.open();
  doc.write(html);
  doc.close();
  const cleanup = () => window.setTimeout(() => {
    if (iframe.parentNode) iframe.parentNode.removeChild(iframe);
  }, 1000);
  frame.addEventListener("afterprint", cleanup);
  frame.focus();
  frame.print();
}

export function ProgramGuideReport({ report, onRemove, printable = true }: { report: GuideReport; onRemove?: (program: GuideProgram) => void; printable?: boolean }) {
  const counts = report.counts || emptyCounts;
  const additions = report.additions || [];
  const changes = report.changes || [];
  const cancelled = report.cancelled || [];
  if (report.ready === false) {
    return <p>{report.message}</p>;
  }
  return (
    <div>
      {printable && (
        <button type="button" onClick={() => printUpdates(report)} style={{ background: "#0072ce", color: "white", border: "none", borderRadius: "6px", padding: "8px 12px", cursor: "pointer", marginBottom: "12px" }}>
          Print updates
        </button>
      )}
      {report.baseline_saved_at && (
        <p>
          {report.baseline_source === "earliest"
            ? `Printed Program Guide is the earliest class list on this computer, saved ${report.baseline_saved_at}.`
            : `Printed Program Guide saved ${report.baseline_saved_at}.`}
        </p>
      )}
      <p>{counts.total} updated program{counts.total === 1 ? "" : "s"}.</p>
      {counts.total === 0 ? <p>{report.message}</p> : (
        <>
          <Group title="Additions" tone="add" programs={additions} onRemove={onRemove} />
          <Group title="Changes" tone="change" programs={changes} onRemove={onRemove} />
          <Group title="Cancelled" tone="cancel" programs={cancelled} onRemove={onRemove} />
        </>
      )}
    </div>
  );
}

const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

const fieldStyle = { display: "block", width: "100%", margin: "0 0 10px", padding: "8px", border: "1px solid #ccd6e0", borderRadius: "6px" };

export function ProgramGuideManual({ sessions, onSaved }: { sessions: string[]; onSaved?: () => void }) {
  const [session, setSession] = React.useState(sessions.find((item) => /2/.test(item)) || sessions[0] || "Session 2-2026");
  const [kind, setKind] = React.useState("addition");
  const [program, setProgram] = React.useState("");
  const [programId, setProgramId] = React.useState("");
  const [day, setDay] = React.useState("Monday");
  const [dateRange, setDateRange] = React.useState("");
  const [time, setTime] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [room, setRoom] = React.useState("");
  const [instructor, setInstructor] = React.useState("");
  const [fee, setFee] = React.useState("");
  const [note, setNote] = React.useState("");
  const [items, setItems] = React.useState<GuideProgram[]>([]);
  const [message, setMessage] = React.useState("");

  const loadItems = React.useCallback(async () => {
    try {
      const response = await fetch(`${apiOrigin()}/api/program-guide/manual`);
      if (!response.ok) return;
      const data = await response.json();
      setItems(Array.isArray(data.items) ? data.items : []);
    } catch {
      setItems([]);
    }
  }, []);

  React.useEffect(() => {
    loadItems();
  }, [loadItems]);

  const addItem = async () => {
    setMessage("");
    try {
      const response = await fetch(`${apiOrigin()}/api/program-guide/manual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session,
          kind,
          program,
          program_id: programId,
          day,
          date_range: dateRange,
          time,
          location,
          room,
          instructor,
          fee,
          note,
        }),
      });
      const data = await response.json();
      if (data.status !== "saved") {
        setMessage(data.message || "The update was not added.");
        return;
      }
      setProgram("");
      setProgramId("");
      setDateRange("");
      setTime("");
      setLocation("");
      setRoom("");
      setInstructor("");
      setFee("");
      setNote("");
      setMessage("Added to the Program Guide Updates list.");
      loadItems();
      if (onSaved) onSaved();
    } catch {
      setMessage("The update was not added.");
    }
  };

  const removeItem = async (id: string) => {
    setMessage("");
    try {
      const response = await fetch(`${apiOrigin()}/api/program-guide/manual/${encodeURIComponent(id)}`, { method: "DELETE" });
      const data = await response.json();
      if (data.status !== "removed") {
        setMessage(data.message || "The update was not removed.");
        return;
      }
      setMessage("Removed from the Program Guide Updates list.");
      loadItems();
      if (onSaved) onSaved();
    } catch {
      setMessage("The update was not removed.");
    }
  };

  const kindLabel = (value: string) => value === "change" ? "Change" : value === "cancelled" ? "Cancelled" : "Addition";

  return (
    <div style={{ marginTop: "16px" }}>
      <h3>Add to Program Guide Updates</h3>
      <p>These items stay on the public Program Guide Updates page until you remove them.</p>
      <label htmlFor="manualSession">Session</label>
      <select id="manualSession" value={session} onChange={(event) => setSession(event.target.value)} style={fieldStyle}>
        {(sessions.length ? sessions : ["Session 2-2026"]).map((item) => (
          <option key={item} value={item}>{item}</option>
        ))}
      </select>
      <label htmlFor="manualKind">Type</label>
      <select id="manualKind" value={kind} onChange={(event) => setKind(event.target.value)} style={fieldStyle}>
        <option value="addition">Addition</option>
        <option value="change">Change</option>
        <option value="cancelled">Cancelled</option>
      </select>
      <label htmlFor="manualProgram">Program name</label>
      <input id="manualProgram" value={program} onChange={(event) => setProgram(event.target.value)} style={fieldStyle} />
      <label htmlFor="manualProgramId">Program ID</label>
      <input id="manualProgramId" value={programId} onChange={(event) => setProgramId(event.target.value)} style={fieldStyle} />
      <label htmlFor="manualDay">Day</label>
      <select id="manualDay" value={day} onChange={(event) => setDay(event.target.value)} style={fieldStyle}>
        {days.map((item) => <option key={item} value={item}>{item}</option>)}
      </select>
      <label htmlFor="manualDates">Dates</label>
      <input id="manualDates" value={dateRange} onChange={(event) => setDateRange(event.target.value)} style={fieldStyle} />
      <label htmlFor="manualTime">Time</label>
      <input id="manualTime" value={time} onChange={(event) => setTime(event.target.value)} style={fieldStyle} />
      <label htmlFor="manualLocation">Location</label>
      <input id="manualLocation" value={location} onChange={(event) => setLocation(event.target.value)} style={fieldStyle} />
      <label htmlFor="manualRoom">Room</label>
      <input id="manualRoom" value={room} onChange={(event) => setRoom(event.target.value)} style={fieldStyle} />
      <label htmlFor="manualInstructor">Instructor</label>
      <input id="manualInstructor" value={instructor} onChange={(event) => setInstructor(event.target.value)} style={fieldStyle} />
      <label htmlFor="manualFee">Fee</label>
      <input id="manualFee" value={fee} onChange={(event) => setFee(event.target.value)} style={fieldStyle} />
      <label htmlFor="manualNote">{kind === "change" ? "What changed" : "Note"}</label>
      <textarea id="manualNote" value={note} onChange={(event) => setNote(event.target.value)} style={{ ...fieldStyle, minHeight: "70px" }} />
      <button type="button" onClick={addItem} style={{ background: "#0072ce", color: "white", border: "none", borderRadius: "6px", padding: "8px 12px", cursor: "pointer" }}>
        Add to the list
      </button>
      {message && <p>{message}</p>}
      {items.length > 0 && (
        <div style={{ marginTop: "12px" }}>
          {items.map((item) => (
            <div key={item.id || `${item.program_id}-${item.day}`} style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "8px" }}>
              <span style={{ flex: 1 }}>{kindLabel(item.kind || "")}: {item.program} {item.program_id}, {item.day}, Session {item.session}</span>
              {item.id && (
                <button type="button" onClick={() => removeItem(item.id || "")} style={{ background: "#b42318", color: "white", border: "none", borderRadius: "6px", padding: "6px 10px", cursor: "pointer" }}>
                  Remove
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

type PageProps = {
  sessions: string[];
  onBack: () => void;
};

const ProgramGuideUpdates: React.FC<PageProps> = ({ sessions, onBack }) => {
  const [session, setSession] = React.useState(sessions[0] || "");
  const [report, setReport] = React.useState<GuideReport | null>(null);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    if (!session) return;
    let stopped = false;
    setError("");
    fetch(`${apiOrigin()}/api/program-guide/updates?session=${encodeURIComponent(session)}`)
      .then((response) => response.json())
      .then((data) => {
        if (!stopped) setReport(data);
      })
      .catch(() => {
        if (!stopped) setError("The Program Guide updates could not be loaded.");
      });
    return () => {
      stopped = true;
    };
  }, [session]);

  return (
    <div className="App" style={{ maxWidth: "860px", margin: "0 auto", padding: "16px" }}>
      <button type="button" onClick={onBack}>Back</button>
      <h1>Program Guide Updates</h1>
      <label htmlFor="guideSession">Session</label>
      <select id="guideSession" value={session} onChange={(event) => setSession(event.target.value)}>
        {sessions.map((item) => {
          const label = /^session/i.test(item) ? item : `Session ${item}`;
          return <option key={item} value={item}>{label}</option>;
        })}
      </select>
      {error && <p>{error}</p>}
      {report && <ProgramGuideReport report={report} />}
    </div>
  );
};

export default ProgramGuideUpdates;
