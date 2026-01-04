import React from "react";

export default function Controls({ params, onChange, disabled }) {
  function set(k, v) {
    onChange({ ...params, [k]: v });
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
      <label>
        <div>pop</div>
        <input disabled={disabled} type="number" value={params.pop} onChange={(e) => set("pop", Number(e.target.value))} />
      </label>
      <label>
        <div>gen</div>
        <input disabled={disabled} type="number" value={params.gen} onChange={(e) => set("gen", Number(e.target.value))} />
      </label>
      <label>
        <div>seed</div>
        <input disabled={disabled} type="number" value={params.seed} onChange={(e) => set("seed", Number(e.target.value))} />
      </label>
      <label>
        <div>workers</div>
        <input disabled={disabled} type="number" value={params.workers} onChange={(e) => set("workers", Number(e.target.value))} />
      </label>
      <label>
        <div>log_every</div>
        <input disabled={disabled} type="number" value={params.log_every} onChange={(e) => set("log_every", Number(e.target.value))} />
      </label>
      <label style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 22 }}>
        <input disabled={disabled} type="checkbox" checked={params.repair} onChange={(e) => set("repair", e.target.checked)} />
        <span>repair</span>
      </label>

      <label>
        <div>repair_attempts</div>
        <input disabled={disabled} type="number" value={params.repair_attempts_per_gene} onChange={(e) => set("repair_attempts_per_gene", Number(e.target.value))} />
      </label>
      <label>
        <div>repair_rounds</div>
        <input disabled={disabled} type="number" value={params.repair_max_rounds} onChange={(e) => set("repair_max_rounds", Number(e.target.value))} />
      </label>
    </div>
  );
}
