/**
 * SaveYourStorage - Frontend Logic
 * Modern WinUI 3 interactive controller
 */

// App State
const state = {
  selectedPath: "",
  isFolder: false,
  items: [],
  outputDir: "",
  options: {
    format: "original",
    speed: 1.0,
    audio_mode: "keep_speed",
    quality_preset: "balanced",
    custom_crf: 26,
    codec: "auto",
    scale_mode: "original",
    aspect_mode: "original",
    aspect_fit: "crop_fill",
    crop_offset: 50,
    custom_crop_w: 100,
    custom_crop_h: 100,
    custom_crop_x: 0,
    custom_crop_y: 0,
    trim_enabled: false,
    trim_start: 0.0,
    trim_end: 0.0,
    normal_speed_ranges: []
  },
  isProcessing: false,
  pollTimer: null
};

// DOM Elements
const elements = {
  // Selection
  dropZone: document.getElementById("dropZone"),
  btnPickFile: document.getElementById("btnPickFile"),
  btnPickFolder: document.getElementById("btnPickFolder"),
  loadedBanner: document.getElementById("loadedBanner"),
  targetTypeIcon: document.getElementById("targetTypeIcon"),
  targetName: document.getElementById("targetName"),
  targetMeta: document.getElementById("targetMeta"),
  btnClearSelection: document.getElementById("btnClearSelection"),

  // Video Trimmer
  videoTrimmerSection: document.getElementById("videoTrimmerSection"),
  previewPlayer: document.getElementById("previewPlayer"),
  playerCurrentTime: document.getElementById("playerCurrentTime"),
  playerTotalDuration: document.getElementById("playerTotalDuration"),
  playerResolution: document.getElementById("playerResolution"),
  trimStartTime: document.getElementById("trimStartTime"),
  trimEndTime: document.getElementById("trimEndTime"),
  btnSetCurrentAsStart: document.getElementById("btnSetCurrentAsStart"),
  btnSetCurrentAsEnd: document.getElementById("btnSetCurrentAsEnd"),
  btnResetTrim: document.getElementById("btnResetTrim"),
  trimEffectiveDuration: document.getElementById("trimEffectiveDuration"),
  normalRangeStart: document.getElementById("normalRangeStart"),
  normalRangeEnd: document.getElementById("normalRangeEnd"),
  btnUseCurrentNormalStart: document.getElementById("btnUseCurrentNormalStart"),
  btnUseCurrentNormalEnd: document.getElementById("btnUseCurrentNormalEnd"),
  btnAddNormalRange: document.getElementById("btnAddNormalRange"),
  normalSpeedList: document.getElementById("normalSpeedList"),
  sliderTrimStart: document.getElementById("sliderTrimStart"),
  sliderTrimEnd: document.getElementById("sliderTrimEnd"),

  // Queue
  queueSection: document.getElementById("queueSection"),
  queueItemCount: document.getElementById("queueItemCount"),
  queueTotalSize: document.getElementById("queueTotalSize"),
  queueTableBody: document.getElementById("queueTableBody"),

  // Settings
  outputFolderPath: document.getElementById("outputFolderPath"),
  btnBrowseOutput: document.getElementById("btnBrowseOutput"),
  formatSelect: document.getElementById("formatSelect"),
  speedPills: document.getElementById("speedPills"),
  audioRadios: document.querySelectorAll("input[name='audioMode']"),
  qualityPreset: document.getElementById("qualityPreset"),
  customCrfGroup: document.getElementById("customCrfGroup"),
  customCrfInput: document.getElementById("customCrfInput"),
  crfValueDisplay: document.getElementById("crfValueDisplay"),
  scaleSelect: document.getElementById("scaleSelect"),

  // Aspect Ratio & Crop
  aspectCard: document.getElementById("aspectCard"),
  aspectSelect: document.getElementById("aspectSelect"),
  aspectFitGroup: document.getElementById("aspectFitGroup"),
  aspectFitRadios: document.querySelectorAll("input[name='aspectFit']"),
  cropOffsetGroup: document.getElementById("cropOffsetGroup"),
  cropOffsetSlider: document.getElementById("cropOffsetSlider"),
  cropOffsetDisplay: document.getElementById("cropOffsetDisplay"),
  btnCropStart: document.getElementById("btnCropStart"),
  btnCropCenter: document.getElementById("btnCropCenter"),
  btnCropEnd: document.getElementById("btnCropEnd"),
  customCropGroup: document.getElementById("customCropGroup"),
  customCropW: document.getElementById("customCropW"),
  customCropH: document.getElementById("customCropH"),
  customCropX: document.getElementById("customCropX"),
  customCropY: document.getElementById("customCropY"),

  // Progress & Stats
  progressCard: document.getElementById("progressCard"),
  progressSpinner: document.getElementById("progressSpinner"),
  progressStatusText: document.getElementById("progressStatusText"),
  progressPercent: document.getElementById("progressPercent"),
  progressBarFill: document.getElementById("progressBarFill"),
  statProcessedCount: document.getElementById("statProcessedCount"),
  statSavedBytes: document.getElementById("statSavedBytes"),
  statSavedPct: document.getElementById("statSavedPct"),

  // Bottom Floating Bar
  actionSummaryText: document.getElementById("actionSummaryText"),
  btnCancelProcess: document.getElementById("btnCancelProcess"),
  btnOpenOutput: document.getElementById("btnOpenOutput"),
  btnStartProcess: document.getElementById("btnStartProcess")
};

