import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine
} from "recharts";

export function DamageChart({ data }) {
  const chartData = data || [
    { date: "Jan 2026", score: 28, label: "Low" },
    { date: "Mar 2026", score: 34, label: "Low" },
    { date: "May 2026", score: 52, label: "Medium" },
    { date: "Jul 2026", score: 68, label: "High" },
    { date: "Aug 2026", score: 86, label: "Critical" }
  ];

  return (
    <div style={{ width: "100%", height: 260 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 15, right: 20, left: -15, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2DDD5" vertical={false} />
          <XAxis
            dataKey="date"
            stroke="#8E857B"
            tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
          />
          <YAxis
            domain={[0, 100]}
            stroke="#8E857B"
            tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#FFFFFF",
              border: "1px solid #E2DDD5",
              borderRadius: "4px",
              fontSize: "11px",
              fontFamily: "var(--font-sans)"
            }}
          />
          <ReferenceLine y={50} stroke="#D97706" strokeDasharray="3 3" label={{ value: "Warning Threshold (50)", fill: "#D97706", fontSize: 10 }} />
          <ReferenceLine y={75} stroke="#DC2626" strokeDasharray="3 3" label={{ value: "Critical Threshold (75)", fill: "#DC2626", fontSize: 10 }} />
          <Line
            type="monotone"
            dataKey="score"
            name="Damage Severity Score"
            stroke="#A04022"
            strokeWidth={2.5}
            dot={{ r: 4, fill: "#A04022", stroke: "#FFFFFF", strokeWidth: 2 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
