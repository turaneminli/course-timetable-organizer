import React, { useMemo } from "react";

const DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function normalizeDay(v) {
  if (!v) return "";
  const s = String(v).trim().toLowerCase();
  if (s.startsWith("mon")) return "Mon";
  if (s.startsWith("tue")) return "Tue";
  if (s.startsWith("wed")) return "Wed";
  if (s.startsWith("thu")) return "Thu";
  if (s.startsWith("fri")) return "Fri";
  if (s.startsWith("sat")) return "Sat";
  if (s.startsWith("sun")) return "Sun";
  if (s === "monday") return "Mon";
  if (s === "tuesday") return "Tue";
  if (s === "wednesday") return "Wed";
  if (s === "thursday") return "Thu";
  if (s === "friday") return "Fri";
  if (s === "saturday") return "Sat";
  if (s === "sunday") return "Sun";
  return v;
}

function parseTimeToMin(t) {
  if (t == null) return null;
  const s = String(t).trim();
  const m = s.match(/^(\d{1,2}):(\d{2})$/);
  if (!m) return null;
  const hh = Number(m[1]);
  const mm = Number(m[2]);
  if (Number.isNaN(hh) || Number.isNaN(mm)) return null;
  return hh * 60 + mm;
}

function extractTimeRange(row) {
  const directStart = row.start ?? row.start_time ?? row.begin ?? row.from;
  const directEnd = row.end ?? row.end_time ?? row.finish ?? row.to;

  const sMin = parseTimeToMin(directStart);
  const eMin = parseTimeToMin(directEnd);

  if (sMin != null && eMin != null) {
    const start = String(directStart).padStart(5, "0");
    const end = String(directEnd).padStart(5, "0");
    return { key: `${start}-${end}`, label: `${start}–${end}`, startMin: sMin };
  }

  const maybe = row.time ?? row.timeslot ?? row.slot ?? row.period;
  if (maybe != null) {
    const txt = String(maybe).trim();
    const m = txt.match(/(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})/);
    if (m) {
      const a = m[1].padStart(5, "0");
      const b = m[2].padStart(5, "0");
      const aMin = parseTimeToMin(a);
      return { key: `${a}-${b}`, label: `${a}–${b}`, startMin: aMin ?? 99999 };
    }
    return { key: txt, label: txt, startMin: 99999 };
  }

  return { key: "Unknown", label: "Unknown", startMin: 99999 };
}

function getPrimaryLabel(r) {
  return (
    r.course ??
    r.subject ??
    r.module ??
    r.lesson ??
    r.name ??
    r.class ??
    r.unit ??
    "Lesson"
  );
}

function compact(v) {
  if (v == null) return "";
  const s = String(v).trim();
  return s;
}

function buildDisplayParts(r, mode) {
  const teacher = compact(r.teacher);
  const room = compact(r.room);
  const group = compact(r.group);

  if (mode === "group") return { top: getPrimaryLabel(r), mid: teacher, right: room };
  if (mode === "teacher") return { top: getPrimaryLabel(r), mid: group, right: room };
  if (mode === "room") return { top: getPrimaryLabel(r), mid: group, right: teacher };
  return { top: getPrimaryLabel(r), mid: teacher, right: room };
}