// Formatting utilities
function formatSeconds(secs) {
  if (isNaN(secs) || secs < 0) return "00:00:00";
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = Math.floor(secs % 60);
  const ms = Math.floor((secs % 1) * 10);
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function parseSeconds(timeStr) {
  if (!timeStr) return 0;
  const parts = timeStr.trim().split(":");
  if (parts.length === 3) {
    return parseFloat(parts[0]) * 3600 + parseFloat(parts[1]) * 60 + parseFloat(parts[2]);
  } else if (parts.length === 2) {
    return parseFloat(parts[0]) * 60 + parseFloat(parts[1]);
  }
  return parseFloat(timeStr) || 0;
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + " GB";
}

// Native Pickers
elements.btnPickFile.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/browse-file", { method: "POST" });
    const data = await res.json();
    if (data.selected && data.data) {
      handleScannedData(data.data);
    }
  } catch (err) {
    console.error("File pick error:", err);
  }
});

elements.btnPickFolder.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/browse-folder", { method: "POST" });
    const data = await res.json();
    if (data.selected && data.data) {
      handleScannedData(data.data);
    }
  } catch (err) {
    console.error("Folder pick error:", err);
  }
});

elements.btnBrowseOutput.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/browse-output-folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ initial_dir: state.outputDir })
    });
    const data = await res.json();
    if (data.selected && data.path) {
      state.outputDir = data.path;
      elements.outputFolderPath.value = data.path;
    }
  } catch (err) {
    console.error("Browse output error:", err);
  }
});

elements.btnOpenOutput.addEventListener("click", async () => {
  if (!state.outputDir) return;
  try {
    await fetch("/api/open-folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: state.outputDir })
    });
  } catch (err) {
    console.error("Open folder error:", err);
  }
});

elements.btnClearSelection.addEventListener("click", resetSelection);

function resetSelection() {
  state.selectedPath = "";
  state.isFolder = false;
  state.items = [];
  state.options.trim_enabled = false;
  state.options.normal_speed_ranges = [];
  state.options.aspect_mode = "original";
  state.options.aspect_fit = "crop_fill";
  state.options.crop_offset = 50;
  elements.aspectSelect.value = "original";
  if (typeof updateAspectUI === "function") updateAspectUI();

  elements.loadedBanner.style.display = "none";
  elements.videoTrimmerSection.style.display = "none";
  elements.queueSection.style.display = "none";
  elements.progressCard.style.display = "none";
  elements.previewPlayer.pause();
  elements.previewPlayer.src = "";
  elements.btnStartProcess.disabled = true;
  elements.actionSummaryText.textContent = "Seleziona uno o più file per iniziare";
}

