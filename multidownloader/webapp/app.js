const strings = {
  en: {
    section_urls: "Links",
    section_download: "Download",
    section_settings: "Settings",
    mode_video: "Video",
    mode_audio: "Audio",
    mode_both: "Both",
    label_output: "Save folder",
    label_cookies: "Cookies file (optional)",
    label_theme: "Theme",
    label_dark: "Dark",
    label_light: "Light",
    btn_browse: "Browse",
    btn_start: "Start download",
    btn_start_running: "Downloading...",
    btn_close: "Close",
    log_title: "Activity",
    placeholder_urls: "Paste links here...",
    label_count: "Links: {count}",
    msg_busy: "A download is already running.",
    msg_no_urls: "Please enter at least one URL.",
    msg_done: "All downloads completed successfully.",
    msg_done_errors: "Some downloads failed.",
  },
};

const state = {
  lang: "en",
  running: false,
  theme: "dark",
};

const initialTheme = document.documentElement.getAttribute("data-theme");
if (initialTheme === "light" || initialTheme === "dark") {
  state.theme = initialTheme;
}

let startPending = false;

const els = {
  urlsInput: document.getElementById("urls-input"),
  outputInput: document.getElementById("output-input"),
  cookiesInput: document.getElementById("cookies-input"),
  startBtn: document.getElementById("start-btn"),
  outputBrowse: document.getElementById("output-browse"),
  cookiesBrowse: document.getElementById("cookies-browse"),
  logOutput: document.getElementById("log-output"),
  toast: document.getElementById("toast"),
  countChip: document.getElementById("count-chip"),
  themeToggle: document.getElementById("theme-toggle"),
  settingsToggle: document.getElementById("settings-toggle"),
  settingsDrawer: document.getElementById("settings-drawer"),
  settingsBackdrop: document.getElementById("settings-backdrop"),
  settingsClose: document.getElementById("settings-close"),
};

function t(key) {
  return (strings[state.lang] && strings[state.lang][key]) || "";
}

function applyLang() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    el.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    el.setAttribute("placeholder", t(key));
  });
  updateCount();
  setRunning(state.running);
}

function applyTheme(theme) {
  state.theme = theme;
  document.documentElement.setAttribute("data-theme", theme);
  if (els.themeToggle) {
    els.themeToggle.checked = theme === "light";
  }
  scheduleSaveSettings();
}

function setRunning(running) {
  state.running = running;
  if (els.startBtn) {
    if (running) {
      els.startBtn.disabled = true;
    } else {
      els.startBtn.disabled = getUrlList().length === 0;
    }
    els.startBtn.textContent = running ? t("btn_start_running") : t("btn_start");
  }
}

function appendLog(message) {
  const node = document.createTextNode(`${message}\n`);
  els.logOutput.appendChild(node);
  els.logOutput.scrollTop = els.logOutput.scrollHeight;
}

function clearLog() {
  els.logOutput.textContent = "";
}

function getUrlList() {
  const lines = els.urlsInput.value.split(/\r?\n/);
  const seen = new Set();
  const urls = [];
  lines.forEach((line) => {
    const url = line.trim();
    if (!url || url.startsWith("#")) {
      return;
    }
    if (!seen.has(url)) {
      seen.add(url);
      urls.push(url);
    }
  });
  return urls;
}

function updateCount() {
  if (!els.countChip && !els.startBtn) {
    return;
  }
  const count = getUrlList().length;
  if (els.countChip) {
    els.countChip.textContent = t("label_count").replace("{count}", count);
  }
  if (els.startBtn && !state.running) {
    els.startBtn.disabled = count === 0;
  }
}

let countFrame = 0;
function scheduleCountUpdate() {
  if (countFrame) {
    return;
  }
  countFrame = requestAnimationFrame(() => {
    countFrame = 0;
    updateCount();
  });
}

let toastTimer;
function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    els.toast.classList.remove("show");
  }, 2200);
}

function getSelectedMode() {
  const selected = document.querySelector("input[name='mode']:checked");
  return selected ? selected.value : "video";
}

function collectSettings() {
  return {
    output: els.outputInput ? els.outputInput.value.trim() : "",
    cookies: els.cookiesInput ? els.cookiesInput.value.trim() : "",
    theme: state.theme,
  };
}

let saveTimer;
function scheduleSaveSettings() {
  if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.save_settings) {
    return;
  }
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    const payload = collectSettings();
    window.pywebview.api.save_settings(payload);
  }, 250);
}

async function initDefaults() {
  if (!window.pywebview || !window.pywebview.api) {
    return;
  }
  const defaults = await window.pywebview.api.get_defaults();
  if (defaults.output) {
    els.outputInput.value = defaults.output;
  }
  if (defaults.cookies) {
    els.cookiesInput.value = defaults.cookies;
  }
  if (defaults.theme === "light" || defaults.theme === "dark") {
    applyTheme(defaults.theme);
  } else {
    applyTheme(state.theme);
  }
}

