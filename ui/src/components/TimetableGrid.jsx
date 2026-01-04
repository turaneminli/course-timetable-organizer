import React, { useMemo } from "react";

function parseLabel(label, timeslotId) {
  const s = String(label || "");
  if (s.includes(",")) {
    const parts = s.split(",");
    const dayRaw = (parts[0] || "").trim();
    const day = dayRaw.includes("_") ? dayRaw.split("_")[0] : dayRaw;
    const time = (parts[1] || "").trim();
    return { day, time };
  }
  const id = String(timeslotId || s);
  const day = id.includes("_") ? id.split("_")[0] : id;
  const time = s || id;
  return { day, time };
}


const DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function TimetableGrid({ mode, selected, schedule, byGroup }) {
  const rows = useMemo(() => {
    if (!selected) return [];
    if (mode === "group") return byGroup.filter((r) => r.group === selected);
    if (mode === "teacher") return schedule.filter((r) => r.teacher === selected);
    if (mode === "room") return schedule.filter((r) => r.room === selected);
    return [];
  }, [mode, selected, schedule, byGroup]);

  const slots = useMemo(() => {
    const m = new Map();
    for (const r of rows) {
      const { day, time } = parseLabel(r.timeslot_label, r.timeslot_id);
      if (!m.has(time)) m.set(time, new Map());
      m.get(time).set(day, r);
    }
    const times = Array.from(m.keys()).sort();
    const days = DAY_ORDER.filter((d) => rows.some((r) => parseLabel(r.timeslot_label, r.timeslot_id).day === d));
    return { times, days, m };
  }, [rows]);

  if (!rows.length) return <div style={{ color: "#666" }}>No rows for selection</div>;

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th style={{ borderBottom: "1px solid #ddd", textAlign: "left", padding: 8 }}>Time</th>
            {slots.days.map((d) => (
              <th key={d} style={{ borderBottom: "1px solid #ddd", textAlign: "left", padding: 8 }}>
                {d}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {slots.times.map((t) => (
            <tr key={t}>
              <td style={{ borderBottom: "1px solid #eee", padding: 8, whiteSpace: "nowrap" }}>{t}</td>
              {slots.days.map((d) => {
                const cell = slots.m.get(t)?.get(d);
                const text = cell
                  ? mode === "group"
                    ? `${cell.course} · ${cell.teacher} · ${cell.room}`
                    : `${cell.course} · ${cell.teacher} · ${cell.room} · ${cell.session_id}`
                  : "";
                return (
                  <td key={d} style={{ borderBottom: "1px solid #eee", padding: 8, minWidth: 220, verticalAlign: "top" }}>
                    {text}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