function handleScannedData(data) {
  state.selectedPath = data.target_path;
  state.isFolder = data.is_folder;
  state.items = data.items || [];

  if (state.items.length === 0) {
    alert("Nessun file video o immagine supportato trovato nella selezione.");
    resetSelection();
    return;
  }

  // Set default output dir
  const firstPath = state.items[0].path;
  const parentFolder = firstPath.substring(0, Math.max(firstPath.lastIndexOf("/"), firstPath.lastIndexOf("\\")));
  state.outputDir = parentFolder + "\\SaveYourStorage_Output";
  elements.outputFolderPath.value = state.outputDir;

  // Show Loaded Banner
  elements.loadedBanner.style.display = "flex";
  if (!state.isFolder && state.items.length === 1) {
    const item = state.items[0];
    elements.targetName.textContent = item.name;
    elements.targetTypeIcon.textContent = item.type === "video" ? "🎬" : "🖼️";
    elements.targetMeta.textContent = `${item.size_formatted} | ${item.resolution || "Dimensione sconosciuta"} | Formato: ${item.extension.toUpperCase()}`;
  } else {
    elements.targetTypeIcon.textContent = "📂";
    elements.targetName.textContent = state.selectedPath.split(/[\\/]/).pop() || state.selectedPath;
    elements.targetMeta.textContent = `${state.items.length} file multimediali trovati | ${data.total_size_formatted}`;
  }

  // Handle Single Video Trimmer vs Folder Queue
  if (!state.isFolder && state.items.length === 1 && state.items[0].type === "video") {
    setupSingleVideoTrimmer(state.items[0]);
    elements.queueSection.style.display = "none";
  } else {
    elements.videoTrimmerSection.style.display = "none";
    elements.previewPlayer.pause();
    elements.previewPlayer.src = "";
    state.options.trim_enabled = false;
    state.options.normal_speed_ranges = [];
    renderQueueTable();
    elements.queueSection.style.display = "flex";
  }

  // Enable Start Button
  elements.btnStartProcess.disabled = false;
  elements.actionSummaryText.textContent = `Pronto per elaborare ${state.items.length} ${state.items.length === 1 ? 'file' : 'file in batch'}`;
}

// Single Video Trimmer Setup
function setupSingleVideoTrimmer(item) {
  elements.videoTrimmerSection.style.display = "flex";
  state.options.trim_enabled = true;

  const streamUrl = `/media-preview?path=${encodeURIComponent(item.path)}`;
  elements.previewPlayer.src = streamUrl;

  elements.playerResolution.textContent = item.resolution !== "Unknown" ? item.resolution : "";

  elements.previewPlayer.onloadedmetadata = () => {
    const duration = elements.previewPlayer.duration || item.duration || 0;
    state.options.trim_start = 0;
    state.options.trim_end = duration;
    state.options.normal_speed_ranges = [];

    elements.playerTotalDuration.textContent = formatSeconds(duration);
    elements.trimStartTime.value = "00:00:00";
    elements.trimEndTime.value = formatSeconds(duration);
    elements.normalRangeStart.value = "00:00:00";
    elements.normalRangeEnd.value = "00:00:00";
    renderNormalSpeedRanges();

    elements.sliderTrimStart.max = duration;
    elements.sliderTrimStart.value = 0;

    elements.sliderTrimEnd.max = duration;
    elements.sliderTrimEnd.value = duration;

    updateTrimmerDuration();
  };

  elements.previewPlayer.ontimeupdate = () => {
    elements.playerCurrentTime.textContent = formatSeconds(elements.previewPlayer.currentTime);
  };
}

// Trimmer UI sync
function updateTrimmerDuration() {
  const start = state.options.trim_start;
  const end = state.options.trim_end;
  const eff = Math.max(0, end - start);
  const speed = state.options.speed || 1.0;
  const normalDuration = state.options.normal_speed_ranges.reduce((total, range) => {
    const rangeStart = Math.max(start, Number(range.start) || 0);
    const rangeEnd = Math.min(end, Number(range.end) || 0);
    return total + Math.max(0, rangeEnd - rangeStart);
  }, 0);
  const afterSpeed = normalDuration + Math.max(0, eff - normalDuration) / speed;

  elements.trimEffectiveDuration.textContent = `${formatSeconds(eff)} (Finale: ${formatSeconds(afterSpeed)})`;
}

