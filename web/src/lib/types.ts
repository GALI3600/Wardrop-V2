export interface SparklinePoint {
  price: number;
  scraped_at: string;
}

export interface MarketplacePrice {
  marketplace: string | null;
  current_price: number | null;
  product_id: string;
}

export interface ProductListItem {
  id: string;
  url: string;
  marketplace: string | null;
  name: string | null;
  image_url: string | null;
  current_price: number | null;
  currency: string;
  seller: string | null;
  ean: string | null;
  group_id: string | null;
  last_scraped_at: string | null;
  created_at: string;
  marketplace_prices: MarketplacePrice[];
  price_max: number | null;
  sparkline: SparklinePoint[];
  price_change_pct: number | null;
  lowest_price: number | null;
  highest_price: number | null;
  is_at_lowest: boolean;
}

export interface ProductListResponse {
  products: ProductListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface MarketplaceOption {
  name: string;
  count: number;
}

export interface FilterOptionsResponse {
  marketplaces: MarketplaceOption[];
  price_min: number | null;
  price_max: number | null;
  total_products: number;
}

export interface PriceHistoryEntry {
  price: number;
  seller: string | null;
  available: boolean;
  scraped_at: string;
}

export interface ProductOut {
  id: string;
  url: string;
  marketplace: string | null;
  name: string | null;
  image_url: string | null;
  current_price: number | null;
  currency: string;
  seller: string | null;
  ean: string | null;
  group_id: string | null;
  last_scraped_at: string | null;
  created_at: string;
}

export interface ProductHistoryOut {
  product: ProductOut;
  history: PriceHistoryEntry[];
}

export interface ProductGroupOut {
  id: string;
  canonical_name: string | null;
  ean: string | null;
  products: ProductOut[];
}

export interface GroupComparisonOut {
  group: ProductGroupOut;
  price_histories: Record<string, PriceHistoryEntry[]>;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface UserOut {
  id: string;
  email: string;
  notify_email: boolean;
  notify_push: boolean;
}

export interface ListParams {
  search?: string;
  marketplace?: string;
  min_price?: number;
  max_price?: number;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}
