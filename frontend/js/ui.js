// ── Icons ────────────────────────────────────────────────────────────────────
const I = {
  mic:         `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg>`,
  cpu:         `<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>`,
  upload:      `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>`,
  file:        `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>`,
  x:           `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
  zap:         `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  loader:      `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/></svg>`,
  copy:        `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`,
  check:       `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  download:    `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
  plus:        `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`,
  alert:       `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  ok:          `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
  chevDown:    `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`,
  chevUp:      `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>`,
  eye:         `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`,
};

// ── Toast ─────────────────────────────────────────────────────────────────────
export function toast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = 'toast';
  const iconSvg = type === 'error' ? I.alert : I.ok;
  const color = type === 'error' ? 'var(--err)' : 'var(--ok)';
  el.innerHTML = `<span class="toast-icon" style="color:${color}">${iconSvg}</span><span class="toast-text">${msg}</span>`;
  container.appendChild(el);
  setTimeout(() => {
    el.classList.add('hiding');
    el.addEventListener('animationend', () => el.remove());
  }, 4000);
}

// ── Screen switching ──────────────────────────────────────────────────────────
export function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const el = document.getElementById(id);
  if (el) { el.style.display = ''; el.classList.add('active'); }
}

// ── Stage 1 ───────────────────────────────────────────────────────────────────
export function setDownloadProgress(percent, currentMb, totalMb) {
  const fill = document.getElementById('dl-fill');
  const info = document.getElementById('dl-info-right');
  const status = document.getElementById('dl-status');
  if (fill) fill.style.width = percent + '%';
  if (info) info.textContent = `${currentMb} МБ / ${totalMb} МБ`;
  if (status) status.textContent = 'Загрузка весов модели...';
}

export function setDownloadDone() {
  const fill = document.getElementById('dl-fill');
  const status = document.getElementById('dl-status');
  const info = document.getElementById('dl-info-right');
  if (fill) { fill.style.width = '100%'; fill.classList.add('done'); }
  if (status) status.innerHTML = `<span style="color:var(--ok)">${I.check} Модель установлена</span>`;
  if (info) info.textContent = '';
}

export function showDownloadBlock() {
  document.getElementById('install-btn').classList.add('hidden');
  document.getElementById('download-block').style.display = 'block';
}

export function setModelLoaded(loaded) {
  const dot = document.getElementById('status-dot');
  if (dot) dot.classList.toggle('active', loaded);
}

// ── File list ─────────────────────────────────────────────────────────────────
function fileIconClass(name) {
  return ['flac'].includes(name.split('.').pop().toLowerCase()) ? 'lossless' : 'audio';
}

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + ' КБ';
  return (bytes / 1024 / 1024).toFixed(1) + ' МБ';
}

export function renderFileList(files, onRemove) {
  const list = document.getElementById('file-list');
  const summary = document.getElementById('file-summary');
  list.innerHTML = '';
  files.forEach((f, i) => {
    const row = document.createElement('div');
    row.className = 'file-row';
    row.innerHTML = `
      <span class="file-icon ${fileIconClass(f.name)}">${I.file}</span>
      <span class="file-name" title="${f.name}">${f.name}</span>
      <span class="file-size">${formatBytes(f.size)}</span>
      <button class="file-remove" aria-label="Удалить">${I.x}</button>`;
    row.querySelector('.file-remove').addEventListener('click', () => onRemove(i));
    list.appendChild(row);
  });
  if (files.length > 1) {
    const total = files.reduce((s, f) => s + f.size, 0);
    summary.textContent = `Итого: ${files.length} файлов · ${formatBytes(total)}`;
  } else { summary.textContent = ''; }
}

// ── Settings ──────────────────────────────────────────────────────────────────
export function getSettings() {
  const fmt = document.querySelector('.seg-btn.active')?.dataset.fmt || 'txt';
  const chunkSize = parseInt(document.getElementById('chunk-slider').value, 10);
  const useVad = document.getElementById('vad-toggle').checked;
  const deviceEl = document.querySelector('input[name="device"]:checked');
  return { fmt, chunkSize, useVad, device: deviceEl ? deviceEl.value : 'cpu' };
}

export function setTranscribeButtonState(enabled) {
  document.getElementById('transcribe-btn').disabled = !enabled;
}

// ── Progress ──────────────────────────────────────────────────────────────────
export function showProgressBlock(show) {
  document.getElementById('progress-block').style.display = show ? 'block' : 'none';
  document.getElementById('transcribe-btn').style.display = show ? 'none' : '';
}