function renderNormalSpeedRanges() {
  elements.normalSpeedList.innerHTML = "";
  state.options.normal_speed_ranges.forEach((range, index) => {
    const row = document.createElement("div");
    row.className = "normal-speed-item";
    row.innerHTML = `<span>Normale: ${formatSeconds(range.start)} → ${formatSeconds(range.end)}</span>
      <button type="button" class="btn btn-sm btn-subtle" data-remove-normal-range="${index}">Rimuovi</button>`;
    elements.normalSpeedList.appendChild(row);
  });
}

elements.btnUseCurrentNormalStart.addEventListener("click", () => {
  elements.normalRangeStart.value = formatSeconds(elements.previewPlayer.currentTime);
});

elements.btnUseCurrentNormalEnd.addEventListener("click", () => {
  elements.normalRangeEnd.value = formatSeconds(elements.previewPlayer.currentTime);
});

elements.btnAddNormalRange.addEventListener("click", () => {
  const start = parseSeconds(elements.normalRangeStart.value);
  const end = parseSeconds(elements.normalRangeEnd.value);
  const duration = elements.previewPlayer.duration || 0;
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start || start < 0 || end > duration) {
    alert("Inserisci un intervallo valido compreso nella durata del video.");
    return;
  }
  state.options.normal_speed_ranges.push({ start, end });
  state.options.normal_speed_ranges = state.options.normal_speed_ranges
    .sort((a, b) => a.start - b.start)
    .reduce((merged, range) => {
      const previous = merged[merged.length - 1];
      if (previous && range.start <= previous.end) {
        previous.end = Math.max(previous.end, range.end);
      } else {
        merged.push({ ...range });
      }
      return merged;
    }, []);
  renderNormalSpeedRanges();
  updateTrimmerDuration();
});

elements.normalSpeedList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-remove-normal-range]");
  if (!button) return;
  state.options.normal_speed_ranges.splice(Number(button.dataset.removeNormalRange), 1);
  renderNormalSpeedRanges();
  updateTrimmerDuration();
});

elements.sliderTrimStart.addEventListener("input", (e) => {
  const val = parseFloat(e.target.value);
  if (val >= state.options.trim_end) {
    state.options.trim_start = Math.max(0, state.options.trim_end - 0.5);
    e.target.value = state.options.trim_start;
  } else {
    state.options.trim_start = val;
  }
  elements.trimStartTime.value = formatSeconds(state.options.trim_start);
  elements.previewPlayer.currentTime = state.options.trim_start;
  updateTrimmerDuration();
});

elements.sliderTrimEnd.addEventListener("input", (e) => {
  const val = parseFloat(e.target.value);
  if (val <= state.options.trim_start) {
    state.options.trim_end = Math.min(elements.previewPlayer.duration, state.options.trim_start + 0.5);
    e.target.value = state.options.trim_end;
  } else {
    state.options.trim_end = val;
  }
  elements.trimEndTime.value = formatSeconds(state.options.trim_end);
  elements.previewPlayer.currentTime = state.options.trim_end;
  updateTrimmerDuration();
});

elements.btnSetCurrentAsStart.addEventListener("click", () => {
  const current = elements.previewPlayer.currentTime;
  if (current < state.options.trim_end) {
    state.options.trim_start = current;
    elements.sliderTrimStart.value = current;
    elements.trimStartTime.value = formatSeconds(current);
    updateTrimmerDuration();
  }
});

elements.btnSetCurrentAsEnd.addEventListener("click", () => {
  const current = elements.previewPlayer.currentTime;
  if (current > state.options.trim_start) {
    state.options.trim_end = current;
    elements.sliderTrimEnd.value = current;
    elements.trimEndTime.value = formatSeconds(current);
    updateTrimmerDuration();
  }
});

