/* Cliente HTTP simples para a API MedGemma (mesma origem por padrão). */

(() => {
  const DEFAULT_TIMEOUT_MS = 120000;

  function buildUrl(path) {
    // Por padrão, usa mesma origem (quando servido em /ui).
    // Se quiser apontar para outra API, defina window.API_BASE_URL.
    const base = (window.API_BASE_URL || "").replace(/\/+$/, "");
    if (!base) return path;
    return `${base}${path.startsWith("/") ? "" : "/"}${path}`;
  }

  async function fetchWithTimeout(url, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const resp = await fetch(url, { ...options, signal: controller.signal });
      return resp;
    } finally {
      clearTimeout(id);
    }
  }

  async function readJsonOrText(resp) {
    const ct = resp.headers.get("content-type") || "";
    if (ct.includes("application/json")) return await resp.json();
    return await resp.text();
  }

  async function getJson(path) {
    const url = buildUrl(path);
    const resp = await fetchWithTimeout(url, { method: "GET" });
    const data = await readJsonOrText(resp);
    if (!resp.ok) {
      const msg = (data && data.detail) ? data.detail : `Erro HTTP ${resp.status}`;
      throw new Error(msg);
    }
    return data;
  }

  async function postJson(path, body) {
    const url = buildUrl(path);
    const resp = await fetchWithTimeout(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await readJsonOrText(resp);
    if (!resp.ok) {
      const msg = (data && data.detail) ? data.detail : `Erro HTTP ${resp.status}`;
      throw new Error(msg);
    }
    return data;
  }

  const ApiClient = {
    sendQuery: (message, context = null, language = "pt-BR") =>
      postJson("/api/v1/health/query", { message, context, language }),
    sendTriage: (message, context = null, language = "pt-BR") =>
      postJson("/api/v1/health/triage", { message, context, language }),
    sendExplain: (message, context = null, language = "pt-BR") =>
      postJson("/api/v1/health/explain", { message, context, language }),

    getStatus: () => getJson("/api/v1/health/status"),
    getMetrics: () => getJson("/api/v1/health/metrics"),
    getLogs: (cursor = null, limit = 50) => {
      const qs = new URLSearchParams();
      if (cursor) qs.set("cursor", cursor);
      qs.set("limit", String(limit));
      return getJson(`/api/v1/health/logs?${qs.toString()}`);
    },
  };

  window.ApiClient = ApiClient;
})();

