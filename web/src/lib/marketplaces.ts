export const MARKETPLACE_COLORS: Record<string, string> = {
  amazon: "#ff9900",
  mercadolivre: "#ffe600",
  magalu: "#0086ff",
  shopee: "#ee4d2d",
  casasbahia: "#0060a8",
  americanas: "#e60014",
  kabum: "#ff6500",
  aliexpress: "#e43225",
};

const MARKETPLACE_DOMAINS: Record<string, string> = {
  amazon: "amazon.com.br",
  mercadolivre: "mercadolivre.com.br",
  magalu: "magazineluiza.com.br",
  shopee: "shopee.com.br",
  casasbahia: "casasbahia.com.br",
  americanas: "americanas.com.br",
  kabum: "kabum.com.br",
  aliexpress: "aliexpress.com",
};

export function getMpColor(mp: string | null): string {
  return MARKETPLACE_COLORS[mp || ""] || "#6366f1";
}

export function getMpFavicon(mp: string | null): string | null {
  const domain = MARKETPLACE_DOMAINS[mp || ""];
  if (!domain) return null;
  return `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
}
