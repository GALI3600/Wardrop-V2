import type {
  AuthToken,
  FilterOptionsResponse,
  GroupComparisonOut,
  ListParams,
  ProductHistoryOut,
  ProductListResponse,
  ProductOut,
  UserOut,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function fetchAuthApi<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem("wardrop-token");
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || `API error: ${res.status}`);
  }
  return res.json();
}

// Auth

export async function login(email: string, password: string): Promise<AuthToken> {
  const data = await fetchAuthApi<AuthToken>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("wardrop-token", data.access_token);
  window.dispatchEvent(
    new StorageEvent("storage", { key: "wardrop-token", newValue: data.access_token })
  );
  return data;
}

export async function register(email: string, password: string): Promise<AuthToken> {
  const data = await fetchAuthApi<AuthToken>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("wardrop-token", data.access_token);
  window.dispatchEvent(
    new StorageEvent("storage", { key: "wardrop-token", newValue: data.access_token })
  );
  return data;
}

export function getMe(): Promise<UserOut> {
  return fetchAuthApi<UserOut>("/auth/me");
}

// Tracking

export function getTrackedProducts(): Promise<ProductOut[]> {
  return fetchAuthApi<ProductOut[]>("/tracking/products");
}

export function trackProduct(productId: string): Promise<{ status: string }> {
  return fetchAuthApi("/tracking/track", {
    method: "POST",
    body: JSON.stringify({ product_id: productId }),
  });
}

export function untrackProduct(productId: string): Promise<{ status: string }> {
  return fetchAuthApi(`/tracking/untrack/${productId}`, {
    method: "DELETE",
  });
}

export function getProducts(params: ListParams = {}): Promise<ProductListResponse> {
  const sp = new URLSearchParams();
  if (params.search) sp.set("search", params.search);
  if (params.marketplace) sp.set("marketplace", params.marketplace);
  if (params.min_price !== undefined) sp.set("min_price", String(params.min_price));
  if (params.max_price !== undefined) sp.set("max_price", String(params.max_price));
  if (params.sort_by) sp.set("sort_by", params.sort_by);
  if (params.sort_order) sp.set("sort_order", params.sort_order);
  if (params.page) sp.set("page", String(params.page));
  if (params.page_size) sp.set("page_size", String(params.page_size));
  const qs = sp.toString();
  return fetchApi<ProductListResponse>(`/products/list${qs ? `?${qs}` : ""}`);
}

export function getFilters(): Promise<FilterOptionsResponse> {
  return fetchApi<FilterOptionsResponse>("/products/filters");
}

export function getProductHistory(productId: string): Promise<ProductHistoryOut> {
  return fetchApi<ProductHistoryOut>(`/products/${productId}/history`);
}

export function getGroupComparison(groupId: string): Promise<GroupComparisonOut> {
  return fetchApi<GroupComparisonOut>(`/products/groups/${groupId}/compare`);
}
