import type { ProductOut, PriceHistoryEntry } from "@/lib/types";

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

interface ComparisonTableProps {
  products: ProductOut[];
  priceHistories: Record<string, PriceHistoryEntry[]>;
}

export default function ComparisonTable({ products, priceHistories }: ComparisonTableProps) {
  const bestPrice = Math.min(
    ...products.map((p) => Number(p.current_price ?? Infinity))
  );

  return (
    <div className="bg-slate-800 rounded-xl overflow-hidden mt-4">
      <h3 className="text-sm font-semibold text-slate-400 px-6 pt-5 pb-3">
        Preços em outros Marketplaces
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Marketplace
              </th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Preço Atual
              </th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Menor Preço
              </th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Vendedor
              </th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Link
              </th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => {
              const price = Number(p.current_price ?? 0);
              const isBest = price === bestPrice;
              const history = priceHistories[p.marketplace || ""] || [];
              const lowestEver =
                history.length > 0
                  ? Math.min(...history.map((h) => Number(h.price)))
                  : price;
              const mpColor = MARKETPLACE_COLORS[p.marketplace || ""] || "#6366f1";

              return (
                <tr
                  key={p.id}
                  className={`border-b border-slate-700/50 ${isBest ? "bg-emerald-500/5" : ""}`}
                >
                  <td className="px-6 py-4 text-sm">
                    <span
                      className="inline-block w-2 h-2 rounded-full mr-2"
                      style={{ background: mpColor }}
                    />
                    <span className="capitalize">{p.marketplace || "—"}</span>
                  </td>
                  <td className={`px-6 py-4 text-sm ${isBest ? "text-emerald-400 font-bold" : ""}`}>
                    R$ {price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 text-sm">R$ {lowestEver.toFixed(2)}</td>
                  <td className="px-6 py-4 text-sm text-slate-400">{p.seller || "—"}</td>
                  <td className="px-6 py-4 text-sm">
                    <a
                      href={p.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-400 hover:text-indigo-300 hover:underline"
                    >
                      Visitar
                    </a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
