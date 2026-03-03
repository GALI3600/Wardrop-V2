/**
 * Content script: detects if the current page is a product page
 * and extracts relevant HTML for parsing.
 *
 * Extraction strategy (cheapest first):
 *   1. Try schema.org JSON-LD (structured data already in the page)
 *   2. Send full HTML to backend for LLM parsing (fallback)
 */

const PRODUCT_URL_PATTERNS = {
  "amazon.com.br": /\/(dp|gp\/product)\/[A-Z0-9]{10}/,
  "mercadolivre.com.br": /MLB-?\d+/,
  "magazineluiza.com.br": /\/(produto|p)\/[a-z0-9]+\//i,
  "shopee.com.br": /(\/product\/\d+\/\d+|-i\.\d+\.\d+)/,
  "casasbahia.com.br": /\/produto\/\d+/,
  "americanas.com.br": /\/produto\/\d+/,
  "kabum.com.br": /\/produto\/\d+/,
  "aliexpress.com": /\/item\/\d+\.html/,
};

function getMarketplace() {
  const hostname = window.location.hostname;
  for (const [domain, pattern] of Object.entries(PRODUCT_URL_PATTERNS)) {
    if (hostname.includes(domain) && pattern.test(window.location.pathname)) {
      return domain.split(".")[0];
    }
  }
  return null;
}

/**
 * Try to extract product data from schema.org JSON-LD in the page.
 * Returns product data object if found, null otherwise.
 */
function extractSchemaOrg() {
  const scripts = document.querySelectorAll('script[type="application/ld+json"]');

  for (const script of scripts) {
    try {
      const data = JSON.parse(script.textContent);
      const product = findProduct(data);
      if (product) {
        return parseSchemaProduct(product);
      }
    } catch (e) {
      continue;
    }
  }

  return null;
}

function findProduct(data) {
  if (Array.isArray(data)) {
    for (const item of data) {
      const result = findProduct(item);
      if (result) return result;
    }
    return null;
  }

  if (data && typeof data === "object") {
    const type = data["@type"];
    const types = Array.isArray(type) ? type : [type];
    if (types.includes("Product")) return data;

    // Search in @graph or nested values
    for (const value of Object.values(data)) {
      if (typeof value === "object") {
        const result = findProduct(value);
        if (result) return result;
      }
    }
  }

  return null;
}

function parseSchemaProduct(data) {
  const name = data.name;
  if (!name) return null;

  const offers = Array.isArray(data.offers) ? data.offers[0] : data.offers || {};
  const price =
    offers["@type"] === "AggregateOffer"
      ? offers.lowPrice || offers.price
      : offers.price;

  if (!price) return null;

  const ean =
    data.gtin13 || data.gtin14 || data.gtin12 || data.gtin8 ||
    data.gtin || data.productID || data.mpn || data.sku || null;

  let image = data.image;
  if (Array.isArray(image)) image = image[0];
  if (image && typeof image === "object") image = image.url || image.contentUrl;

  let seller = offers.seller;
  if (seller && typeof seller === "object") seller = seller.name;

  const availability = offers.availability || "";
  const available = availability ? availability.includes("InStock") : true;

  return {
    name: String(name),
    price: parseFloat(price),
    currency: offers.priceCurrency || "BRL",
    seller: seller || null,
    image_url: image ? String(image) : null,
    available,
    ean: ean ? String(ean) : null,
    source: "schema_org",
  };
}

/**
 * Try to extract the main product image URL from the live DOM.
 * Works even when images are loaded via JS (e.g., Amazon's data-a-dynamic-image).
 */
function extractMainImage() {
  // Amazon: #landingImage or #imgBlkFront
  const amazonImg = document.querySelector("#landingImage, #imgBlkFront, #main-image");
  if (amazonImg) {
    // Prefer data-old-hires (high-res), then src
    return amazonImg.getAttribute("data-old-hires") || amazonImg.src || null;
  }

  // Generic: og:image meta tag (works on most sites)
  const ogImage = document.querySelector('meta[property="og:image"]');
  if (ogImage) return ogImage.content || null;

  // Fallback: first large product image
  const imgs = document.querySelectorAll('img[src*="product"], img[src*="images/I/"], img[src*="http"]');
  for (const img of imgs) {
    if (img.naturalWidth > 200 && img.naturalHeight > 200) {
      return img.src;
    }
  }

  return null;
}

function extractPageHTML() {
  const clone = document.documentElement.cloneNode(true);

  const removeSelectors = [
    "style", "nav", "footer", "header", "iframe", "noscript",
    "[role='navigation']", "[role='banner']", "[role='contentinfo']",
    ".nav", ".footer", ".header", "#nav", "#footer", "#header",
  ];

  removeSelectors.forEach((sel) => {
    clone.querySelectorAll(sel).forEach((el) => el.remove());
  });

  return clone.innerHTML;
}

// Main execution
(function () {
  const marketplace = getMarketplace();
  if (!marketplace) return;

  const url = window.location.href;

  // Camada 1: Try schema.org first
  const schemaData = extractSchemaOrg();

  if (schemaData) {
    // schema.org found — send minimal data to backend (no HTML needed for LLM)
    schemaData.marketplace = marketplace;
    if (!schemaData.image_url) schemaData.image_url = extractMainImage();
    chrome.runtime.sendMessage(
      {
        type: "PARSE_PRODUCT",
        payload: { html: document.documentElement.outerHTML, url, marketplace, schemaData },
      },
      (response) => {
        if (response && response.product) {
          window.dispatchEvent(
            new CustomEvent("wardrop:product-parsed", { detail: response.product })
          );
        }
      }
    );
    return;
  }

  // Camada 3: No schema.org — send HTML for LLM parsing
  const html = extractPageHTML();
  const image_url = extractMainImage();
  chrome.runtime.sendMessage(
    {
      type: "PARSE_PRODUCT",
      payload: { html, url, marketplace, image_url },
    },
    (response) => {
      if (response && response.product) {
        window.dispatchEvent(
          new CustomEvent("wardrop:product-parsed", { detail: response.product })
        );
      }
    }
  );
})();
