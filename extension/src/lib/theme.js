const themeManager = {
  async init() {
    const theme = await this.get();
    this.apply(theme);
  },

  async get() {
    return new Promise((resolve) => {
      chrome.storage.local.get("wardrop-theme", (result) => {
        resolve(result["wardrop-theme"] || "light");
      });
    });
  },

  apply(theme) {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  },

  async toggle() {
    const current = await this.get();
    const next = current === "dark" ? "light" : "dark";
    await chrome.storage.local.set({ "wardrop-theme": next });
    this.apply(next);
    return next;
  },
};
