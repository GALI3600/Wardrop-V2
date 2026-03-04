// Syncs JWT token between extension (chrome.storage) and web app (localStorage)

(async () => {
  const WEB_KEY = "wardrop-token";
  const STORAGE_KEY = "token";

  const webToken = localStorage.getItem(WEB_KEY);
  const { [STORAGE_KEY]: extToken } = await chrome.storage.local.get(STORAGE_KEY);

  if (webToken && webToken !== extToken) {
    // Web has a token the extension doesn't — sync to extension
    await chrome.storage.local.set({ [STORAGE_KEY]: webToken });
  } else if (extToken && !webToken) {
    // Extension has a token but web doesn't — sync to web
    localStorage.setItem(WEB_KEY, extToken);
    window.dispatchEvent(new Event("storage"));
  }

  // Watch for web login/logout changes
  window.addEventListener("storage", async (e) => {
    if (e.key !== WEB_KEY) return;
    if (e.newValue) {
      await chrome.storage.local.set({ [STORAGE_KEY]: e.newValue });
    } else {
      await chrome.storage.local.remove(STORAGE_KEY);
    }
  });

  // Watch for extension login/logout changes
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local" || !changes[STORAGE_KEY]) return;
    const newToken = changes[STORAGE_KEY].newValue;
    if (newToken) {
      localStorage.setItem(WEB_KEY, newToken);
    } else {
      localStorage.removeItem(WEB_KEY);
    }
    // Notify same-tab listeners (storage event only fires cross-tab)
    window.dispatchEvent(
      new StorageEvent("storage", { key: WEB_KEY, newValue: newToken || null })
    );
  });
})();
