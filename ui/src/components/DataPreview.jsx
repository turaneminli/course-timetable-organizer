import React, { useState } from "react";
import SimpleTable from "./SimpleTable.jsx";

export default function DataPreview({ preview }) {
  const [tab, setTab] = useState("sessions");
  const inst = preview.instance;

  const tabs = [
    ["sessions", "Sessions"],
    ["rooms", "Rooms"],
    ["timeslots", "Timeslots"],
    ["teachers", "Teachers"],
    ["groups", "Groups"],
    ["teacher_availability", "Teacher Availability"]
  ];

  const data = inst?.[tab];

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div style={{ fontWeight: 800 }}>Preview: {preview.name}</div>
        <div style={{ color: "#666" }}>instance_id: {preview.instance_id}</div>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
        {tabs.map(([k, label]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            style={{
              padding: "8px 10px",
              borderRadius: 999,
              border: "1px solid #333",
              background: tab === k ? "#111" : "#fff",
              color: tab === k ? "#fff" : "#111"
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <div style={{ height: 12 }} />
      <div style={{ color: "#666" }}>{JSON.stringify(inst.summary)}</div>
      <div style={{ height: 12 }} />

      <SimpleTable data={data} />
    </div>
  );
}
