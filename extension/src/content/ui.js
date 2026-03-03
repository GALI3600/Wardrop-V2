/**
 * Content script: injects the "Track this product" UI into the page.
 * Starts as a collapsed FAB circle ("W") that expands on click.
 */

function createTrackButton(product) {
  // Remove existing button if any
  const existing = document.getElementById("wardrop-track-btn");
  if (existing) existing.remove();

  const container = document.createElement("div");
  container.id = "wardrop-track-btn";
  container.className = "wardrop-collapsed";
  container.innerHTML = `
    <div class="wardrop-fab" id="wardrop-fab">
      <span class="wardrop-fab-icon">W</span>
    </div>
    <div class="wardrop-widget">
      <button class="wardrop-close-btn" id="wardrop-close-btn">&times;</button>
      <div class="wardrop-info">
        <span class="wardrop-price">${product.currency} ${product.current_price}</span>
        <span class="wardrop-name">${product.name?.substring(0, 50) || "Produto"}</span>
      </div>
      <button class="wardrop-btn" id="wardrop-follow-btn">
        Acompanhar
      </button>
    </div>
  `;

  document.body.appendChild(container);

  // FAB click → expand
  document.getElementById("wardrop-fab").addEventListener("click", () => {
    container.classList.remove("wardrop-collapsed");
    container.classList.add("wardrop-expanded");
  });

  // Close button → collapse
  document.getElementById("wardrop-close-btn").addEventListener("click", () => {
    container.classList.remove("wardrop-expanded");
    container.classList.add("wardrop-collapsed");
  });

  // Check if already tracked
  chrome.storage.local.get("trackedProducts", ({ trackedProducts = [] }) => {
    const isTracked = trackedProducts.some(
      (p) => p.id === product.id || p.url === product.url
    );
    const btn = document.getElementById("wardrop-follow-btn");
    if (isTracked) {
      btn.textContent = "Acompanhando ✓";
      btn.classList.add("wardrop-btn--active");
      document.getElementById("wardrop-fab").classList.add("wardrop-fab--tracked");
    }
  });

  // Handle click
  document.getElementById("wardrop-follow-btn").addEventListener("click", () => {
    chrome.runtime.sendMessage(
      {
        type: "TRACK_PRODUCT",
        payload: product,
      },
      (response) => {
        const btn = document.getElementById("wardrop-follow-btn");
        if (response && response.success) {
          btn.textContent = "Acompanhando ✓";
          btn.classList.add("wardrop-btn--active");
          document.getElementById("wardrop-fab").classList.add("wardrop-fab--tracked");
        }
      }
    );
  });
}

// Listen for parsed product data from extractor.js
window.addEventListener("wardrop:product-parsed", (event) => {
  createTrackButton(event.detail);
});
