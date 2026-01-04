import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getResult } from "../api.js";
import ResultsTabs from "../components/ResultsTabs.jsx";
import ValidationPanel from "../components/ValidationPanel.jsx";

export default function ResultPage() {
  const { jobId } = useParams();
  const nav = useNavigate();
  const [result, setResult] = React.useState(null);
  const [err, setErr] = React.useState("");

  React.useEffect(() => {
    let stopped = false;
    async function load() {
      setErr("");
      try {
        const r = await getResult(jobId);
        if (!stopped) setResult(r);
      } catch (e) {
        if (!stopped) setErr(String(e));
      }
    }
    load();
    return () => {
      stopped = true;
    };
  }, [jobId]);

  if (err) return <div style={{ color: "#b00020", whiteSpace: "pre-wrap" }}>{err}</div>;
  if (!result) return <div style={{ color: "#666" }}>Loading...</div>;

  const hard = result.verify_penalty?.hard ?? result.penalty?.hard;
  const soft = result.verify_penalty?.soft ?? result.penalty?.soft;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h2 style={{ margin: 0 }}>Result</h2>
        <button onClick={() => nav("/upload")} style={{ padding: "8px 10px", borderRadius: 10, border: "1px solid #333" }}>
          New Upload
        </button>
      </div>

      <div style={{ marginTop: 10, padding: 12, borderRadius: 12, border: "1px solid #ddd" }}>
        <div style={{ fontWeight: 800, fontSize: 16 }}>
          {hard === 0 ? "Feasible timetable found (hard=0)" : `Not feasible (hard=${hard})`}
        </div>
        <div style={{ color: "#666", marginTop: 6 }}>soft={soft}</div>
      </div>

      <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <ValidationPanel validation={result.validation} />
        <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12 }}>
          <div style={{ fontWeight: 800 }}>Uploaded Data Summary</div>
          <div style={{ color: "#666", marginTop: 6 }}>{JSON.stringify(result.instance?.summary || {}, null, 2)}</div>
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <ResultsTabs result={result} />
      </div>
    </div>
  );
}
