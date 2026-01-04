import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { previewInstance } from "../api.js";
import DataPreview from "../components/DataPreview.jsx";

export default function UploadPage() {
  const nav = useNavigate();
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [err, setErr] = useState("");

  async function onPreview() {
    setErr("");
    setPreview(null);
    if (!file) return setErr("Select a JSON file.");
    try {
      const res = await previewInstance(file);
      setPreview(res);
    } catch (e) {
      setErr(String(e));
    }
  }

  return (
    <div>
      <h2 style={{ margin: 0 }}>University Timetable Tool</h2>
      <div style={{ color: "#666", marginTop: 6 }}>Upload your current data, review it, then optimise.</div>

      <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12, marginTop: 16 }}>
        <div style={{ fontWeight: 700 }}>Upload</div>
        <div style={{ height: 8 }} />
        <input type="file" accept=".json,application/json" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <div style={{ color: "#666", marginTop: 6 }}>{file ? file.name : "No file selected"}</div>

        <div style={{ height: 10 }} />
        <button
          onClick={onPreview}
          style={{ padding: "10px 12px", borderRadius: 10, border: "1px solid #333", background: "#111", color: "#fff" }}
        >
          Preview Data
        </button>

        {err ? <div style={{ marginTop: 10, color: "#b00020", whiteSpace: "pre-wrap" }}>{err}</div> : null}
      </div>

      {preview ? (
        <div style={{ marginTop: 16 }}>
          <DataPreview preview={preview} />
          <div style={{ height: 12 }} />
          <button
            onClick={() => nav(`/optimise/${preview.instance_id}`)}
            style={{ padding: "10px 12px", borderRadius: 10, border: "1px solid #333", background: "#0b5", color: "#fff" }}
          >
            Continue to Optimisation
          </button>
        </div>
      ) : null}
    </div>
  );
}
