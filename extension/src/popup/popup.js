let currentAuthMode = "login";

function getChartColors() {
  const isDark = document.documentElement.classList.contains("dark");
  return {
    grid: isDark ? "#1e293b" : "#e2e8f0",
    tick: isDark ? "#64748b" : "#94a3b8",
    legend: isDark ? "#94a3b8" : "#64748b",
    line: isDark ? "#818cf8" : "#6366f1",
    fill: isDark ? "rgba(129, 140, 248, 0.1)" : "rgba(99, 102, 241, 0.1)",
  };
}

function updateThemeIcon() {
  const isDark = document.documentElement.classList.contains("dark");
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = isDark ? "\u2600\uFE0F" : "\uD83C\uDF19";
}

document.addEventListener("DOMContentLoaded", async () => {
  // Init theme
  await themeManager.init();
  updateThemeIcon();

  document.getElementById("theme-toggle").addEventListener("click", async () => {
    await themeManager.toggle();
    updateThemeIcon();
  });

  await updateAuthUI();
  await loadTrackedProducts();

  document.getElementById("open-dashboard").addEventListener("click", () => {
    chrome.tabs.create({
      url: chrome.runtime.getURL("src/dashboard/dashboard.html"),
    });
  });

  document.getElementById("login-btn").addEventListener("click", () => {
    toggleAuthSection(true);
  });

  document.getElementById("logout-btn").addEventListener("click", async () => {
    await auth.logout();
    await updateAuthUI();
  });

  document.getElementById("auth-submit").addEventListener("click", handleAuthSubmit);

  // Auth tabs
  document.querySelectorAll(".auth-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".auth-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      currentAuthMode = tab.dataset.tab;
      const submitBtn = document.getElementById("auth-submit");
      submitBtn.textContent = currentAuthMode === "login" ? "Entrar" : "Criar conta";
      hideAuthError();
    });
  });

  // Enter key submits auth form
  document.getElementById("auth-password").addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleAuthSubmit();
  });
});

async function updateAuthUI() {
  let loggedIn = await auth.isLoggedIn();
  const loginBtn = document.getElementById("login-btn");
  const authSection = document.getElementById("auth-section");
  const userSection = document.getElementById("user-section");

  if (loggedIn) {
    try {
      const user = await api.getMe();
      loginBtn.style.display = "none";
      authSection.style.display = "none";
      userSection.style.display = "block";
      document.getElementById("user-email").textContent = user.email || "Conectado";
    } catch {
      // Token expired or invalid — clear it and show login
      await auth.logout();
      loggedIn = false;
    }
  }

  if (!loggedIn) {
    loginBtn.style.display = "block";
    userSection.style.display = "none";
  }
}

function toggleAuthSection(show) {
  const authSection = document.getElementById("auth-section");
  authSection.style.display = show ? "block" : "none";
  if (show) {
    document.getElementById("auth-email").focus();
  }
}

