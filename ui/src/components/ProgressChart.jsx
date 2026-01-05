import React from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

export default function ProgressChart({ history }) {
  if (!history || history.length === 0) {
    return <div style={{ color: "#666" }}>No history yet</div>;
  }

  const data = history.map((d) => ({
    gen: d.gen,
    total: d.total,
    hard_scaled: d.hard * 1000,
    soft: d.soft,
  }));

  return (
    <div style={{ width: "100%", height: 260 }}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <XAxis dataKey="gen" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="total" stroke="red" dot={false} />
          <Line type="monotone" dataKey="hard_scaled" name="hard (x1000)" stroke="green" dot={false} />
          <Line type="monotone" dataKey="soft" stroke="blue" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
