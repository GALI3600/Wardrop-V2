// API_BASE is defined in ../lib/api.js (loaded before this script)
let currentChart = null;

const MARKETPLACE_COLORS = {
  amazon: "#ff9900",
  mercadolivre: "#ffe600",
  magalu: "#0086ff",
  shopee: "#ee4d2d",
  casasbahia: "#0060a8",
  americanas: "#e60014",
  kabum: "#ff6500",
  aliexpress: "#e43225",
};

function getMarketplaceColor(marketplace) {
  return MARKETPLACE_COLORS[marketplace] || "#6366f1";
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadProducts();
  setupNavigation();
});

function setupNavigation() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      document.querySelectorAll(".view").forEach((v) => {
        v.classList.remove("active");
        v.style.display = "none";
      });
      const view = document.getElementById(`${btn.dataset.view}-view`);
      if (view) {
        view.classList.add("active");
        view.style.display = "block";
      }
    });
  });

  document.getElementById("back-btn").addEventListener("click", () => {
    showView("products-view");
    activateNavBtn("products");
  });
}

function showView(viewId) {
  document.querySelectorAll(".view").forEach((v) => {
    v.classList.remove("active");
    v.style.display = "none";
  });
  const view = document.getElementById(viewId);
  view.classList.add("active");
  view.style.display = "block";
}

