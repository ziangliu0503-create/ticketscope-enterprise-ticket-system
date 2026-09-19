const API_BASE = import.meta.env.VITE_API_BASE || "";
const TOKEN_KEY = "ticket_token";
let authToken = sessionStorage.getItem(TOKEN_KEY) || "";

// Earlier versions used localStorage, which is shared by every tab. Remove the
// old value so different demo roles can be tested in separate tabs safely.
localStorage.removeItem(TOKEN_KEY);

function queryString(params = {}) {
  return new URLSearchParams(Object.entries(params).filter(([, value]) => value !== "" && value != null));
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(payload.details) ? `：${payload.details.join("、")}` : "";
    throw new Error(`${payload.error || "请求失败"}${detail}`);
  }
  return payload;
}

async function download(path, filename) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || "导出失败");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export const api = {
  hasToken() {
    return Boolean(authToken);
  },
  setToken(token) {
    authToken = token || "";
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  },
  login: (payload) => request("/api/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request("/api/auth/me"),
  getMeta: () => request("/api/meta"),
  getDashboard: () => request("/api/dashboard"),
  getTickets: (params = {}) => request(`/api/tickets?${queryString(params)}`),
  getTicket: (id) => request(`/api/tickets/${id}`),
  createTicket: (payload) => request("/api/tickets", { method: "POST", body: JSON.stringify(payload) }),
  updateTicket: (id, payload) => request(`/api/tickets/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  transitionTicket: (id, payload) => request(`/api/tickets/${id}/transition`, { method: "POST", body: JSON.stringify(payload) }),
  escalateTicket: (id) => request(`/api/tickets/${id}/escalate`, { method: "POST" }),
  exportTickets: (format, params = {}) => download(`/api/reports/tickets.${format}?${queryString(params)}`, `工单报表.${format}`),
};