elements.btnResetTrim.addEventListener("click", () => {
  const duration = elements.previewPlayer.duration || 0;
  state.options.trim_start = 0;
  state.options.trim_end = duration;
  state.options.normal_speed_ranges = [];
  elements.sliderTrimStart.value = 0;
  elements.sliderTrimEnd.value = duration;
  elements.trimStartTime.value = "00:00:00";
  elements.trimEndTime.value = formatSeconds(duration);
  elements.normalRangeStart.value = "00:00:00";
  elements.normalRangeEnd.value = "00:00:00";
  renderNormalSpeedRanges();
  updateTrimmerDuration();
});

elements.trimStartTime.addEventListener("change", (e) => {
  const sec = parseSeconds(e.target.value);
  state.options.trim_start = Math.max(0, Math.min(sec, state.options.trim_end - 0.5));
  elements.sliderTrimStart.value = state.options.trim_start;
  e.target.value = formatSeconds(state.options.trim_start);
  updateTrimmerDuration();
});

elements.trimEndTime.addEventListener("change", (e) => {
  const sec = parseSeconds(e.target.value);
  state.options.trim_end = Math.min(elements.previewPlayer.duration || 99999, Math.max(sec, state.options.trim_start + 0.5));
  elements.sliderTrimEnd.value = state.options.trim_end;
  e.target.value = formatSeconds(state.options.trim_end);
  updateTrimmerDuration();
});

// Stepping helper
function adjustTrim(type, delta) {
  if (type === 'start') {
    state.options.trim_start = Math.max(0, Math.min(state.options.trim_start + delta, state.options.trim_end - 0.2));
    elements.sliderTrimStart.value = state.options.trim_start;
    elements.trimStartTime.value = formatSeconds(state.options.trim_start);
    elements.previewPlayer.currentTime = state.options.trim_start;
  } else {
    const maxDur = elements.previewPlayer.duration || 99999;
    state.options.trim_end = Math.max(state.options.trim_start + 0.2, Math.min(state.options.trim_end + delta, maxDur));
    elements.sliderTrimEnd.value = state.options.trim_end;
    elements.trimEndTime.value = formatSeconds(state.options.trim_end);
    elements.previewPlayer.currentTime = state.options.trim_end;
  }
  updateTrimmerDuration();
}

const stepBtnMap = {
  "btnStartMinus1s": ["start", -1.0],
  "btnStartMinus01s": ["start", -0.1],
  "btnStartPlus01s": ["start", 0.1],
  "btnStartPlus1s": ["start", 1.0],
  "btnEndMinus1s": ["end", -1.0],
  "btnEndMinus01s": ["end", -0.1],
  "btnEndPlus01s": ["end", 0.1],
  "btnEndPlus1s": ["end", 1.0]
};

Object.entries(stepBtnMap).forEach(([btnId, [target, delta]]) => {
  const btn = document.getElementById(btnId);
  if (btn) {
    btn.addEventListener("click", () => adjustTrim(target, delta));
  }
});

// Keyboard Shortcuts (Space=Play/Pause, I=In-point, O=Out-point, ArrowLeft/Right=Seek)
document.addEventListener("keydown", (e) => {
  if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) return;
  if (!state.options.trim_enabled || elements.videoTrimmerSection.style.display === "none") return;

  if (e.code === "Space") {
    e.preventDefault();
    if (elements.previewPlayer.paused) {
      elements.previewPlayer.play();
    } else {
      elements.previewPlayer.pause();
    }
  } else if (e.code === "KeyI") {
    elements.btnSetCurrentAsStart.click();
  } else if (e.code === "KeyO") {
    elements.btnSetCurrentAsEnd.click();
  } else if (e.code === "ArrowLeft") {
    e.preventDefault();
    elements.previewPlayer.currentTime = Math.max(0, elements.previewPlayer.currentTime - 1);
  } else if (e.code === "ArrowRight") {
    e.preventDefault();
    elements.previewPlayer.currentTime = Math.min(elements.previewPlayer.duration || 99999, elements.previewPlayer.currentTime + 1);
  }
});