export function updateProgress(status) {
  const statusEl = document.getElementById('prog-status-text');
  const fileFill = document.getElementById('prog-file-fill');
  const chunkFill = document.getElementById('prog-chunk-fill');
  const fileLabel = document.getElementById('prog-file-label');
  const chunkLabel = document.getElementById('prog-chunk-label');

  if (statusEl) statusEl.innerHTML = `<span class="spin" style="display:inline-flex">${I.loader}</span> Обрабатывается: ${status.current_file || '…'}`;
  const fp = status.total_files > 0 ? (status.done_files / status.total_files) * 100 : 0;
  const cp = status.total_chunks > 0 ? (status.done_chunks / status.total_chunks) * 100 : 0;
  if (fileFill) fileFill.style.width = fp + '%';
  if (chunkFill) chunkFill.style.width = cp + '%';
  if (fileLabel) fileLabel.textContent = `Файл ${status.done_files} из ${status.total_files}`;
  if (chunkLabel) chunkLabel.textContent = status.total_chunks > 0 ? `Чанк ${status.done_chunks} из ${status.total_chunks}` : '';
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function elapsed(sec) {
  if (!sec) return '';
  const m = Math.floor(sec / 60), s = Math.round(sec % 60);
  return m > 0 ? `${m} мин ${s} с` : `${s} с`;
}

function fullText(fr) {
  return (fr.chunks || []).map(c => c.text || '').join(' ').trim();
}

function wordCount(text) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

async function copyText(text, btn, original) {
  try {
    await navigator.clipboard.writeText(text);
    btn.innerHTML = `<span style="color:var(--ok)">${I.check}</span> Скопировано`;
    setTimeout(() => { btn.innerHTML = original; }, 2000);
  } catch { toast('Не удалось скопировать', 'error'); }
}

// ── Results ───────────────────────────────────────────────────────────────────
export function renderResults(taskData, taskId, fmt, _onPreview) {
  const container = document.getElementById('result-cards');
  container.innerHTML = '';

  const sub = document.getElementById('results-sub');
  if (sub) {
    const el = taskData.elapsed ? `· обработано за ${elapsed(taskData.elapsed)}` : '';
    sub.textContent = `${taskData.total_files} файлов ${el}`;
  }

  const results = taskData.results || [];
  if (results.length === 0) {
    container.innerHTML = `<div style="color:var(--text-3);font-size:13px;padding:20px 0">Нет результатов</div>`;
    return;
  }

  results.forEach(fr => {
    const card = document.createElement('div');
    card.className = 'result-card';

    if (fr.error) {
      card.innerHTML = `
        <div class="card-header">
          <div class="card-file">
            <div class="card-filename">${I.file} ${fr.filename}</div>
            <div class="card-meta" style="color:var(--err)">${fr.error}</div>
          </div>
        </div>
        <div class="card-error">
          <span style="color:var(--err)">${I.alert}</span>
          <div class="card-error-text">Не удалось обработать файл<br><span style="opacity:.7">${fr.error}</span></div>
        </div>`;
      container.appendChild(card);
      return;
    }

    const text = fullText(fr);
    const wc = wordCount(text);
    const isExpanded = { val: false };

    card.innerHTML = `
      <div class="card-header">
        <div class="card-file">
          <div class="card-filename">${I.file} ${fr.filename}</div>
          <div class="card-meta">${fr.duration ? elapsed(fr.duration) : ''} · ${wc} слов · ${fmt.toUpperCase()}</div>
        </div>
        <div class="card-actions">
          <button class="btn btn-ghost btn-copy-card">${I.copy} Копировать</button>
          <a class="btn btn-ghost btn-download"
             href="/api/task/${taskId}/download?file=${encodeURIComponent(fr.filename)}&fmt=${fmt}"
             download>${I.download} Скачать</a>
          <button class="btn btn-ghost btn-toggle">${I.chevDown} Развернуть</button>
        </div>
      </div>
      <div class="card-body" style="display:none">
        <div class="card-fulltext"></div>
        <div class="card-foot">
          <span class="card-foot-stats">${wc} слов · ${text.length} символов</span>
          <button class="btn btn-ghost btn-copy-full">${I.copy} Копировать всё</button>
        </div>
      </div>`;

    const body = card.querySelector('.card-body');
    const fullEl = card.querySelector('.card-fulltext');
    const toggleBtn = card.querySelector('.btn-toggle');

    // Render text body based on format
    if (fmt === 'srt') {
      fullEl.innerHTML = renderSrtInline(fr.chunks || []);
    } else if (fmt === 'json') {
      fullEl.innerHTML = renderJsonInline(fr);
    } else {
      fullEl.textContent = text;
      fullEl.style.cssText = 'font-size:14px;color:#E0E0E0;line-height:1.8;white-space:pre-wrap;word-break:break-word;padding:20px';
    }

    toggleBtn.addEventListener('click', () => {
      isExpanded.val = !isExpanded.val;
      body.style.display = isExpanded.val ? 'block' : 'none';
      toggleBtn.innerHTML = isExpanded.val
        ? `${I.chevUp} Свернуть`
        : `${I.chevDown} Развернуть`;
    });

    const copyOrig = `${I.copy} Копировать`;
    card.querySelector('.btn-copy-card').addEventListener('click', e => copyText(text, e.currentTarget, copyOrig));
    card.querySelector('.btn-copy-full').addEventListener('click', e => copyText(text, e.currentTarget, `${I.copy} Копировать всё`));

    container.appendChild(card);
  });
}

function renderSrtInline(chunks) {
  const ts = t => {
    const h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = Math.floor(t % 60);
    const ms = Math.round((t - Math.floor(t)) * 1000);
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')},${String(ms).padStart(3,'0')}`;
  };
  const blocks = chunks.filter(c => c.text).map(c =>
    `<div class="srt-block"><div class="srt-ts">${ts(c.start)} --> ${ts(c.end)}</div><div class="srt-text">${c.text.replace(/</g,'&lt;')}</div></div>`
  ).join('');
  return `<div style="padding:20px">${blocks}</div>`;
}

function renderJsonInline(fr) {
  const text = (fr.chunks || []).map(c => c.text || '').join(' ');
  const data = { filename: fr.filename, chunks: fr.chunks || [], full_text: text };
  const hl = JSON.stringify(data, null, 2)
    .replace(/("[\w]+"): /g, '<span class="json-key">$1</span>: ')
    .replace(/: (".*?")/g, ': <span class="json-str">$1</span>')
    .replace(/: (\d+\.?\d*)/g, ': <span class="json-num">$1</span>');
  return `<div class="json-view" style="padding:20px">${hl}</div>`;
}

// ── Modal (kept for backward compat, not actively used) ───────────────────────
export function openModal() {}