function activateNavBtn(viewName) {
  document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
  const btn = document.querySelector(`.nav-btn[data-view="${viewName}"]`);
  if (btn) btn.classList.add("active");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ─── Products View ──────────────────────────────────────────

async function loadProducts() {
  const grid = document.getElementById("products-grid");
  let trackedProducts = [];

  // Try API first (logged-in user), fall back to local storage
  const { token } = await chrome.storage.local.get("token");
  if (token) {
    try {
      trackedProducts = await api.getTrackedProducts();
    } catch (err) {
      console.warn("[Wardrop] API fetch failed, falling back to local storage:", err);
    }
  }

  if (trackedProducts.length === 0) {
    const local = await chrome.storage.local.get("trackedProducts");
    trackedProducts = local.trackedProducts || [];
  }

  if (trackedProducts.length === 0) {
    grid.innerHTML = '<p class="empty-state">Nenhum produto acompanhado ainda. Visite um marketplace para começar.</p>';
    return;
  }

  // Group products by group_id
  const groupIds = new Set();
  const standalone = [];
  for (const p of trackedProducts) {
    if (p.group_id) {
      groupIds.add(p.group_id);
    } else {
      standalone.push(p);
    }
  }

  // Fetch full group data and auto-track untracked siblings
  const trackedIds = new Set(trackedProducts.map((p) => p.id));
  const groupDataMap = {};
  await Promise.all(
    [...groupIds].map(async (gid) => {
      try {
        const data = await api.getGroupComparison(gid);
        groupDataMap[gid] = data.group.products;

        // Auto-track siblings that aren't tracked yet (retroactive sync)
        if (token) {
          const untrackedSiblings = data.group.products.filter((p) => !trackedIds.has(p.id));
          for (const sib of untrackedSiblings) {
            try {
              await api.trackProduct(sib.id);
              console.info("[Wardrop] Auto-tracked sibling %s (%s)", sib.id, sib.marketplace);
            } catch { /* already tracked or error — skip */ }
          }
        }
      } catch (err) {
        console.warn("[Wardrop] Could not fetch group", gid, err);
        groupDataMap[gid] = trackedProducts.filter((p) => p.group_id === gid);
      }
    })
  );

  // Build display items
  const displayItems = [];

  for (const [groupId, products] of Object.entries(groupDataMap)) {
    const sorted = [...products].sort(
      (a, b) => parseFloat(a.current_price || Infinity) - parseFloat(b.current_price || Infinity)
    );
    const cheapest = sorted[0];
    const prices = products.map((p) => parseFloat(p.current_price || 0)).filter((p) => p > 0);
    const minPrice = prices.length ? Math.min(...prices) : 0;
    const maxPrice = prices.length ? Math.max(...prices) : 0;

    // Use earliest tracked_at from the products the user actually tracks
    const trackedInGroup = trackedProducts.filter((p) => p.group_id === groupId);
    const trackedAt = trackedInGroup.length
      ? Math.min(...trackedInGroup.map((p) => new Date(p.tracked_at || p.created_at).getTime()))
      : Date.now();

    displayItems.push({
      type: "group",
      id: cheapest.id,
      group_id: groupId,
      name: cheapest.name,
      image_url: cheapest.image_url,
      currency: cheapest.currency || "BRL",
      min_price: minPrice,
      max_price: maxPrice,
      marketplaces: products.map((p) => p.marketplace || "—"),
      tracked_at: trackedAt,
    });
  }

  for (const p of standalone) {
    displayItems.push({ type: "single", ...p });
  }

  grid.innerHTML = displayItems
    .map((item) => {
      if (item.type === "group") {
        const badges = item.marketplaces
          .map(
            (mp) =>
              `<span class="marketplace-badge" style="background:${getMarketplaceColor(mp)}20;color:${getMarketplaceColor(mp)}">${escapeHtml(mp)}</span>`
          )
          .join("");
        const priceText =
          item.min_price !== item.max_price
            ? `${item.currency} ${item.min_price.toFixed(2)} — ${item.max_price.toFixed(2)}`
            : `${item.currency} ${item.min_price.toFixed(2)}`;
        return `
          <div class="product-card" data-product-id="${escapeHtml(item.id || "")}">
            ${item.image_url ? `<img class="product-img" src="${escapeHtml(item.image_url)}" alt="">` : '<div class="product-img-placeholder"></div>'}
            <div class="product-body">
              <div class="marketplace-badges">${badges}</div>
              <div class="name" title="${escapeHtml(item.name || "")}">${escapeHtml(item.name || "Produto")}</div>
              <div class="price">${priceText}</div>
              <div class="tracked-since">Desde ${new Date(item.tracked_at).toLocaleDateString("pt-BR")}</div>
            </div>
          </div>
        `;
      } else {
        return `
          <div class="product-card" data-product-id="${escapeHtml(item.id || "")}" data-url="${escapeHtml(item.url || "")}">
            ${item.image_url ? `<img class="product-img" src="${escapeHtml(item.image_url)}" alt="">` : '<div class="product-img-placeholder"></div>'}
            <div class="product-body">
              <div class="marketplace">${escapeHtml(item.marketplace || "—")}</div>
              <div class="name" title="${escapeHtml(item.name || "")}">${escapeHtml(item.name || "Produto")}</div>
              <div class="price">${escapeHtml(item.currency || "BRL")} ${escapeHtml(String(item.current_price || "—"))}</div>
              <div class="tracked-since">Desde ${new Date(item.tracked_at || item.created_at).toLocaleDateString("pt-BR")}</div>
            </div>
          </div>
        `;
      }
    })
    .join("");

  grid.querySelectorAll(".product-card").forEach((card) => {
    card.addEventListener("click", () => {
      const productId = card.dataset.productId;
      if (productId) showProductDetail(productId);
    });
  });
}

async function showProductDetail(productId) {
  try {
    const data = await fetch(`${API_BASE}/products/${productId}/history`).then((r) =>
      r.json()
    );

    const product = data.product;
    const detailInfo = document.getElementById("detail-info");
    detailInfo.innerHTML = `
      <div class="detail-marketplace">${escapeHtml(product.marketplace || "—")}</div>
      <h2>${escapeHtml(product.name || "Produto")}</h2>
      <div class="detail-price">${escapeHtml(product.currency)} ${escapeHtml(String(product.current_price))}</div>
    `;

    const comparisonDiv = document.getElementById("detail-comparison");

    if (product.group_id) {
      // Has group → load comparison data
      const groupData = await api.getGroupComparison(product.group_id);
      const products = groupData.group.products;
      const bestPrice = Math.min(...products.map((p) => parseFloat(p.current_price || Infinity)));

      const tbody = document.getElementById("detail-comparison-tbody");
      tbody.innerHTML = products
        .map((p) => {
          const price = parseFloat(p.current_price || 0);
          const isBest = price === bestPrice;
          const history = groupData.price_histories[p.marketplace] || [];
          const lowestEver = history.length > 0
            ? Math.min(...history.map((h) => parseFloat(h.price)))
            : price;

          return `
            <tr class="${isBest ? "best-price-row" : ""}">
              <td>
                <span class="marketplace-dot" style="background: ${getMarketplaceColor(p.marketplace)}"></span>
                ${escapeHtml(p.marketplace || "—")}
              </td>
              <td class="${isBest ? "best-price" : ""}">R$ ${price.toFixed(2)}</td>
              <td>R$ ${lowestEver.toFixed(2)}</td>
              <td>${escapeHtml(p.seller || "—")}</td>
              <td><a href="${escapeHtml(p.url)}" target="_blank" class="table-link">Visitar</a></td>
            </tr>
          `;
        })
        .join("");

      comparisonDiv.style.display = "block";
      showView("product-detail");
      renderComparisonChart(groupData.price_histories, "detail-chart");
    } else {
      // No group → simple single chart
      comparisonDiv.style.display = "none";
      showView("product-detail");
      renderSinglePriceChart(data.history, "detail-chart");
    }
  } catch (err) {
    console.error("[Wardrop] Failed to load product detail:", err);
  }
}

function renderSinglePriceChart(history, canvasId) {
  const ctx = document.getElementById(canvasId).getContext("2d");

  if (currentChart) {
    currentChart.destroy();
  }

  const labels = history.map((h) =>
    new Date(h.scraped_at).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "short",
    })
  );
  const prices = history.map((h) => parseFloat(h.price));

  currentChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Preço",
          data: prices,
          borderColor: "#6366f1",
          backgroundColor: "rgba(99, 102, 241, 0.1)",
          fill: true,
          tension: 0.3,
          pointRadius: 3,
          pointHoverRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `R$ ${ctx.parsed.y.toFixed(2)}`,
          },
        },
      },
      scales: {
        y: {
          ticks: {
            callback: (val) => `R$ ${val}`,
            color: "#94a3b8",
          },
          grid: { color: "#1e293b" },
        },
        x: {
          ticks: { color: "#94a3b8" },
          grid: { color: "#1e293b" },
        },
      },
    },
  });
}

