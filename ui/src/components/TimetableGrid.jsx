import React, { useMemo } from "react";

const DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const DAY_ALIASES = {
  mon: "Mon",
  monday: "Mon",
  tue: "Tue",
  tues: "Tue",
  tuesday: "Tue",
  wed: "Wed",
  wednesday: "Wed",
  thu: "Thu",
  thur: "Thu",
  thurs: "Thu",
  thursday: "Thu",
  fri: "Fri",
  friday: "Fri",
  sat: "Sat",
  saturday: "Sat",
  sun: "Sun",
  sunday: "Sun",
};

function normDay(s) {
  const k = String(s || "").trim().toLowerCase();
  if (!k) return "";
  if (DAY_ALIASES[k]) return DAY_ALIASES[k];
  const k3 = k.slice(0, 3);
  return DAY_ALIASES[k3] || s;
}

function parseStartMinutes(timeRange) {
  const s = String(timeRange || "").trim();
  const m = s.match(/(\d{1,2}):(\d{2})/);
  if (!m) return 99999;
  const hh = Number(m[1]);
  const mm = Number(m[2]);
  if (Number.isNaN(hh) || Number.isNaN(mm)) return 99999;
  return hh * 60 + mm;
}

function parseLabel(label, timeslotId) {
  const s = String(label || "").trim();
  const id = String(timeslotId || "").trim();

  if (s.includes(",")) {
    const parts = s.split(",");
    const dayRaw = (parts[0] || "").trim();
    const day = normDay(dayRaw.includes("_") ? dayRaw.split("_")[0] : dayRaw);
    const time = (parts[1] || "").trim();
    return { day, time };
  }

  const fromId = id.includes("_") ? id.split("_")[0] : "";
  const dayFromId = normDay(fromId);

  const withDayInText = s.match(/^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(.+)$/i);
  if (withDayInText) {
    return { day: normDay(withDayInText[1]), time: String(withDayInText[2]).trim() };
  }

  const withDayInText2 = s.match(/^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(.+)$/i);
  if (withDayInText2) {
    return { day: normDay(withDayInText2[1]), time: String(withDayInText2[2]).trim() };
  }

  const day = dayFromId || "";
  const time = s || id || "";
  return { day, time };
}

export default function TimetableGrid({ mode, selected, schedule = [], byGroup = [] }) {
  const rows = useMemo(() => {
    if (!selected) return [];
    if (mode === "group") return byGroup.filter((r) => String(r.group) === String(selected));
    if (mode === "teacher") return schedule.filter((r) => String(r.teacher) === String(selected));
    if (mode === "room") return schedule.filter((r) => String(r.room) === String(selected));
    return [];
  }, [mode, selected, schedule, byGroup]);

  const slots = useMemo(() => {
    const m = new Map();
    const daySet = new Set();

    for (const r of rows) {
      const { day, time } = parseLabel(r.timeslot_label, r.timeslot_id);
      if (!time) continue;

      const d = normDay(day);
      if (d) daySet.add(d);

      if (!m.has(time)) m.set(time, new Map());
      const rowMap = m.get(time);

      const keyDay = d || "Unknown";
      if (!rowMap.has(keyDay)) rowMap.set(keyDay, []);
      rowMap.get(keyDay).push(r);
    }

    const times = Array.from(m.keys()).sort((a, b) => {
      const am = parseStartMinutes(a);
      const bm = parseStartMinutes(b);
      if (am !== bm) return am - bm;
      return String(a).localeCompare(String(b));
    });

    const days = DAY_ORDER.filter((d) => daySet.has(d));
    return { times, days, m };
  }, [rows]);

  if (!rows.length) return <div style={{ color: "#666" }}>No rows for selection</div>;

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th style={{ borderBottom: "1px solid #ddd", textAlign: "left", padding: 8, whiteSpace: "nowrap" }}>
              Time
            </th>
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
              <td style={{ borderBottom: "1px solid #eee", padding: 8, whiteSpace: "nowrap", fontWeight: 700 }}>
                {t}
              </td>
              {slots.days.map((d) => {
                const items = slots.m.get(t)?.get(d) || [];
                return (
                  <td
                    key={d}
                    style={{
                      borderBottom: "1px solid #eee",
                      padding: 8,
                      minWidth: 260,
                      verticalAlign: "top",
                      lineHeight: 1.25,
                    }}
                  >
                    {items.map((cell, i) => {
                      const text =
                        mode === "group"
                          ? `${cell.course} · ${cell.teacher} · ${cell.room}`
                          : `${cell.course} · ${cell.teacher} · ${cell.room} · ${cell.session_id}`;
                      return (
                        <div
                          key={i}
                          style={{
                            border: "1px solid #eee",
                            borderRadius: 10,
                            padding: "8px 10px",
                            marginBottom: 6,
                            background: "#fff",
                            overflowWrap: "anywhere",
                            wordBreak: "break-word",
                          }}
                          title={text}
                        >
                          {text}
                        </div>
                      );
                    })}
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