// Ko-Fi Handlers
["btnKofiHeader", "btnKofiCard"].forEach(id => {
  const btn = document.getElementById(id);
  if (btn) {
    btn.addEventListener("click", async (e) => {
      // In Edge App Mode or desktop window, notify backend to launch system browser directly
      try {
        await fetch("/api/open-kofi", { method: "POST" });
      } catch (err) {
        // Fallback to standard href navigation
      }
    });
  }
});

// Render Batch Queue
function renderQueueTable() {
  elements.queueItemCount.textContent = state.items.length;
  const totalBytes = state.items.reduce((acc, it) => acc + it.size_bytes, 0);
  elements.queueTotalSize.textContent = formatBytes(totalBytes);

  elements.queueTableBody.innerHTML = "";
  state.items.forEach((item, index) => {
    const tr = document.createElement("tr");
    tr.id = `row-${item.id}`;

    let statusBadge = `<span class="badge badge-outline">In attesa</span>`;
    if (item.status === "processing") {
      statusBadge = `<span class="badge badge-accent">Elaborazione...</span>`;
    } else if (item.status === "done") {
      statusBadge = `<span class="badge badge-success">Completato</span>`;
    } else if (item.status === "error") {
      statusBadge = `<span class="badge" style="color:var(--color-danger)">Errore</span>`;
    }

    let savingsText = "-";
    if (item.status === "done" && item.saved_bytes !== undefined) {
      const isReduction = item.saved_bytes >= 0;
      savingsText = `<strong class="${isReduction ? 'text-success' : 'text-accent'}">${isReduction ? '-' : '+'}${item.saved_percentage}% (${formatBytes(Math.abs(item.saved_bytes))})</strong>`;
    }

    tr.innerHTML = `
      <td><strong>${item.name}</strong></td>
      <td>${item.type === "video" ? "🎬 Video" : "🖼️ Foto"}</td>
      <td>${item.resolution || item.extension}</td>
      <td>${item.size_formatted}</td>
      <td id="status-cell-${item.id}">${statusBadge}</td>
      <td id="savings-cell-${item.id}">${savingsText}</td>
    `;
    elements.queueTableBody.appendChild(tr);
  });
}

// Speed Pills
elements.speedPills.addEventListener("click", (e) => {
  if (e.target.classList.contains("pill-btn")) {
    elements.speedPills.querySelectorAll(".pill-btn").forEach(b => b.classList.remove("active"));
    e.target.classList.add("active");
    state.options.speed = parseFloat(e.target.dataset.speed);
    updateTrimmerDuration();
  }
});

// Audio Radios
elements.audioRadios.forEach(r => {
  r.addEventListener("change", (e) => {
    state.options.audio_mode = e.target.value;
  });
});

// Format Select
elements.formatSelect.addEventListener("change", (e) => {
  state.options.format = e.target.value;
});

// Quality Preset
elements.qualityPreset.addEventListener("change", (e) => {
  state.options.quality_preset = e.target.value;
  if (e.target.value === "custom") {
    elements.customCrfGroup.style.display = "flex";
  } else {
    elements.customCrfGroup.style.display = "none";
  }
});

// Custom CRF
elements.customCrfInput.addEventListener("input", (e) => {
  elements.crfValueDisplay.textContent = e.target.value;
  state.options.custom_crf = parseInt(e.target.value, 10);
});

// Scale / Upscale Select
elements.scaleSelect.addEventListener("change", (e) => {
  state.options.scale_mode = e.target.value;
});

// Aspect Ratio & Orientation
elements.aspectSelect.addEventListener("change", (e) => {
  state.options.aspect_mode = e.target.value;
  updateAspectUI();
});