// ─── Comparison Chart ───────────────────────────────────────

function renderComparisonChart(priceHistories, canvasId) {
  const ctx = document.getElementById(canvasId).getContext("2d");

  if (currentChart) {
    currentChart.destroy();
  }

  // Build datasets — one line per marketplace
  const datasets = [];
  const allDates = new Set();

  for (const [marketplace, history] of Object.entries(priceHistories)) {
    for (const h of history) {
      allDates.add(new Date(h.scraped_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" }));
    }
  }

  const labels = [...allDates].sort();

  for (const [marketplace, history] of Object.entries(priceHistories)) {
    const color = getMarketplaceColor(marketplace);
    const dataMap = {};
    for (const h of history) {
      const label = new Date(h.scraped_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
      dataMap[label] = parseFloat(h.price);
    }

    datasets.push({
      label: marketplace,
      data: labels.map((l) => dataMap[l] ?? null),
      borderColor: color,
      backgroundColor: color + "20",
      fill: false,
      tension: 0.3,
      pointRadius: 4,
      pointHoverRadius: 7,
      spanGaps: true,
    });
  }

  currentChart = new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true,
          labels: { color: "#94a3b8" },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: R$ ${ctx.parsed.y.toFixed(2)}`,
          },
        },
      },
      scales: {
        y: {
          ticks: {
            callback: (val) => `R$ ${val}`,
            color: "#94a3b8",
          },
          grid: { color: "#1e293b" },
        },
        x: {
          ticks: { color: "#94a3b8" },
          grid: { color: "#1e293b" },
        },
      },
    },
  });
}
