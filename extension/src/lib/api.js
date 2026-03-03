const API_BASE = "http://localhost:8000/api";

async function apiRequest(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = { "Content-Type": "application/json", ...options.headers };

  // Add auth token if available
  const { token } = await chrome.storage.local.get("token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

const api = {
  parseProduct(html, url) {
    return apiRequest("/products/parse", {
      method: "POST",
      body: JSON.stringify({ html, url }),
    });
  },

  getProduct(productId) {
    return apiRequest(`/products/${productId}`);
  },

  getProductHistory(productId) {
    return apiRequest(`/products/${productId}/history`);
  },

  login(email, password) {
    return apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  register(email, password) {
    return apiRequest("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  getMe() {
    return apiRequest("/auth/me");
  },

  trackProduct(productId, targetPrice = null, notifyOnAnyDrop = true) {
    return apiRequest("/tracking/track", {
      method: "POST",
      body: JSON.stringify({
        product_id: productId,
        target_price: targetPrice,
        notify_on_any_drop: notifyOnAnyDrop,
      }),
    });
  },

  untrackProduct(productId) {
    return apiRequest(`/tracking/untrack/${productId}`, {
      method: "DELETE",
    });
  },

  getTrackedProducts() {
    return apiRequest("/tracking/products");
  },

  getProductGroups() {
    return apiRequest("/products/groups/list");
  },

  getGroupComparison(groupId) {
    return apiRequest(`/products/groups/${groupId}/compare`);
  },
};
