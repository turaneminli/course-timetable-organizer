import React from "react";

export default function ValidationPanel({ validation }) {
  if (!validation) {
    return (
      <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12, color: "#666" }}>
        No validation data
      </div>
    );
  }

  const counts = validation.hard?.counts || {};
  const hardTotal = validation.hard_total;

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12 }}>
      <div style={{ fontWeight: 800 }}>Validation</div>
      <div style={{ marginTop: 6, fontWeight: 700 }}>
        {hardTotal === 0 ? "Hard constraints OK" : `Hard violations detected: ${hardTotal}`}
      </div>

      <div style={{ marginTop: 10, color: "#666" }}>
        room_collisions={counts.room_collisions || 0} • teacher_collisions={counts.teacher_collisions || 0} • group_collisions={counts.group_collisions || 0} • capacity={counts.capacity || 0} • room_type={counts.room_type || 0} • availability={counts.availability || 0}
      </div>

      <div style={{ height: 12 }} />
      <div style={{ fontWeight: 700 }}>Top gap groups</div>
      <div style={{ height: 6 }} />
      <div style={{ color: "#666" }}>
        total_gaps={validation.soft?.total_gaps ?? "-"}
      </div>

      <div style={{ height: 10 }} />
      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #ddd" }}>group</th>
              <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #ddd" }}>gaps</th>
            </tr>
          </thead>
          <tbody>
            {(validation.soft?.gaps_by_group_top || []).map((r, i) => (
              <tr key={i}>
                <td style={{ padding: 8, borderBottom: "1px solid #eee" }}>{r.group}</td>
                <td style={{ padding: 8, borderBottom: "1px solid #eee" }}>{r.gaps}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
