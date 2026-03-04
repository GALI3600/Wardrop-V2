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
import { MARKETPLACE_COLORS, getMpFavicon } from "@/lib/marketplaces";

function useChartTheme() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  return {
    grid: isDark ? "#334155" : "#f1f5f9",
    tick: isDark ? "#94a3b8" : "#94a3b8",
    tooltipBg: isDark ? "#1e293b" : "#ffffff",
    tooltipBorder: isDark ? "#334155" : "#e2e8f0",
    tooltipLabel: isDark ? "#cbd5e1" : "#475569",
    tooltipText: isDark ? "#f1f5f9" : "#1e293b",
    areaStroke: isDark ? "#818cf8" : "#6366f1",
    areaFill: isDark ? "rgba(129, 140, 248, 0.15)" : "rgba(99, 102, 241, 0.08)",
    legendText: isDark ? "#94a3b8" : "#64748b",
    cursorLine: isDark ? "rgba(148, 163, 184, 0.2)" : "rgba(148, 163, 184, 0.3)",
  };
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  const day = d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
  const time = d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return `${day} ${time}`;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload, label, ct }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-lg px-3 py-2.5 text-xs shadow-xl border"
      style={{
        background: ct.tooltipBg,
        borderColor: ct.tooltipBorder,
      }}
    >
      <p className="font-medium mb-1.5" style={{ color: ct.tooltipLabel }}>
        {label}
      </p>
      {payload.map((entry: { color: string; name: string; value: number }, i: number) => (
        <div key={i} className="flex items-center gap-2 py-0.5">
          <span
            className="w-2.5 h-2.5 rounded-full shrink-0"
            style={{ background: entry.color }}
          />
          <span className="capitalize" style={{ color: ct.tooltipLabel }}>
            {entry.name === "price" ? "Preço" : entry.name}
          </span>
          <span className="ml-auto font-semibold pl-3" style={{ color: ct.tooltipText }}>
            R$ {Number(entry.value ?? 0).toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomLegend({ payload, ct }: any) {
  if (!payload?.length) return null;
  return (
    <div className="flex items-center justify-center gap-4 mt-2 flex-wrap">
      {payload.map((entry: { color: string; value: string }, i: number) => {
        const favicon = getMpFavicon(entry.value);
        return (
          <div key={i} className="flex items-center gap-1.5 text-xs" style={{ color: ct.legendText }}>
            {favicon ? (
              <img src={favicon} alt={entry.value} className="w-3.5 h-3.5" />
            ) : (
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ background: entry.color }}
              />
            )}
            <span className="capitalize">{entry.value}</span>
          </div>
        );
      })}
    </div>
  );
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

  const prices = data.map((d) => d.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = (maxPrice - minPrice) * 0.1 || 10;

  return (
    <div className="bg-[var(--bg-card)] rounded-xl p-6 mt-4" style={{ boxShadow: "var(--shadow)" }}>
      <h3 className="text-sm font-semibold text-[var(--text-secondary)] mb-4">Histórico de Preços</h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={ct.areaStroke} stopOpacity={0.2} />
                <stop offset="100%" stopColor={ct.areaStroke} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: ct.tick, fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              dy={8}
            />
            <YAxis
              tick={{ fill: ct.tick, fontSize: 11 }}
              tickFormatter={(v) => `R$${v}`}
              axisLine={false}
              tickLine={false}
              domain={[minPrice - padding, maxPrice + padding]}
              dx={-4}
            />
            <Tooltip
              content={<CustomTooltip ct={ct} />}
              cursor={{ stroke: ct.cursorLine, strokeWidth: 1, strokeDasharray: "4 4" }}
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke={ct.areaStroke}
              fill="url(#priceGradient)"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 2, fill: ct.tooltipBg, stroke: ct.areaStroke }}
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
        Comparativo de Preços
      </h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: ct.tick, fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              dy={8}
            />
            <YAxis
              tick={{ fill: ct.tick, fontSize: 11 }}
              tickFormatter={(v) => `R$${v}`}
              axisLine={false}
              tickLine={false}
              dx={-4}
            />
            <Tooltip
              content={<CustomTooltip ct={ct} />}
              cursor={{ stroke: ct.cursorLine, strokeWidth: 1, strokeDasharray: "4 4" }}
            />
            <Legend content={<CustomLegend ct={ct} />} />
            {marketplaces.map((mp) => {
              const color = MARKETPLACE_COLORS[mp] || "#6366f1";
              return (
                <Line
                  key={mp}
                  type="monotone"
                  dataKey={mp}
                  stroke={color}
                  strokeWidth={2.5}
                  dot={false}
                  activeDot={{ r: 5, strokeWidth: 2, fill: ct.tooltipBg, stroke: color }}
                  connectNulls
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
