import type {
  FilterOptionsResponse,
  GroupComparisonOut,
  ListParams,
  ProductHistoryOut,
  ProductListResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
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
