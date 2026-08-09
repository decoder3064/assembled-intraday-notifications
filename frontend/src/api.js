const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8020";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.status === 204 ? null : res.json();
}

export const listRules = () => request("/rules");
export const createRule = (rule) => request("/rules", { method: "POST", body: JSON.stringify(rule) });
export const updateRule = (id, patch) => request(`/rules/${id}`, { method: "PATCH", body: JSON.stringify(patch) });
export const deleteRule = (id) => request(`/rules/${id}`, { method: "DELETE" });
export const listNotifications = (resolved = false) => request(`/notifications?resolved=${resolved}`);
export const resolveNotification = (id) => request(`/notifications/${id}`, { method: "PATCH", body: JSON.stringify({ resolved: true }) });
export const unresolveNotification = (id) => request(`/notifications/${id}`, { method: "PATCH", body: JSON.stringify({ resolved: false }) });
export const deleteNotification = (id) => request(`/notifications/${id}`, { method: "DELETE" });
