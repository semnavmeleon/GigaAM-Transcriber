const BASE = '';

async function apiFetch(path, options = {}) {
  const res = await fetch(BASE + path, options);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const j = await res.json(); msg = j.detail || msg; } catch {}
    throw new Error(msg);
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res;
}

export const api = {
  modelStatus: () => apiFetch('/api/model/status'),
  modelDownload: () => apiFetch('/api/model/download', { method: 'POST' }),
  modelDownloadProgress: () => apiFetch('/api/model/download-progress'),

  transcribe(files, settings) {
    const fd = new FormData();
    for (const f of files) fd.append('files', f);
    fd.append('fmt', settings.fmt);
    fd.append('chunk_size', String(settings.chunkSize));
    fd.append('use_vad', String(settings.useVad));
    fd.append('device', settings.device);
    return apiFetch('/api/transcribe', { method: 'POST', body: fd });
  },

  taskStatus: (id) => apiFetch(`/api/task/${id}/status`),
  cancelTask: (id) => apiFetch(`/api/task/${id}`, { method: 'DELETE' }),

  downloadUrl(taskId, filename, fmt) {
    return `/api/task/${taskId}/download?file=${encodeURIComponent(filename)}&fmt=${fmt}`;
  },
};
