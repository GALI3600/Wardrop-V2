"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { getProductHistory, getGroupComparison } from "@/lib/api";
import { SinglePriceChart, ComparisonPriceChart } from "@/components/PriceChart";
import ComparisonTable from "@/components/ComparisonTable";

const MARKETPLACE_COLORS: Record<string, string> = {
  amazon: "#ff9900",
  mercadolivre: "#ffe600",
  magalu: "#0086ff",
  shopee: "#ee4d2d",
  casasbahia: "#0060a8",
  americanas: "#e60014",
  kabum: "#ff6500",
  aliexpress: "#e43225",
};

export default function ProductDetailPage() {
  const params = useParams();
  const productId = params.id as string;

  const { data, isLoading } = useQuery({
    queryKey: ["product-history", productId],
    queryFn: () => getProductHistory(productId),
  });

  const groupId = data?.product.group_id;
  const { data: groupData } = useQuery({
    queryKey: ["group-comparison", groupId],
    queryFn: () => getGroupComparison(groupId!),
    enabled: !!groupId,
  });

  if (isLoading) {
    return <div className="text-center py-20 text-slate-500">Carregando...</div>;
  }

  if (!data) {
    return <div className="text-center py-20 text-slate-500">Produto não encontrado.</div>;
  }

  const { product, history } = data;
  const mpColor = MARKETPLACE_COLORS[product.marketplace || ""] || "#6366f1";

  return (
    <div>
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 text-sm mb-6 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        Voltar
      </Link>

      {/* Product info */}
      <div className="bg-slate-800 rounded-xl p-6 flex flex-col md:flex-row gap-6">
        {product.image_url && (
          <div className="bg-white rounded-lg p-4 flex items-center justify-center w-full md:w-64 h-64 shrink-0">
            <img
              src={product.image_url}
              alt={product.name || "Produto"}
              className="max-h-full max-w-full object-contain"
            />
          </div>
        )}
        <div className="flex flex-col gap-3 flex-1">
          <span
            className="text-xs font-semibold uppercase tracking-wider px-2 py-1 rounded w-fit"
            style={{ background: mpColor + "20", color: mpColor }}
          >
            {product.marketplace || "—"}
          </span>
          <h1 className="text-xl font-bold text-slate-100">
            {product.name || "Produto"}
          </h1>
          <p className="text-3xl font-bold text-emerald-400">
            {product.currency} {Number(product.current_price || 0).toFixed(2)}
          </p>
          {product.seller && (
            <p className="text-sm text-slate-400">
              Vendedor: {product.seller}
            </p>
          )}
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-indigo-400 hover:text-indigo-300 mt-2 w-fit transition"
          >
            <ExternalLink className="w-4 h-4" />
            Ver no marketplace
          </a>
        </div>
      </div>

      {/* Comparison table + multi-marketplace chart (if grouped) */}
      {groupData && (
        <>
          <ComparisonTable
            products={groupData.group.products}
            priceHistories={groupData.price_histories}
          />
          <ComparisonPriceChart priceHistories={groupData.price_histories} />
        </>
      )}

      {/* Single price chart (if not grouped) */}
      {!groupId && history.length > 0 && (
        <SinglePriceChart history={history} />
      )}

      {/* If grouped, also show the single product history below */}
      {groupId && history.length > 0 && (
        <div className="mt-4">
          <SinglePriceChart history={history} />
        </div>
      )}
    </div>
  );
}
