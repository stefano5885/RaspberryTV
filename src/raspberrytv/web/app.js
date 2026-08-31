const $ = (selector) => document.querySelector(selector);
let availableTag = "";

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

async function loadStatus() {
  const data = await request("/api/status");
  const config = data.config;
  $("#current-url").textContent = config.url || "Nessun URL configurato";
  $("#url").value = config.url || "";
  $("#ethernet").textContent = connected(data.network.ethernet);
  $("#wifi").textContent = connected(data.network.wifi);
  $("#telegram").textContent = config.telegram_token_configured && config.telegram_chat_id ? "Configurato" : "Da configurare";
  $("#version").textContent = data.version;
  $("#chat-id").value = config.telegram_chat_id || "";
  $("#topic-id").value = config.telegram_topic_id || "";
  $("#repository-url").value = config.repository_url || "";
  const overall = $("#overall-status");
  overall.textContent = data.network.online ? "Rete connessa" : "Rete non disponibile";
  overall.className = data.network.online ? "status-pill online" : "status-pill";
  const update = data.update || {};
  if (update.status && update.status !== "idle") {
    $("#update-summary").textContent = `Ultima operazione: ${update.status}${update.message ? ` · ${update.message}` : ""}`;
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
      await request("/api/update/apply", { method: "POST", body: JSON.stringify({ tag: availableTag }) });
      toast("Aggiornamento avviato; la UI potrebbe riavviarsi");
    }
    if (action === "rollback") {
      if (!confirm("Ripristinare la release precedente?")) return;
      await request("/api/update/rollback", { method: "POST", body: "{}" });
      toast("Rollback avviato");
    }
    if (action === "reboot") {
      if (!confirm("Riavviare il Raspberry Pi?")) return;
      await request("/api/system/reboot", { method: "POST", body: "{}" });
      toast("Riavvio richiesto");
    }
  } catch (error) { toast(error.message, true); }
});

loadStatus().catch((error) => toast(error.message, true));
setInterval(() => loadStatus().catch(() => {}), 30000);