function updateAspectUI() {
  const mode = state.options.aspect_mode;
  if (mode === "original") {
    elements.aspectFitGroup.style.display = "none";
    elements.cropOffsetGroup.style.display = "none";
    elements.customCropGroup.style.display = "none";
    elements.previewPlayer.style.aspectRatio = "unset";
  } else if (mode === "custom") {
    elements.aspectFitGroup.style.display = "none";
    elements.cropOffsetGroup.style.display = "none";
    elements.customCropGroup.style.display = "grid";
    elements.previewPlayer.style.aspectRatio = "unset";
  } else {
    // 9:16, 16:9, 1:1, 4:5
    elements.aspectFitGroup.style.display = "flex";
    elements.customCropGroup.style.display = "none";
    if (state.options.aspect_fit === "crop_fill") {
      elements.cropOffsetGroup.style.display = "flex";
    } else {
      elements.cropOffsetGroup.style.display = "none";
    }

    // Dynamic player preview aspect ratio guide
    if (mode === "9:16") {
      elements.previewPlayer.style.aspectRatio = "9 / 16";
    } else if (mode === "16:9") {
      elements.previewPlayer.style.aspectRatio = "16 / 9";
    } else if (mode === "1:1") {
      elements.previewPlayer.style.aspectRatio = "1 / 1";
    } else if (mode === "4:5") {
      elements.previewPlayer.style.aspectRatio = "4 / 5";
    }
  }
}

// Aspect Fit Radios
elements.aspectFitRadios.forEach(r => {
  r.addEventListener("change", (e) => {
    state.options.aspect_fit = e.target.value;
    if (state.options.aspect_fit === "crop_fill" && state.options.aspect_mode !== "original" && state.options.aspect_mode !== "custom") {
      elements.cropOffsetGroup.style.display = "flex";
    } else {
      elements.cropOffsetGroup.style.display = "none";
    }
  });
});

// Crop Offset Slider
function setCropOffset(val) {
  state.options.crop_offset = val;
  elements.cropOffsetSlider.value = val;
  let text = `${val}%`;
  if (val === 50) text = "Centro (50%)";
  else if (val < 40) text = `Inizio / Sinistra-Alto (${val}%)`;
  else if (val > 60) text = `Fine / Destra-Basso (${val}%)`;
  elements.cropOffsetDisplay.textContent = text;

  [elements.btnCropStart, elements.btnCropCenter, elements.btnCropEnd].forEach(b => b.classList.remove("active"));
  if (val === 0) elements.btnCropStart.classList.add("active");
  else if (val === 50) elements.btnCropCenter.classList.add("active");
  else if (val === 100) elements.btnCropEnd.classList.add("active");
}

elements.cropOffsetSlider.addEventListener("input", (e) => {
  setCropOffset(parseInt(e.target.value, 10));
});

elements.btnCropStart.addEventListener("click", () => setCropOffset(0));
elements.btnCropCenter.addEventListener("click", () => setCropOffset(50));
elements.btnCropEnd.addEventListener("click", () => setCropOffset(100));

// Custom Crop inputs
elements.customCropW.addEventListener("change", (e) => {
  state.options.custom_crop_w = Math.max(10, Math.min(100, parseFloat(e.target.value) || 100));
  e.target.value = state.options.custom_crop_w;
});

elements.customCropH.addEventListener("change", (e) => {
  state.options.custom_crop_h = Math.max(10, Math.min(100, parseFloat(e.target.value) || 100));
  e.target.value = state.options.custom_crop_h;
});

elements.customCropX.addEventListener("change", (e) => {
  state.options.custom_crop_x = Math.max(0, Math.min(90, parseFloat(e.target.value) || 0));
  e.target.value = state.options.custom_crop_x;
});

elements.customCropY.addEventListener("change", (e) => {
  state.options.custom_crop_y = Math.max(0, Math.min(90, parseFloat(e.target.value) || 0));
  e.target.value = state.options.custom_crop_y;
});