async function handleAuthSubmit() {
  const email = document.getElementById("auth-email").value.trim();
  const password = document.getElementById("auth-password").value;

  if (!email || !password) {
    showAuthError("Preencha email e senha.");
    return;
  }

  const submitBtn = document.getElementById("auth-submit");
  submitBtn.disabled = true;
  submitBtn.textContent = "Aguarde...";
  hideAuthError();

  try {
    if (currentAuthMode === "login") {
      await auth.login(email, password);
    } else {
      await auth.register(email, password);
    }

    // Login successful — sync local products to cloud
    await syncLocalToCloud();
    await updateAuthUI();
    await loadTrackedProducts();

    // Clear form
    document.getElementById("auth-email").value = "";
    document.getElementById("auth-password").value = "";
    toggleAuthSection(false);
  } catch (err) {
    showAuthError(err.message || "Erro ao autenticar.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = currentAuthMode === "login" ? "Entrar" : "Criar conta";
  }
}

async function syncLocalToCloud() {
  const syncStatus = document.getElementById("sync-status");
  syncStatus.style.display = "block";

  try {
    const localProducts = await storage.getTrackedProducts();
    if (localProducts.length === 0) {
      syncStatus.style.display = "none";
      return;
    }

    let synced = 0;
    for (const product of localProducts) {
      try {
        if (product.id) {
          await api.trackProduct(product.id);
          synced++;
        }
      } catch (err) {
        // Product might already be tracked or not exist on server — skip
        console.warn("[Wardrop] Sync skip:", product.url, err.message);
      }
    }

    syncStatus.textContent = `${synced} produto(s) sincronizado(s)!`;
    setTimeout(() => {
      syncStatus.style.display = "none";
    }, 2000);
  } catch (err) {
    console.error("[Wardrop] Sync error:", err);
    syncStatus.textContent = "Erro ao sincronizar.";
    setTimeout(() => {
      syncStatus.style.display = "none";
    }, 2000);
  }
}

function showAuthError(msg) {
  const el = document.getElementById("auth-error");
  el.textContent = msg;
  el.style.display = "block";
}

function hideAuthError() {
  document.getElementById("auth-error").style.display = "none";
}

async function loadTrackedProducts() {
  let trackedProducts = [];

  const { token } = await chrome.storage.local.get("token");
  if (token) {
    try {
      trackedProducts = await api.getTrackedProducts();
    } catch (err) {
      console.warn("[Wardrop] API fetch failed, falling back to local:", err);
    }
  }

  if (trackedProducts.length === 0) {
    const local = await chrome.storage.local.get("trackedProducts");
    trackedProducts = local.trackedProducts || [];
  }

  const countEl = document.getElementById("tracked-count");
  const listEl = document.getElementById("tracked-products");

  if (trackedProducts.length === 0) {
    countEl.textContent = "0";
    listEl.innerHTML = '<p class="empty-state">Nenhum produto acompanhado ainda.</p>';
    return;
  }

  // Group by group_id
  const groupIds = new Set();
  const standalone = [];
  for (const p of trackedProducts) {
    if (p.group_id) {
      groupIds.add(p.group_id);
    } else {
      standalone.push(p);
    }
  }

  // Fetch full group data (includes untracked siblings) + auto-track them
  const trackedIds = new Set(trackedProducts.map((p) => p.id));
  const groupDataMap = {};
  await Promise.all(
    [...groupIds].map(async (gid) => {
      try {
        const data = await api.getGroupComparison(gid);
        groupDataMap[gid] = data.group.products;
        // Auto-track untracked siblings
        if (token) {
          for (const sib of data.group.products) {
            if (!trackedIds.has(sib.id)) {
              try { await api.trackProduct(sib.id); } catch {}
            }
          }
        }
      } catch {
        groupDataMap[gid] = trackedProducts.filter((p) => p.group_id === gid);
      }
    })
  );

  const displayItems = [];
  let cardIndex = 0;

  for (const [, products] of Object.entries(groupDataMap)) {
    const sorted = [...products].sort(
      (a, b) => parseFloat(a.current_price || Infinity) - parseFloat(b.current_price || Infinity)
    );
    const cheapest = sorted[0];
    const prices = products.map((p) => parseFloat(p.current_price || 0)).filter((v) => v > 0);
    const minPrice = prices.length ? Math.min(...prices) : 0;
    const maxPrice = prices.length ? Math.max(...prices) : 0;

    displayItems.push({
      type: "group",
      id: cheapest.id,
      group_id: cheapest.group_id,
      name: cheapest.name,
      image_url: cheapest.image_url,
      currency: cheapest.currency || "BRL",
      min_price: minPrice,
      max_price: maxPrice,
      marketplaces: products.map((p) => p.marketplace || "—"),
    });
  }

  for (const p of standalone) {
    displayItems.push({ type: "single", ...p });
  }

  countEl.textContent = displayItems.length;

  listEl.innerHTML = displayItems
    .map((item) => {
      const idx = cardIndex++;
      const pid = escapeHtml(item.id || "");
      const gid = escapeHtml(item.group_id || "");
      const chartDiv = `<div class="product-card-chart" id="chart-area-${idx}"><canvas id="popup-chart-${idx}"></canvas></div>`;

      if (item.type === "group") {
        const badges = item.marketplaces
          .map((mp) => `<span class="popup-mp-badge">${escapeHtml(mp)}</span>`)
          .join("");
        const priceText =
          item.min_price !== item.max_price
            ? `${item.currency} ${item.min_price.toFixed(2)} — ${item.max_price.toFixed(2)}`
            : `${item.currency} ${item.min_price.toFixed(2)}`;
        return `
          <div class="product-card" data-product-id="${pid}" data-group-id="${gid}" data-idx="${idx}">
            <div class="product-card-row">
              ${item.image_url ? `<img class="product-thumb" src="${escapeHtml(item.image_url)}" alt="">` : ""}
              <div class="product-card-info">
                <div class="popup-mp-badges">${badges}</div>
                <div class="product-name" title="${escapeHtml(item.name || "")}">${escapeHtml(item.name || "Produto")}</div>
                <div class="product-price">${priceText}</div>
              </div>
            </div>
            ${chartDiv}
          </div>
        `;
      } else {
        return `
          <div class="product-card" data-product-id="${pid}" data-idx="${idx}">
            <div class="product-card-row">
              ${item.image_url ? `<img class="product-thumb" src="${escapeHtml(item.image_url)}" alt="">` : ""}
              <div class="product-card-info">
                <div class="product-marketplace">${escapeHtml(item.marketplace || "—")}</div>
                <div class="product-name" title="${escapeHtml(item.name || "")}">${escapeHtml(item.name || "Produto")}</div>
                <div class="product-price">${escapeHtml(item.currency || "BRL")} ${escapeHtml(String(item.current_price || "—"))}</div>
              </div>
            </div>
            ${chartDiv}
          </div>
        `;
      }
    })
    .join("");

  // Click to expand/collapse with chart
  listEl.querySelectorAll(".product-card").forEach((card) => {
    card.addEventListener("click", () => togglePopupChart(card));
  });
}

let popupCharts = {};

async function togglePopupChart(card) {
  const idx = card.dataset.idx;
  const productId = card.dataset.productId;
  const groupId = card.dataset.groupId;

  // Collapse if already expanded
  if (card.classList.contains("expanded")) {
    card.classList.remove("expanded");
    if (popupCharts[idx]) {
      popupCharts[idx].destroy();
      delete popupCharts[idx];
    }
    return;
  }

  // Collapse any other expanded card
  card.closest(".products-list").querySelectorAll(".product-card.expanded").forEach((other) => {
    other.classList.remove("expanded");
    const otherIdx = other.dataset.idx;
    if (popupCharts[otherIdx]) {
      popupCharts[otherIdx].destroy();
      delete popupCharts[otherIdx];
    }
  });

  card.classList.add("expanded");

  const chartArea = document.getElementById(`chart-area-${idx}`);
  const canvasId = `popup-chart-${idx}`;

  if (!productId) return;

  chartArea.innerHTML = `<p class="chart-loading">Carregando...</p><canvas id="${canvasId}"></canvas>`;

  try {
    if (groupId) {
      // Grouped: fetch comparison data and render multi-line chart
      const data = await api.getGroupComparison(groupId);
      chartArea.innerHTML = `<canvas id="${canvasId}"></canvas>`;
      renderPopupComparisonChart(data.price_histories, canvasId, idx);
    } else {
      // Single: fetch product history
      const data = await api.getProductHistory(productId);
      chartArea.innerHTML = `<canvas id="${canvasId}"></canvas>`;
      renderPopupSingleChart(data.history, canvasId, idx);
    }
  } catch (err) {
    console.error("[Wardrop] Failed to load chart:", err);
    chartArea.innerHTML = `<p class="chart-loading">Erro ao carregar gráfico.</p>`;
  }
}

const POPUP_MARKETPLACE_COLORS = {
  amazon: "#ff9900",
  mercadolivre: "#ffe600",
  magalu: "#0086ff",
  shopee: "#ee4d2d",
  casasbahia: "#0060a8",
  americanas: "#e60014",
  kabum: "#ff6500",
  aliexpress: "#e43225",
};

function renderPopupSingleChart(history, canvasId, idx) {
  const colors = getChartColors();
  const ctx = document.getElementById(canvasId).getContext("2d");
  const labels = history.map((h) =>
    new Date(h.scraped_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })
  );
  const prices = history.map((h) => parseFloat(h.price));

  popupCharts[idx] = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        data: prices,
        borderColor: colors.line,
        backgroundColor: colors.fill,
        fill: true,
        tension: 0.3,
        pointRadius: 2,
        borderWidth: 1.5,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: (ctx) => `R$ ${ctx.parsed.y.toFixed(2)}` },
        },
      },
      scales: {
        y: {
          ticks: { callback: (v) => `R$${v}`, color: colors.tick, font: { size: 9 } },
          grid: { color: colors.grid },
        },
        x: {
          ticks: { color: colors.tick, font: { size: 9 }, maxTicksLimit: 5 },
          grid: { display: false },
        },
      },
    },
  });
}