export default function TimetableGrid({ mode, selected, schedule, byGroup }) {
  const rows = useMemo(() => {
    if (!selected) return [];
    if (mode === "group") return (byGroup || []).filter((r) => String(r.group) === String(selected));
    if (mode === "teacher") return (schedule || []).filter((r) => String(r.teacher) === String(selected));
    if (mode === "room") return (schedule || []).filter((r) => String(r.room) === String(selected));
    return [];
  }, [mode, selected, schedule, byGroup]);

  const { times, cellMap } = useMemo(() => {
    const tMap = new Map();
    const map = new Map();

    for (const r of rows) {
      const day = normalizeDay(r.day ?? r.weekday ?? r.dow);
      const tr = extractTimeRange(r);
      tMap.set(tr.key, tr);

      const key = `${tr.key}__${day}`;
      const arr = map.get(key) || [];
      arr.push(r);
      map.set(key, arr);
    }

    const timesArr = Array.from(tMap.values()).sort((a, b) => {
      if (a.startMin !== b.startMin) return a.startMin - b.startMin;
      return a.label.localeCompare(b.label);
    });

    return { times: timesArr, cellMap: map };
  }, [rows]);

  if (!selected) {
    return <div style={{ color: "#666" }}>No selection</div>;
  }

  const gridTemplateColumns = `120px repeat(${DAY_ORDER.length}, minmax(160px, 1fr))`;

  return (
    <div
      style={{
        border: "1px solid #eee",
        borderRadius: 12,
        overflow: "hidden",
        background: "#fff",
      }}
    >
      <div style={{ overflowX: "auto" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns,
            minWidth: 120 + DAY_ORDER.length * 160,
          }}
        >
          <div
            style={{
              position: "sticky",
              left: 0,
              zIndex: 3,
              background: "#fff",
              fontWeight: 800,
              padding: "12px 10px",
              borderBottom: "1px solid #eee",
              borderRight: "1px solid #eee",
            }}
          >
            Time
          </div>

          {DAY_ORDER.map((d) => (
            <div
              key={d}
              style={{
                position: "sticky",
                top: 0,
                zIndex: 2,
                background: "#fff",
                fontWeight: 800,
                padding: "12px 10px",
                borderBottom: "1px solid #eee",
                borderRight: "1px solid #eee",
                textAlign: "left",
              }}
            >
              {d}
            </div>
          ))}

          {times.length === 0 ? (
            <div style={{ gridColumn: `1 / span ${1 + DAY_ORDER.length}`, padding: 14, color: "#666" }}>
              No lessons for {mode}: <b>{selected}</b>
            </div>
          ) : (
            times.map((t, idx) => {
              const zebra = idx % 2 === 1;
              return (
                <React.Fragment key={t.key}>
                  <div
                    style={{
                      position: "sticky",
                      left: 0,
                      zIndex: 1,
                      background: zebra ? "#fcfcfc" : "#fff",
                      padding: "10px 10px",
                      borderBottom: "1px solid #f0f0f0",
                      borderRight: "1px solid #eee",
                      fontWeight: 700,
                      color: "#333",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {t.label}
                  </div>

                  {DAY_ORDER.map((d) => {
                    const key = `${t.key}__${d}`;
                    const items = cellMap.get(key) || [];
                    return (
                      <div
                        key={d}
                        style={{
                          background: zebra ? "#fcfcfc" : "#fff",
                          padding: 8,
                          borderBottom: "1px solid #f0f0f0",
                          borderRight: "1px solid #eee",
                          minHeight: 56,
                        }}
                      >
                        {items.map((r, i) => {
                          const parts = buildDisplayParts(r, mode);
                          const title = `${parts.top}${parts.mid ? " • " + parts.mid : ""}${parts.right ? " • " + parts.right : ""}`;
                          return (
                            <div
                              key={i}
                              title={title}
                              style={{
                                border: "1px solid #fed7aa",
                                background: "#fff7ed",
                                borderRadius: 10,
                                padding: "8px 10px",
                                marginBottom: 6,
                                lineHeight: 1.2,
                                overflowWrap: "anywhere",
                                wordBreak: "break-word",
                              }}
                            >
                              <div style={{ fontWeight: 800, color: "#111", fontSize: 13 }}>{parts.top}</div>
                              {(parts.mid || parts.right) && (
                                <div style={{ marginTop: 4, display: "flex", gap: 6, flexWrap: "wrap" }}>
                                  {parts.mid && (
                                    <span
                                      style={{
                                        fontSize: 12,
                                        padding: "2px 8px",
                                        borderRadius: 999,
                                        border: "1px solid #fdba74",
                                        background: "#ffedd5",
                                      }}
                                    >
                                      {parts.mid}
                                    </span>
                                  )}
                                  {parts.right && (
                                    <span
                                      style={{
                                        fontSize: 12,
                                        padding: "2px 8px",
                                        borderRadius: 999,
                                        border: "1px solid #fdba74",
                                        background: "#ffedd5",
                                      }}
                                    >
                                      {parts.right}
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    );
                  })}
                </React.Fragment>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
