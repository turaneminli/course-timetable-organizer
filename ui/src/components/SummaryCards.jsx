import React from "react";

function card(title, value) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12 }}>
      <div style={{ color: "#666" }}>{title}</div>
      <div style={{ fontSize: 20, fontWeight: 700, marginTop: 6 }}>{value}</div>
    </div>
  );
}

export default function SummaryCards({ job, result }) {
  const status = job ? job.status : "-";
  const gen = job?.history?.length ? job.history[job.history.length - 1][0] : "-";
  const total = result?.penalty?.total ?? "-";
  const hard = result?.penalty?.hard ?? "-";
  const soft = result?.penalty?.soft ?? "-";

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12 }}>
      {card("status", status)}
      {card("last_gen", gen)}
      {card("total", total)}
      {card("hard", hard)}
      {card("soft", soft)}
    </div>
  );
}
