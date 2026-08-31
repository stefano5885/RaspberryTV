const $ = (selector) => document.querySelector(selector);
let availableTag = "";
let updateMonitor = 0;

function toast(message, error = false) {
  const node = $("#toast");
  node.textContent = message;
  node.className = error ? "visible error" : "visible";
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { node.className = ""; }, 4500);
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Errore HTTP ${response.status}`);
  return payload;
}

function connected(items) {
  const item = (items || []).find((entry) => entry.connected);
  return item ? `${item.connection || item.name}${item.address ? ` · ${item.address}` : ""}` : "Non connessa";
}

function bytes(value) {
  if (!Number.isFinite(value)) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let amount = value;
  let unit = 0;
  while (amount >= 1024 && unit < units.length - 1) { amount /= 1024; unit += 1; }
  return `${amount.toFixed(unit > 1 ? 1 : 0)} ${units[unit]}`;
}

function telemetry(id, online) {
  document.querySelector(id)?.closest(".telemetry-card")?.classList.toggle("offline", !online);
}

function showUpdate(message) {
  const overlay = $("#update-overlay");
  overlay.classList.add("visible");
  overlay.setAttribute("aria-hidden", "false");
  $("#update-overlay-message").textContent = message;
}

async function monitorUpdate() {
  clearTimeout(updateMonitor);
  updateMonitor = 0;
  try {
    const data = await request("/api/status");
    const update = data.update || {};
    showUpdate(update.message || "Aggiornamento in corso…");
    if (["failed", "no_change"].includes(update.status)) {
      setTimeout(() => {
        $("#update-overlay").classList.remove("visible");
        $("#update-overlay").setAttribute("aria-hidden", "true");
        loadStatus().catch(() => {});
      }, 5000);
      return;
    }
  } catch (_) {
    showUpdate("Riavvio dei servizi o del Raspberry in corso…");
  }
  updateMonitor = setTimeout(monitorUpdate, 1000);
}

async function loadStatus() {
  const data = await request("/api/status");
  const config = data.config;
  $("#current-url").textContent = config.url || "Nessun URL configurato";
  $("#url").value = config.url || "";
  $("#ethernet").textContent = connected(data.network.ethernet);
  $("#wifi").textContent = connected(data.network.wifi);
  telemetry("#ethernet", data.network.ethernet?.some((item) => item.connected));
  telemetry("#wifi", data.network.wifi?.some((item) => item.connected));
  $("#telegram").textContent = config.telegram_token_configured && config.telegram_chat_id ? "Configurato" : "Da configurare";
  telemetry("#telegram", config.telegram_token_configured && config.telegram_chat_id);
  $("#version").textContent = data.version;
  const system = data.system || {};
  const cpu = system.cpu_percent == null ? Number.NaN : Number(system.cpu_percent);
  const ram = system.ram || {};
  $("#cpu").textContent = Number.isFinite(cpu) ? `${cpu.toFixed(1)}%` : "—";
  $("#cpu-gauge").style.width = `${Number.isFinite(cpu) ? Math.min(100, Math.max(0, cpu)) : 0}%`;
  $("#cpu-detail").textContent = `LOAD ${system.load_1m ?? "—"} · TEMP ${system.cpu_temperature_c != null ? `${system.cpu_temperature_c}°C` : "—"}`;
  $("#ram").textContent = Number.isFinite(ram.percent) ? `${ram.percent.toFixed(1)}%` : "—";
  $("#ram-gauge").style.width = `${Number.isFinite(ram.percent) ? Math.min(100, Math.max(0, ram.percent)) : 0}%`;
  $("#ram-detail").textContent = `${bytes(ram.used_bytes)} / ${bytes(ram.total_bytes)}`;
  $("#chat-id").value = config.telegram_chat_id || "";
  $("#topic-id").value = config.telegram_topic_id || "";
  $("#repository-url").value = config.repository_url || "";
  const overall = $("#overall-status");
  overall.innerHTML = data.network.online ? "<span></span>NODE ONLINE" : "<span></span>RETE OFFLINE";
  overall.className = data.network.online ? "node-state online" : "node-state";
  const update = data.update || {};
  if (update.status && update.status !== "idle") {
    $("#update-summary").textContent = `Ultima operazione: ${update.status}${update.message ? ` · ${update.message}` : ""}`;
  }
  if (["queued", "preparing", "activating", "verifying", "rolling_back", "rebooting"].includes(update.status)) {
    showUpdate(update.message || "Aggiornamento in corso…");
    if (!updateMonitor) monitorUpdate();
  }
  const rollback = $("[data-action='rollback']");
  rollback.disabled = !data.release?.previous;
  rollback.title = data.release?.previous ? `Ripristina ${data.release.previous}` : "Nessuna release precedente";
}

async function submitForm(form, path) {
  const data = Object.fromEntries(new FormData(form).entries());
  await request(path, { method: "POST", body: JSON.stringify(data) });
  toast("Configurazione salvata");
  await loadStatus();
}

$("#url-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try { await submitForm(event.currentTarget, "/api/config/url"); } catch (error) { toast(error.message, true); }
});
$("#wifi-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try { await submitForm(event.currentTarget, "/api/config/wifi"); event.currentTarget.password.value = ""; } catch (error) { toast(error.message, true); }
});
$("#telegram-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try { await submitForm(event.currentTarget, "/api/config/telegram"); event.currentTarget.token.value = ""; } catch (error) { toast(error.message, true); }
});
$("#repository-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try { await submitForm(event.currentTarget, "/api/config/repository"); } catch (error) { toast(error.message, true); }
});

document.addEventListener("click", async (event) => {
  const action = event.target.closest("[data-action]")?.dataset.action;
  if (!action) return;
  try {
    if (action === "refresh") await loadStatus();
    if (action === "open-site") await request("/api/browser/site", { method: "POST", body: "{}" });
    if (action === "telegram-refresh") {
      const result = await request("/api/telegram/refresh", { method: "POST", body: "{}" });
      toast(result.message || (result.changed ? "URL aggiornato" : "URL già aggiornato"));
      await loadStatus();
    }
    if (action === "update-check") {
      const result = await request("/api/update/check");
      availableTag = result.available || "";
      $("#update-summary").textContent = availableTag ? `Installata ${result.installed} · disponibile ${availableTag}` : "Nessuna release stabile trovata";
      $("[data-action='update-apply']").disabled = !result.update_available;
    }
    if (action === "update-apply") {
      if (!availableTag || !confirm(`Installare ${availableTag}?`)) return;
      showUpdate(`Avvio installazione ${availableTag}…`);
      await request("/api/update/apply", { method: "POST", body: JSON.stringify({ tag: availableTag }) });
      monitorUpdate();
    }
    if (action === "rollback") {
      if (!confirm("Ripristinare la release precedente?")) return;
      showUpdate("Avvio ripristino della release precedente…");
      await request("/api/update/rollback", { method: "POST", body: "{}" });
      monitorUpdate();
    }
    if (action === "reboot") {
      if (!confirm("Riavviare il Raspberry Pi?")) return;
      await request("/api/system/reboot", { method: "POST", body: "{}" });
      toast("Riavvio richiesto");
    }
  } catch (error) {
    if (["update-apply", "rollback"].includes(action)) {
      $("#update-overlay").classList.remove("visible");
      $("#update-overlay").setAttribute("aria-hidden", "true");
    }
    toast(error.message, true);
  }
});

loadStatus().catch((error) => toast(error.message, true));
setInterval(() => loadStatus().catch(() => {}), 10000);
