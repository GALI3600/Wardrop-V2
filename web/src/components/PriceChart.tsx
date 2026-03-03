"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  LineChart,
  Line,
} from "recharts";
import type { PriceHistoryEntry } from "@/lib/types";

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

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
  });
}

interface SingleChartProps {
  history: PriceHistoryEntry[];
}

export function SinglePriceChart({ history }: SingleChartProps) {
  const data = history.map((h) => ({
    date: formatDate(h.scraped_at),
    price: Number(h.price),
  }));

  return (
    <div className="bg-slate-800 rounded-xl p-6 mt-4">
      <h3 className="text-sm font-semibold text-slate-400 mb-4">Histórico de Preços</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 12 }} />
            <YAxis
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              tickFormatter={(v) => `R$${v}`}
            />
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              labelStyle={{ color: "#94a3b8" }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(value: any) => [`R$ ${Number(value ?? 0).toFixed(2)}`, "Preço"]}
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke="#6366f1"
              fill="rgba(99, 102, 241, 0.15)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

interface MultiChartProps {
  priceHistories: Record<string, PriceHistoryEntry[]>;
}

export function ComparisonPriceChart({ priceHistories }: MultiChartProps) {
  // Collect all dates
  const allDates = new Set<string>();
  for (const history of Object.values(priceHistories)) {
    for (const h of history) {
      allDates.add(formatDate(h.scraped_at));
    }
  }
  const dates = [...allDates].sort();

  // Build data array with one key per marketplace
  const data = dates.map((date) => {
    const point: Record<string, string | number> = { date };
    for (const [mp, history] of Object.entries(priceHistories)) {
      const entry = history.find((h) => formatDate(h.scraped_at) === date);
      if (entry) point[mp] = Number(entry.price);
    }
    return point;
  });

  const marketplaces = Object.keys(priceHistories);

  return (
    <div className="bg-slate-800 rounded-xl p-6 mt-4">
      <h3 className="text-sm font-semibold text-slate-400 mb-4">
        Histórico de Preços por Marketplace
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 12 }} />
            <YAxis
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              tickFormatter={(v) => `R$${v}`}
            />
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              labelStyle={{ color: "#94a3b8" }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(value: any, name: any) => [`R$ ${Number(value ?? 0).toFixed(2)}`, String(name)]}
            />
            <Legend wrapperStyle={{ color: "#94a3b8" }} />
            {marketplaces.map((mp) => (
              <Line
                key={mp}
                type="monotone"
                dataKey={mp}
                stroke={MARKETPLACE_COLORS[mp] || "#6366f1"}
                strokeWidth={2}
                dot={{ r: 3 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
