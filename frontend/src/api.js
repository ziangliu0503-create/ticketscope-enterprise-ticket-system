const API_BASE = import.meta.env.VITE_API_BASE || "";
let authToken = localStorage.getItem("ticket_token") || "";

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
  setToken(token) {
    authToken = token || "";
    if (token) localStorage.setItem("ticket_token", token);
    else localStorage.removeItem("ticket_token");
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
