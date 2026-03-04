const API_BASE = "https://wardrop.api.serverapp.com.br/api";

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "PARSE_PRODUCT") {
    handleParseProduct(message.payload)
      .then((product) => sendResponse({ product }))
      .catch((err) => {
        console.error("[Wardrop] Parse error:", err);
        sendResponse({ error: err.message });
      });
    return true; // Keep message channel open for async response
  }

  if (message.type === "TRACK_PRODUCT") {
    handleTrackProduct(message.payload)
      .then(() => sendResponse({ success: true }))
      .catch((err) => {
        console.error("[Wardrop] Track error:", err);
        sendResponse({ error: err.message });
      });
    return true;
  }
});

async function handleParseProduct({ html, url, marketplace, image_url }) {
  const [response] = await Promise.all([
    fetch(`${API_BASE}/products/parse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ html, url, image_url }),
    }),
    syncTrackedProducts(),
  ]);

  if (!response.ok) {
    throw new Error(`API returned ${response.status}`);
  }

  return response.json();
}

async function syncTrackedProducts() {
  const { token } = await chrome.storage.local.get("token");
  if (!token) return;
  try {
    const res = await fetch(`${API_BASE}/tracking/products`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const trackedProducts = await res.json();
      await chrome.storage.local.set({ trackedProducts });
    }
  } catch {}
}

async function handleTrackProduct(product) {
  const { token } = await chrome.storage.local.get("token");

  if (token) {
    // User is logged in — save to backend (auto-tracks siblings)
    await fetch(`${API_BASE}/tracking/track`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        product_id: product.id,
        notify_on_any_drop: true,
      }),
    });
  }

  // Always save locally too (hybrid mode)
  const { trackedProducts = [] } = await chrome.storage.local.get(
    "trackedProducts"
  );

  // If product has a group, fetch and track all siblings
  let productsToTrack = [product];
  if (product.group_id) {
    try {
      const res = await fetch(
        `${API_BASE}/products/groups/${product.group_id}/compare`
      );
      if (res.ok) {
        const data = await res.json();
        productsToTrack = data.group.products;
      }
    } catch (e) {
      console.warn("[Wardrop] Could not fetch group siblings:", e);
    }
  }

  for (const p of productsToTrack) {
    const exists = trackedProducts.some((tp) => tp.url === p.url);
    if (!exists) {
      trackedProducts.push({
        ...p,
        tracked_at: new Date().toISOString(),
      });
    }
  }

  await chrome.storage.local.set({ trackedProducts });
}
