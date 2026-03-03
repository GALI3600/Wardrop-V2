/**
 * Abstraction over chrome.storage.local for offline/local-first mode.
 * When the user is not logged in, product tracking is stored locally.
 */
const storage = {
  async getTrackedProducts() {
    const { trackedProducts = [] } = await chrome.storage.local.get(
      "trackedProducts"
    );
    return trackedProducts;
  },

  async trackProduct(product) {
    const products = await this.getTrackedProducts();
    const exists = products.some((p) => p.url === product.url);
    if (!exists) {
      products.push({
        ...product,
        tracked_at: new Date().toISOString(),
      });
      await chrome.storage.local.set({ trackedProducts: products });
    }
    return products;
  },

  async untrackProduct(url) {
    const products = await this.getTrackedProducts();
    const filtered = products.filter((p) => p.url !== url);
    await chrome.storage.local.set({ trackedProducts: filtered });
    return filtered;
  },

  async isTracked(url) {
    const products = await this.getTrackedProducts();
    return products.some((p) => p.url === url);
  },

  async getToken() {
    const { token } = await chrome.storage.local.get("token");
    return token || null;
  },

  async setToken(token) {
    await chrome.storage.local.set({ token });
  },

  async clearToken() {
    await chrome.storage.local.remove("token");
  },

  async isLoggedIn() {
    const token = await this.getToken();
    return !!token;
  },
};
