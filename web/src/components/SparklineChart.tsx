"use client";

import { LineChart, Line, YAxis, ResponsiveContainer } from "recharts";
import type { SparklinePoint } from "@/lib/types";

interface SparklineChartProps {
  data: SparklinePoint[];
  color?: string;
}

export default function SparklineChart({ data, color = "#6366f1" }: SparklineChartProps) {
  if (data.length < 2) {
    return (
      <div className="w-full h-10 flex items-center justify-center">
        <span className="text-[10px] text-[var(--text-muted)] italic">
          Sem dados suficientes
        </span>
      </div>
    );
  }

  const chartData = data.map((d) => ({ price: Number(d.price) }));

  // Calculate price range with padding to show proportional variations
  const prices = chartData.map((d) => d.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = (maxPrice - minPrice) * 0.1 || 10;

  return (
    <div className="w-full h-10">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <YAxis
            domain={[minPrice - padding, maxPrice + padding]}
            hide={true}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
