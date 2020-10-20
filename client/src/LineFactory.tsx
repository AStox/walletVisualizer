import { map } from "lodash";
import React from "react";
import { Area, Line } from "recharts";

const LineFactory = (transactions, showUSD, colorMap) => {
  if (!transactions) return null;
  return map(transactions[transactions.length - 1]["balances"], (_, key) => {
    return (
      <Line
        key={key}
        type="monotone"
        dataKey={showUSD ? `balancesUSD.${key}` : `balances.${key}`}
        stroke={colorMap[key]}
        strokeWidth="0"
      />
    );
  });
};

export const GradientFactory = (transactions, colorMap) => {
  if (!transactions) return null;
  return map(transactions[transactions.length - 1]["balances"], (_, key) => {
    return (
      <defs>
        <linearGradient id={`color${key}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="5%" stopColor={colorMap[key]} stopOpacity={0.65} />
          <stop offset="95%" stopColor={colorMap[key]} stopOpacity={0} />
        </linearGradient>
      </defs>
    );
  });
};

export const AreaFactory = (transactions, showUSD, colorMap) => {
  if (!transactions) return null;
  return map(transactions[transactions.length - 1]["balances"], (_, key) => {
    return (
      <Area
        key={key}
        type="monotone"
        dataKey={showUSD ? `balancesUSD.${key}` : `balances.${key}`}
        stroke={colorMap[key]}
        fill={`url(#color${key})`}
        stackId={1}
        strokeWidth="none"
        dot={false}
        activeDot={false}
      />
    );
  });
};

export default LineFactory;
