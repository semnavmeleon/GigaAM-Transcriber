const BASE = '';

async function apiFetch(path, options = {}) {
  const res = await fetch(BASE + path, options);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const j = await res.json(); msg = j.detail || msg; } catch {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res;
}

export const api = {
  systemInfo: () => apiFetch('/api/system/info'),

  // Model management
  installModel(variant) {
    const fd = new FormData();
    fd.append('variant', variant);
    return apiFetch('/api/model/install', { method: 'POST', body: fd });
  },
  uninstallModel: (variant) => apiFetch(`/api/model/${variant}`, { method: 'DELETE' }),
  setActiveModel(variant) {
    const fd = new FormData();
    fd.append('variant', variant);
    return apiFetch('/api/model/set-active', { method: 'POST', body: fd });
  },
  modelProgress: (variant) => apiFetch(`/api/model/progress/${variant}`),

  // Punctuation management
  installPunct: () => apiFetch('/api/punctuation/install', { method: 'POST' }),
  uninstallPunct: () => apiFetch('/api/punctuation', { method: 'DELETE' }),
  punctProgress: () => apiFetch('/api/punctuation/progress'),

  // Transcription
  transcribe(files, settings) {
    const fd = new FormData();
    for (const f of files) fd.append('files', f);
    fd.append('fmt', settings.fmt);
    fd.append('chunk_size', String(settings.chunkSize));
    fd.append('use_vad', String(settings.useVad));
    fd.append('use_punctuation', String(settings.usePunctuation));
    fd.append('device', settings.device);
    return apiFetch('/api/transcribe', { method: 'POST', body: fd });
  },

  taskStatus: (id) => apiFetch(`/api/task/${id}/status`),
  cancelTask: (id) => apiFetch(`/api/task/${id}`, { method: 'DELETE' }),

  downloadUrl(taskId, filename, fmt) {
    return `/api/task/${taskId}/download?file=${encodeURIComponent(filename)}&fmt=${fmt}`;
  },
};
