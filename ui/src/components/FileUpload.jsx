import React from "react";

export default function FileUpload({ file, onChange }) {
  return (
    <div>
      <div style={{ fontWeight: 600 }}>Instance JSON</div>
      <input
        type="file"
        accept=".json,application/json"
        onChange={(e) => onChange(e.target.files?.[0] || null)}
      />
      <div style={{ color: "#666", marginTop: 6 }}>{file ? file.name : "No file selected"}</div>
    </div>
  );
}