function renderPopupComparisonChart(priceHistories, canvasId, idx) {
  const colors = getChartColors();
  const ctx = document.getElementById(canvasId).getContext("2d");
  const allDates = new Set();
  for (const history of Object.values(priceHistories)) {
    for (const h of history) {
      allDates.add(new Date(h.scraped_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" }));
    }
  }
  const labels = [...allDates].sort();
  const datasets = [];

  for (const [marketplace, history] of Object.entries(priceHistories)) {
    const color = POPUP_MARKETPLACE_COLORS[marketplace] || "#6366f1";
    const dataMap = {};
    for (const h of history) {
      const label = new Date(h.scraped_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
      dataMap[label] = parseFloat(h.price);
    }
    datasets.push({
      label: marketplace,
      data: labels.map((l) => dataMap[l] ?? null),
      borderColor: color,
      fill: false,
      tension: 0.3,
      pointRadius: 2,
      borderWidth: 1.5,
      spanGaps: true,
    });
  }

  popupCharts[idx] = new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true, labels: { color: colors.legend, font: { size: 9 }, boxWidth: 8 } },
        tooltip: {
          callbacks: { label: (ctx) => `${ctx.dataset.label}: R$ ${ctx.parsed.y.toFixed(2)}` },
        },
      },
      scales: {
        y: {
          ticks: { callback: (v) => `R$${v}`, color: colors.tick, font: { size: 9 } },
          grid: { color: colors.grid },
        },
        x: {
          ticks: { color: colors.tick, font: { size: 9 }, maxTicksLimit: 5 },
          grid: { display: false },
        },
      },
    },
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
