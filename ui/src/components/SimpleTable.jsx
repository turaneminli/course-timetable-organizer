import React from "react";

export default function SimpleTable({ data }) {
  if (!data) return <div style={{ color: "#666" }}>No data</div>;

  if (Array.isArray(data)) {
    if (data.length === 0) return <div style={{ color: "#666" }}>Empty</div>;

    const first = data[0];
    const isObjectRow = first !== null && typeof first === "object" && !Array.isArray(first);

    if (!isObjectRow) {
      return (
        <div style={{ overflowX: "auto" }}>
          <table style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #ddd" }}>#</th>
                <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #ddd" }}>Value</th>
              </tr>
            </thead>
            <tbody>
              {data.slice(0, 250).map((v, i) => (
                <tr key={i}>
                  <td style={{ padding: 8, borderBottom: "1px solid #eee", verticalAlign: "top", color: "#666" }}>
                    {i + 1}
                  </td>
                  <td style={{ padding: 8, borderBottom: "1px solid #eee", verticalAlign: "top" }}>
                    {String(v)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.length > 250 ? <div style={{ color: "#666", marginTop: 8 }}>Showing first 250 rows</div> : null}
        </div>
      );
    }

    const cols = Object.keys(first);

    return (
      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              {cols.map((c) => (
                <th key={c} style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #ddd" }}>
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 250).map((row, i) => (
              <tr key={i}>
                {cols.map((c) => (
                  <td key={c} style={{ padding: 8, borderBottom: "1px solid #eee", verticalAlign: "top" }}>
                    {row[c] !== null && typeof row[c] === "object" ? JSON.stringify(row[c]) : String(row[c])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {data.length > 250 ? <div style={{ color: "#666", marginTop: 8 }}>Showing first 250 rows</div> : null}
      </div>
    );
  }

  if (typeof data === "object") {
    const rows = Object.entries(data).slice(0, 250).map(([k, v]) => ({ key: k, value: v }));
    return <SimpleTable data={rows} />;
  }

  return <div>{String(data)}</div>;
}
