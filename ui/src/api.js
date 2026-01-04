export async function previewInstance(file) {
  const fd = new FormData();
  fd.append("instance", file);
  const res = await fetch("/api/instances/preview", {
    method: "POST",
    body: fd,
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function createJobFromInstanceId(instanceId, params) {
  const fd = new FormData();
  fd.append("instance_id", instanceId);
  Object.entries(params).forEach(([k, v]) => fd.append(k, String(v)));
  const res = await fetch("/api/jobs", { method: "POST", body: fd });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function getJob(jobId) {
  const res = await fetch(`/api/jobs/${jobId}`);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function getResult(jobId) {
  const res = await fetch(`/api/jobs/${jobId}/result`);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}
