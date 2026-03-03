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
import { useTheme } from "@/providers/ThemeProvider";

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

function useChartTheme() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  return {
    grid: isDark ? "#334155" : "#e2e8f0",
    tick: isDark ? "#94a3b8" : "#64748b",
    tooltipBg: isDark ? "#1e293b" : "#ffffff",
    tooltipBorder: isDark ? "#334155" : "#e2e8f0",
    tooltipLabel: isDark ? "#94a3b8" : "#64748b",
    areaStroke: isDark ? "#818cf8" : "#6366f1",
    areaFill: isDark ? "rgba(129, 140, 248, 0.15)" : "rgba(99, 102, 241, 0.1)",
    legendText: isDark ? "#94a3b8" : "#64748b",
  };
}

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
  const ct = useChartTheme();
  const data = history.map((h) => ({
    date: formatDate(h.scraped_at),
    price: Number(h.price),
  }));

  return (
    <div className="bg-[var(--bg-card)] rounded-xl p-6 mt-4" style={{ boxShadow: "var(--shadow)" }}>
      <h3 className="text-sm font-semibold text-[var(--text-secondary)] mb-4">Histórico de Preços</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
            <XAxis dataKey="date" tick={{ fill: ct.tick, fontSize: 12 }} />
            <YAxis
              tick={{ fill: ct.tick, fontSize: 12 }}
              tickFormatter={(v) => `R$${v}`}
            />
            <Tooltip
              contentStyle={{ background: ct.tooltipBg, border: `1px solid ${ct.tooltipBorder}`, borderRadius: 8 }}
              labelStyle={{ color: ct.tooltipLabel }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(value: any) => [`R$ ${Number(value ?? 0).toFixed(2)}`, "Preço"]}
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke={ct.areaStroke}
              fill={ct.areaFill}
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
  const ct = useChartTheme();

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
    <div className="bg-[var(--bg-card)] rounded-xl p-6 mt-4" style={{ boxShadow: "var(--shadow)" }}>
      <h3 className="text-sm font-semibold text-[var(--text-secondary)] mb-4">
        Histórico de Preços por Marketplace
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
            <XAxis dataKey="date" tick={{ fill: ct.tick, fontSize: 12 }} />
            <YAxis
              tick={{ fill: ct.tick, fontSize: 12 }}
              tickFormatter={(v) => `R$${v}`}
            />
            <Tooltip
              contentStyle={{ background: ct.tooltipBg, border: `1px solid ${ct.tooltipBorder}`, borderRadius: 8 }}
              labelStyle={{ color: ct.tooltipLabel }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(value: any, name: any) => [`R$ ${Number(value ?? 0).toFixed(2)}`, String(name)]}
            />
            <Legend wrapperStyle={{ color: ct.legendText }} />
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
