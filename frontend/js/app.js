import { api } from './api.js';
import * as ui from './ui.js';

// ── State ─────────────────────────────────────────────────────────────────────
let selectedFiles = [];
let currentTaskId = null;
let pollInterval = null;
let modelVariant = 'v2_ctc';

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  setupStage2();
  try {
    const status = await api.modelStatus();
    modelVariant = status.variant || 'e2e_ctc';
    document.getElementById('model-badge').textContent = `v3 ${modelVariant}`;
    if (status.loaded) {
      ui.setModelLoaded(true);
      ui.showScreen('stage2');
    } else {
      ui.showScreen('stage1');
    }
  } catch (e) {
    ui.showScreen('stage1');
  }
}

// ── Stage 1: model install ────────────────────────────────────────────────────
document.getElementById('install-btn').addEventListener('click', async () => {
  ui.showDownloadBlock();
  try {
    await api.modelDownload();
    pollDownload();
  } catch (e) {
    ui.toast('Ошибка запуска загрузки: ' + e.message, 'error');
  }
});

function pollDownload() {
  const iv = setInterval(async () => {
    try {
      const prog = await api.modelDownloadProgress();
      ui.setDownloadProgress(prog.percent, prog.current_mb || 0, prog.total_mb || 900);
      if (prog.done) {
        clearInterval(iv);
        ui.setDownloadDone();
        ui.setModelLoaded(true);
        setTimeout(() => ui.showScreen('stage2'), 1500);
      } else if (prog.error) {
        clearInterval(iv);
        ui.toast('Ошибка загрузки модели: ' + prog.error, 'error');
      }
    } catch {}
  }, 2000);
}

// ── Stage 2: file upload & settings ──────────────────────────────────────────
function setupStage2() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');

  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
  dropzone.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    addFiles(Array.from(e.dataTransfer.files));
  });
  fileInput.addEventListener('change', () => addFiles(Array.from(fileInput.files)));

  // Segmented control
  document.querySelectorAll('.seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // Chunk slider
  const slider = document.getElementById('chunk-slider');
  const sliderVal = document.getElementById('chunk-value');
  slider.addEventListener('input', () => { sliderVal.textContent = slider.value + ' с'; });

  // Transcribe button
  document.getElementById('transcribe-btn').addEventListener('click', startTranscription);

  // Cancel button
  document.getElementById('cancel-btn').addEventListener('click', async () => {
    if (currentTaskId) {
      try { await api.cancelTask(currentTaskId); } catch {}
      stopPoll();
      ui.showProgressBlock(false);
      ui.setTranscribeButtonState(selectedFiles.length > 0);
      ui.toast('Задача отменена');
    }
  });

  // "Process more" button
  document.getElementById('more-btn').addEventListener('click', () => {
    selectedFiles = [];
    currentTaskId = null;
    ui.renderFileList([], () => {});
    ui.setTranscribeButtonState(false);
    ui.showProgressBlock(false);
    ui.showScreen('stage2');
  });
}

const AUDIO_EXTS = new Set(['mp3', 'wav', 'm4a', 'ogg', 'flac', 'opus']);
const VIDEO_EXTS = new Set(['mp4', 'mkv', 'avi', 'mov', 'webm', 'ts', 'm2ts']);

function addFiles(incoming) {
  const MAX_SIZE = 500 * 1024 * 1024;
  for (const f of incoming) {
    const ext = f.name.split('.').pop().toLowerCase();
    if (!AUDIO_EXTS.has(ext) && !VIDEO_EXTS.has(ext)) { ui.toast(`Формат .${ext} не поддерживается`, 'error'); continue; }
    if (f.size > MAX_SIZE) { ui.toast(`${f.name} превышает 500 МБ`, 'error'); continue; }
    if (selectedFiles.length >= 10) { ui.toast('Максимум 10 файлов за раз', 'error'); break; }
    if (!selectedFiles.find(s => s.name === f.name && s.size === f.size)) selectedFiles.push(f);
  }
  ui.renderFileList(selectedFiles, removeFile);
  ui.setTranscribeButtonState(selectedFiles.length > 0);
}

function removeFile(idx) {
  selectedFiles.splice(idx, 1);
  ui.renderFileList(selectedFiles, removeFile);
  ui.setTranscribeButtonState(selectedFiles.length > 0);
}

async function startTranscription() {
  if (!selectedFiles.length) return;
  const settings = ui.getSettings();

  ui.showProgressBlock(true);

  try {
    const { task_id } = await api.transcribe(selectedFiles, settings);
    currentTaskId = task_id;
    pollTask(task_id, settings.fmt);
  } catch (e) {
    ui.toast('Ошибка запуска транскрибации: ' + e.message, 'error');
    ui.showProgressBlock(false);
    ui.setTranscribeButtonState(true);
  }
}

function stopPoll() {
  if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
}

function pollTask(taskId, fmt) {
  stopPoll();
  pollInterval = setInterval(async () => {
    try {
      const status = await api.taskStatus(taskId);
      ui.updateProgress(status);

      if (status.state === 'done') {
        stopPoll();
        ui.showProgressBlock(false);
        showResults(taskId, fmt, status);
      } else if (status.state === 'cancelled' || status.state === 'error') {
        stopPoll();
        ui.showProgressBlock(false);
        ui.setTranscribeButtonState(true);
        if (status.state === 'error') ui.toast('Ошибка транскрибации', 'error');
      }
    } catch {}
  }, 1500);
}

async function showResults(taskId, fmt, statusData) {
  try {
    const fullStatus = await api.taskStatus(taskId);
    ui.renderResults(fullStatus, taskId, fmt, ui.openModal);
    ui.showScreen('stage3');
  } catch (e) {
    ui.toast('Не удалось загрузить результаты: ' + e.message, 'error');
  }
}

// ── Boot ──────────────────────────────────────────────────────────────────────
init();
