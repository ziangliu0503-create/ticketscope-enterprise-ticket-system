const API_BASE = import.meta.env.VITE_API_BASE || "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(payload.details) ? `：${payload.details.join("、")}` : "";
    throw new Error(`${payload.error || "请求失败"}${detail}`);
  }
  return payload;
}

export const api = {
  getMeta: () => request("/api/meta"),
  getDashboard: () => request("/api/dashboard"),
  getTickets: (params = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value !== "" && value != null));
    return request(`/api/tickets?${query}`);
  },
  getTicket: (id) => request(`/api/tickets/${id}`),
  createTicket: (payload) => request("/api/tickets", { method: "POST", body: JSON.stringify(payload) }),
  updateTicket: (id, payload) => request(`/api/tickets/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  transitionTicket: (id, payload) => request(`/api/tickets/${id}/transition`, { method: "POST", body: JSON.stringify(payload) }),
};

