/**
 * Auth management for the extension.
 * Handles login state, token storage, and session management.
 */
const auth = {
  async login(email, password) {
    const data = await api.login(email, password);
    await chrome.storage.local.set({ token: data.access_token });
    return data;
  },

  async register(email, password) {
    const data = await api.register(email, password);
    await chrome.storage.local.set({ token: data.access_token });
    return data;
  },

  async logout() {
    await chrome.storage.local.remove("token");
  },

  async isLoggedIn() {
    const { token } = await chrome.storage.local.get("token");
    return !!token;
  },

  async getToken() {
    const { token } = await chrome.storage.local.get("token");
    return token || null;
  },
};
