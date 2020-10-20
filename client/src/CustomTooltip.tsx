import { map, reduce } from "lodash";
import React, { useEffect } from "react";
import "./CustomTooltip.sass";
import { listParams } from "./Utils";

const CustomTooltip = (props) => {
  useEffect(() => {
    if (props.active && props.payload && props.payload[0]) {
      props.setTransaction(props.payload[0].payload);
    }
  });
  const options = { year: "numeric", month: "long", day: "numeric" };
  return (
    <div className="CustomTooltip">
      {props.payload &&
        props.payload[0] &&
        listParams({
          date: new Date(
            props.payload[0].payload.timeStamp * 1000
          ).toLocaleDateString("en-US", options),
          // name: props.payload[0].payload.name,
          // from: props.payload[0].payload.fromName,
          // to: props.payload[0].payload.toName,
          Total: `$${reduce(
            props.payload[0].payload.balancesUSD,
            (sum, bal) => bal + sum
          ).toFixed(2)}`,
        })}
      {props.payload &&
        props.payload[0] &&
        map(
          props.showUSD
            ? props.payload[0].payload.balancesUSD
            : props.payload[0].payload.balances,
          (val, key) => {
            return (
              <ColoredBalance
                symbol={key}
                val={val}
                showUSD={props.showUSD}
                color={props.colorMap[key]}
              />
            );
          }
        )}
    </div>
  );
};

const ColoredBalance = ({
  symbol,
  val,
  showUSD,
  color,
}: {
  symbol: string;
  val: number;
  showUSD: boolean;
  color: string;
}) => (
  <div style={{ color }}>
    {symbol}: {showUSD && "$"}
    {val.toFixed(2)}
  </div>
);

export default CustomTooltip;
