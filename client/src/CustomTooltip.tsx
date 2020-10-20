import { spawn } from "child_process";
import { map, reduce } from "lodash";
import React, { Dispatch, SetStateAction, useEffect } from "react";
import { Tooltip, TooltipProps } from "recharts";
import "./CustomTooltip.sass";
import { listParams } from "./Utils";

// interface Props extends TooltipProps {
//   onChange: Dispatch<SetStateAction<{}>>;
// }

const CustomTooltip = (props) => {
  let index = 0;
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
            index += 1;
            return (
              <ColoredBalance
                symbol={key}
                val={val}
                index={index}
                showUSD={props.showUSD}
                colorChooser={props.colorChooser}
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
  index,
  showUSD,
  colorChooser,
}: {
  symbol: string;
  val: number;
  index: number;
  showUSD: boolean;
  colorChooser(index: number): string;
}) => (
  <div style={{ color: colorChooser(index) }}>
    {symbol}: {showUSD && "$"}
    {val.toFixed(2)}
  </div>
);

export default CustomTooltip;
