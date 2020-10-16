import { map } from "lodash";
import React from "react";
import { Area, Line } from "recharts";

const LineFactory = (transactions, showUSD, chooseColor) => {
  if (!transactions) return null;
  let index = 0;
  const colors = ["#C6920C", "#1DB6D4", "#E25635", "#08A984", "#A959F1"];
  return map(transactions[transactions.length - 1]["balances"], (_, key) => {
    index += 1;
    console.log(colors[index % colors.length]);
    return (
      <Line
        key={key}
        type="monotone"
        dataKey={showUSD ? `balancesUSD.${key}` : `balances.${key}`}
        stroke={colors[index % colors.length]}
        strokeWidth="3"
      />
    );
  });
};

export const AreaFactory = (transactions, showUSD, chooseColor) => {
  if (!transactions) return null;
  let index = 0;
  const colors = ["#C6920C", "#1DB6D4", "#E25635", "#08A984", "#A959F1"];
  return map(transactions[transactions.length - 1]["balances"], (_, key) => {
    index += 1;
    const color = colors[index % colors.length];
    return (
      <Area
        key={key}
        type="monotone"
        dataKey={showUSD ? `balancesUSD.${key}` : `balances.${key}`}
        stroke={color}
        fill={color}
        stackId={1}
        strokeWidth="3"
      />
    );
  });
};

export default LineFactory;
