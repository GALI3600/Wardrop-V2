"use client";

import { LineChart, Line, ResponsiveContainer } from "recharts";
import type { SparklinePoint } from "@/lib/types";

interface SparklineChartProps {
  data: SparklinePoint[];
  color?: string;
}

export default function SparklineChart({ data, color = "#6366f1" }: SparklineChartProps) {
  if (data.length < 2) return null;

  const chartData = data.map((d) => ({ price: Number(d.price) }));

  return (
    <div className="w-full h-10">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
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