async function startDownload() {
  if (state.running || startPending) {
    showToast(t("msg_busy"));
    return;
  }
  if (!window.pywebview || !window.pywebview.api) {
    showToast("Bridge not ready.");
    return;
  }

  if (getUrlList().length === 0) {
    showToast(t("msg_no_urls"));
    return;
  }

  startPending = true;
  if (els.startBtn) {
    els.startBtn.disabled = true;
  }

  const payload = {
    urls: els.urlsInput.value,
    mode: getSelectedMode(),
    output: els.outputInput.value,
    cookies: els.cookiesInput.value,
  };

  const response = await window.pywebview.api.start_download(payload);
  startPending = false;
  if (!response.ok) {
    updateCount();
    if (response.error === "busy") {
      showToast(t("msg_busy"));
    } else if (response.error === "no_urls") {
      showToast(t("msg_no_urls"));
    } else {
      showToast("Error: " + response.error);
    }
    return;
  }

  setRunning(true);
  clearLog();
  appendLog("Downloading...");
}

async function browseOutput() {
  if (!window.pywebview || !window.pywebview.api) {
    return;
  }
  const result = await window.pywebview.api.select_output_dir();
  if (result) {
    els.outputInput.value = result;
    scheduleSaveSettings();
  }
}

async function browseCookies() {
  if (!window.pywebview || !window.pywebview.api) {
    return;
  }
  const result = await window.pywebview.api.select_cookies_file();
  if (result) {
    els.cookiesInput.value = result;
    scheduleSaveSettings();
  }
}

function handleBackendEvent(event) {
  const detail = event.detail || {};
  if (detail.type === "log") {
    appendLog(detail.message || "");
  }
  if (detail.type === "done") {
    setRunning(false);
    if (detail.ok) {
      showToast(t("msg_done"));
    } else {
      showToast(t("msg_done_errors"));
      if (detail.errors && detail.errors.length) {
        appendLog(detail.errors.join("\n"));
      }
    }
  }
}

function openSettings() {
  if (!els.settingsDrawer) {
    return;
  }
  els.settingsDrawer.classList.add("open");
  els.settingsDrawer.setAttribute("aria-hidden", "false");
  if (els.settingsBackdrop) {
    els.settingsBackdrop.classList.add("show");
    els.settingsBackdrop.setAttribute("aria-hidden", "false");
  }
  if (els.settingsToggle) {
    els.settingsToggle.setAttribute("aria-expanded", "true");
  }
}

function closeSettings() {
  if (!els.settingsDrawer) {
    return;
  }
  els.settingsDrawer.classList.remove("open");
  els.settingsDrawer.setAttribute("aria-hidden", "true");
  if (els.settingsBackdrop) {
    els.settingsBackdrop.classList.remove("show");
    els.settingsBackdrop.setAttribute("aria-hidden", "true");
  }
  if (els.settingsToggle) {
    els.settingsToggle.setAttribute("aria-expanded", "false");
  }
}

if (els.settingsToggle) {
  els.settingsToggle.addEventListener("click", () => {
    if (!els.settingsDrawer) {
      return;
    }
    if (els.settingsDrawer.classList.contains("open")) {
      closeSettings();
    } else {
      openSettings();
    }
  });
}

if (els.settingsClose) {
  els.settingsClose.addEventListener("click", closeSettings);
}

if (els.settingsBackdrop) {
  els.settingsBackdrop.addEventListener("click", closeSettings);
}

document.addEventListener("click", (event) => {
  if (!els.settingsDrawer || !els.settingsToggle) {
    return;
  }
  if (!els.settingsDrawer.classList.contains("open")) {
    return;
  }
  const target = event.target;
  if (target instanceof Node) {
    if (els.settingsDrawer.contains(target) || els.settingsToggle.contains(target)) {
      return;
    }
  }
  closeSettings();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeSettings();
  }
});

if (els.themeToggle) {
  els.themeToggle.checked = state.theme === "light";
  els.themeToggle.addEventListener("change", () => {
    applyTheme(els.themeToggle.checked ? "light" : "dark");
  });
}

els.startBtn.addEventListener("click", startDownload);
els.outputBrowse.addEventListener("click", browseOutput);
els.cookiesBrowse.addEventListener("click", browseCookies);
els.urlsInput.addEventListener("input", scheduleCountUpdate);
els.outputInput.addEventListener("input", scheduleSaveSettings);
els.cookiesInput.addEventListener("input", scheduleSaveSettings);

window.addEventListener("md-event", handleBackendEvent);
window.addEventListener("pywebviewready", initDefaults);

applyLang();
setRunning(false);
