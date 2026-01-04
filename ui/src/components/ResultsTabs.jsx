import React, { useMemo, useState } from "react";
import TimetableGrid from "./TimetableGrid.jsx";

export default function ResultsTabs({ result }) {
  const [mode, setMode] = useState("group");
  const [key, setKey] = useState("");

  const schedule = result?.schedule || [];
  const byGroup = result?.by_group || [];

  const keys = useMemo(() => {
    if (!result) return [];
    if (mode === "group") return Array.from(new Set(byGroup.map((r) => r.group))).sort();
    if (mode === "teacher") return Array.from(new Set(schedule.map((r) => r.teacher))).sort();
    if (mode === "room") return Array.from(new Set(schedule.map((r) => r.room))).sort();
    return [];
  }, [result, mode]);

  React.useEffect(() => {
    if (!keys.length) return;
    if (!key || !keys.includes(key)) setKey(keys[0]);
  }, [keys.join("|"), mode]);

  if (!result) {
    return <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12, color: "#666" }}>No results yet</div>;
  }

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12 }}>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <div style={{ fontWeight: 700 }}>Result Viewer</div>
        <select value={mode} onChange={(e) => setMode(e.target.value)}>
          <option value="group">Group</option>
          <option value="teacher">Teacher</option>
          <option value="room">Room</option>
        </select>
        <select value={key} onChange={(e) => setKey(e.target.value)} style={{ minWidth: 220 }}>
          {keys.map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
        <div style={{ marginLeft: "auto", color: "#666" }}>
          verify hard={result.verify_penalty?.hard} soft={result.verify_penalty?.soft}
        </div>
      </div>

      <div style={{ height: 12 }} />

      <TimetableGrid mode={mode} selected={key} schedule={schedule} byGroup={byGroup} />
    </div>
  );
}
