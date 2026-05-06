import { api } from './api.js';
import * as ui from './ui.js';

// ── State ─────────────────────────────────────────────────────────────────────
let selectedFiles = [];
let currentTaskId = null;
let pollInterval = null;
let _hubPollers = {};

// ── Nav ───────────────────────────────────────────────────────────────────────
function setNavTab(which) {
  document.getElementById('nav-hub').classList.toggle('active', which === 'hub');
  document.getElementById('nav-main').classList.toggle('active', which === 'main');
}

function setMainTabEnabled(enabled) {
  document.getElementById('nav-main').disabled = !enabled;
}

document.getElementById('nav-hub').addEventListener('click', () => {
  refreshHub().then(() => { ui.showScreen('stage1'); setNavTab('hub'); });
});

document.getElementById('nav-main').addEventListener('click', () => {
  if (!document.getElementById('nav-main').disabled) {
    ui.showScreen('stage2'); setNavTab('main');
  }
});

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  setupStage2();
  await refreshHub(true);
}

// ── Hub ───────────────────────────────────────────────────────────────────────
async function refreshHub(navigate = false) {
  try {
    const info = await api.systemInfo();
    ui.renderHub(info.components, {
      onInstall: handleInstall,
      onUninstall: handleUninstall,
      onSetActive: handleSetActive,
    });
    ui.applySystemInfo(info);

    const anyModel = info.components.some(c => c.type === 'model' && c.installed);
    setMainTabEnabled(anyModel);

    if (navigate) {
      if (anyModel) {
        ui.showScreen('stage2'); setNavTab('main');
      } else {
        ui.showScreen('stage1'); setNavTab('hub');
      }
    }

    for (const comp of info.components) {
      if (comp.installing && !_hubPollers[comp.id]) {
        startHubPoll(comp.id);
      }
    }
  } catch {
    ui.showScreen('stage1'); setNavTab('hub');
  }
}

async function handleInstall(id) {
  try {
    if (id === 'punctuation') {
      await api.installPunct();
    } else {
      await api.installModel(id);
    }
    await refreshHub();
    startHubPoll(id);
  } catch (e) {
    ui.toast('Ошибка установки: ' + e.message, 'error');
  }
}

async function handleUninstall(id) {
  try {
    stopHubPoll(id);
    if (id === 'punctuation') {
      await api.uninstallPunct();
    } else {
      await api.uninstallModel(id);
    }
    await refreshHub();
  } catch (e) {
    ui.toast('Ошибка удаления: ' + e.message, 'error');
  }
}

async function handleSetActive(variant) {
  try {
    await api.setActiveModel(variant);
    await refreshHub();
  } catch (e) {
    ui.toast('Ошибка: ' + e.message, 'error');
  }
}

function startHubPoll(id) {
  if (_hubPollers[id]) return;
  _hubPollers[id] = setInterval(async () => {
    try {
      const info = await api.systemInfo();
      ui.renderHub(info.components, {
        onInstall: handleInstall,
        onUninstall: handleUninstall,
        onSetActive: handleSetActive,
      });
      const anyModel = info.components.some(c => c.type === 'model' && c.installed);
      setMainTabEnabled(anyModel);

      const comp = info.components.find(c => c.id === id);
      if (!comp || !comp.installing) {
        stopHubPoll(id);
        ui.applySystemInfo(info);
      }
    } catch {}
  }, 2000);
}

function stopHubPoll(id) {
  if (_hubPollers[id]) {
    clearInterval(_hubPollers[id]);
    delete _hubPollers[id];
  }
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

  document.querySelectorAll('.seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  const slider = document.getElementById('chunk-slider');
  const sliderVal = document.getElementById('chunk-value');
  slider.addEventListener('input', () => { sliderVal.textContent = slider.value + ' с'; });

  document.getElementById('transcribe-btn').addEventListener('click', startTranscription);

  document.getElementById('cancel-btn').addEventListener('click', async () => {
    if (currentTaskId) {
      try { await api.cancelTask(currentTaskId); } catch {}
      stopPoll();
      ui.showProgressBlock(false);
      ui.setTranscribeButtonState(selectedFiles.length > 0);
      ui.toast('Задача отменена');
    }
  });

  document.getElementById('more-btn').addEventListener('click', () => {
    selectedFiles = [];
    currentTaskId = null;
    ui.renderFileList([], () => {});
    ui.setTranscribeButtonState(false);
    ui.showProgressBlock(false);
    ui.showScreen('stage2');
    setNavTab('main');
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
        showResults(taskId, fmt);
      } else if (status.state === 'cancelled' || status.state === 'error') {
        stopPoll();
        ui.showProgressBlock(false);
        ui.setTranscribeButtonState(true);
        if (status.state === 'error') ui.toast('Ошибка транскрибации', 'error');
      }
    } catch {}
  }, 1500);
}

async function showResults(taskId, fmt) {
  try {
    const fullStatus = await api.taskStatus(taskId);
    ui.renderResults(fullStatus, taskId, fmt, ui.openModal);
    ui.showScreen('stage3');
    setNavTab('main');
  } catch (e) {
    ui.toast('Не удалось загрузить результаты: ' + e.message, 'error');
  }
}

// ── Boot ──────────────────────────────────────────────────────────────────────
init();
