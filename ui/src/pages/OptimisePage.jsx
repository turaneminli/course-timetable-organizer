import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { createJobFromInstanceId, getJob } from "../api.js";
import Controls from "../components/Controls.jsx";
import ProgressChart from "../components/ProgressChart.jsx";

export default function OptimisePage() {
  const { instanceId } = useParams();
  const nav = useNavigate();

  const [params, setParams] = React.useState({
    pop: 200,
    gen: 1000,
    seed: 42,
    repair: true,
    workers: 4,
    log_every: 20,
    repair_attempts_per_gene: 25,
    repair_max_rounds: 4
  });

  const [job, setJob] = React.useState(null);
  const [err, setErr] = React.useState("");

  const running = job && (job.status === "queued" || job.status === "running");
  const history = (job?.history || []).map(([gen, total, hard, soft]) => ({ gen, total, hard, soft }));

  async function start() {
    setErr("");
    try {
      const j = await createJobFromInstanceId(instanceId, params);
      setJob(j);
    } catch (e) {
      setErr(String(e));
    }
  }

  React.useEffect(() => {
    if (!job) return;
    let stopped = false;

    async function tick() {
      try {
        const j = await getJob(job.id);
        if (stopped) return;
        setJob(j);
        if (j.status === "done") nav(`/result/${j.id}`);
      } catch (e) {
        if (!stopped) setErr(String(e));
      }
    }

    tick();
    const id = setInterval(() => tick(), 900);
    return () => {
      stopped = true;
      clearInterval(id);
    };
  }, [job?.id]);

  return (
    <div>
      <h2 style={{ margin: 0 }}>Optimise</h2>
      <div style={{ color: "#666", marginTop: 6 }}>Instance ID: {instanceId}</div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
        <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12 }}>
          <div style={{ fontWeight: 700 }}>Settings</div>
          <div style={{ height: 10 }} />
          <Controls params={params} onChange={setParams} disabled={running} />
          <div style={{ height: 12 }} />
          <button
            onClick={start}
            disabled={running}
            style={{
              padding: "10px 12px",
              borderRadius: 10,
              border: "1px solid #333",
              background: running ? "#eee" : "#111",
              color: running ? "#666" : "#fff",
              cursor: running ? "not-allowed" : "pointer"
            }}
          >
            {running ? "Running..." : "Start Optimisation"}
          </button>
          {err ? <div style={{ marginTop: 10, color: "#b00020", whiteSpace: "pre-wrap" }}>{err}</div> : null}
        </div>

        <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <div style={{ fontWeight: 700 }}>Progress</div>
            <div style={{ color: "#666" }}>status: {job ? job.status : "-"}</div>
          </div>
          <div style={{ height: 10 }} />
          <ProgressChart history={history} />
        </div>
      </div>
    </div>
  );
}