// Drag and drop zone handling
["dragenter", "dragover"].forEach(name => {
  elements.dropZone.addEventListener(name, (e) => {
    e.preventDefault();
    e.stopPropagation();
    elements.dropZone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach(name => {
  elements.dropZone.addEventListener(name, (e) => {
    e.preventDefault();
    e.stopPropagation();
    elements.dropZone.classList.remove("dragover");
  });
});

elements.dropZone.addEventListener("drop", (e) => {
  // Direct file drop notification
  if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    alert("Per garantire l'accesso al percorso completo su Windows, clicca su 'Carica Singolo File' o 'Carica Intera Cartella'.");
  }
});

// Start Processing
elements.btnStartProcess.addEventListener("click", async () => {
  if (state.items.length === 0 || state.isProcessing) return;

  state.isProcessing = true;
  elements.btnStartProcess.disabled = true;
  elements.btnCancelProcess.style.display = "inline-flex";
  elements.btnOpenOutput.style.display = "none";
  elements.progressCard.style.display = "flex";

  const payload = {
    items: state.items,
    output_dir: elements.outputFolderPath.value || state.outputDir,
    options: state.options
  };

  try {
    const res = await fetch("/api/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.status === 200) {
      startPollingProgress();
    } else {
      alert("Errore avvio elaborazione: " + (data.error || "Errore sconosciuto"));
      stopProcessingUI();
    }
  } catch (err) {
    alert("Errore di rete: " + err.message);
    stopProcessingUI();
  }
});

// Cancel Processing
elements.btnCancelProcess.addEventListener("click", async () => {
  try {
    await fetch("/api/cancel", { method: "POST" });
  } catch (err) {
    console.error("Cancel error:", err);
  }
});

function startPollingProgress() {
  if (state.pollTimer) clearInterval(state.pollTimer);

  state.pollTimer = setInterval(async () => {
    try {
      const res = await fetch("/api/status");
      const status = await res.json();

      // Update progress bar & text
      elements.progressPercent.textContent = `${status.overall_progress}%`;
      elements.progressBarFill.style.width = `${status.overall_progress}%`;
      elements.progressStatusText.textContent = status.current_status_text;

      // Stats
      elements.statProcessedCount.textContent = `${status.completed_items} / ${status.total_items}`;
      elements.statSavedBytes.textContent = status.total_saved_formatted;
      elements.statSavedPct.textContent = `${status.total_saved_percentage}%`;

      // Update queue items
      if (status.items && status.items.length > 0) {
        status.items.forEach(it => {
          const statusCell = document.getElementById(`status-cell-${it.id}`);
          const savingsCell = document.getElementById(`savings-cell-${it.id}`);
          if (statusCell && savingsCell) {
            if (it.status === "processing") {
              statusCell.innerHTML = `<span class="badge badge-accent">In corso...</span>`;
            } else if (it.status === "done") {
              statusCell.innerHTML = `<span class="badge badge-success">✓ Completato</span>`;
              const isReduction = it.saved_bytes >= 0;
              savingsCell.innerHTML = `<strong class="${isReduction ? 'text-success' : 'text-accent'}">${isReduction ? '-' : '+'}${it.saved_percentage}% (${formatBytes(Math.abs(it.saved_bytes))})</strong>`;
            } else if (it.status === "error") {
              statusCell.innerHTML = `<span class="badge" style="color:var(--color-danger)">✕ Errore</span>`;
            }
          }
        });
      }

      // Check if finished
      if (!status.is_running) {
        clearInterval(state.pollTimer);
        state.pollTimer = null;
        state.isProcessing = false;
        elements.progressSpinner.style.display = "none";
        elements.btnCancelProcess.style.display = "none";
        elements.btnOpenOutput.style.display = "inline-flex";
        elements.btnStartProcess.disabled = false;
        elements.btnStartProcess.textContent = "✓ Elaborazione Terminata (Riavvia)";
        elements.actionSummaryText.textContent = `Operazione terminata! Spazio totale risparmiato: ${status.total_saved_formatted} (${status.total_saved_percentage}%)`;
      }
    } catch (err) {
      console.error("Poll status error:", err);
    }
  }, 400);
}

function stopProcessingUI() {
  state.isProcessing = false;
  if (state.pollTimer) clearInterval(state.pollTimer);
  elements.btnStartProcess.disabled = false;
  elements.btnCancelProcess.style.display = "none";
  elements.progressSpinner.style.display = "none";
}
