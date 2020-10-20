import { map } from "lodash";
import React from "react";
import { Area, Line } from "recharts";

const LineFactory = (transactions, showUSD, chooseColor) => {
  if (!transactions) return null;
  let index = 0;
  return map(transactions[transactions.length - 1]["balances"], (_, key) => {
    index += 1;
    return (
      <Line
        key={key}
        type="monotone"
        dataKey={showUSD ? `balancesUSD.${key}` : `balances.${key}`}
        stroke={chooseColor(index)}
        strokeWidth="0"
      />
    );
  });
};

export const AreaFactory = (transactions, showUSD, chooseColor) => {
  if (!transactions) return null;
  let index = 0;
  return map(transactions[transactions.length - 1]["balances"], (_, key) => {
    index += 1;
    return (
      <Area
        key={key}
        type="monotone"
        dataKey={showUSD ? `balancesUSD.${key}` : `balances.${key}`}
        stroke={chooseColor(index)}
        fill={chooseColor(index)}
        stackId={1}
        strokeWidth="3"
      />
    );
  });
};

export default LineFactory;
