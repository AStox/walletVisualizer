import { map, reduce } from "lodash";
import React, { useEffect } from "react";
import "./CustomTooltip.sass";
import { listParams } from "./Utils";

const ColoredBalance = ({
  symbol,
  val,
  showUSD,
  color,
  _24hourChange,
  _1weekChange,
}: {
  symbol: string;
  val: number;
  showUSD: boolean;
  color: string;
  _24hourChange: number;
  _1weekChange: number;
}) => (
  <tr style={{ color }}>
    <td>{symbol}</td>
    <td>
      {showUSD && "$"}
      {val.toFixed(2)}
    </td>
    {showUSD && (
      <td style={{ color: _24hourChange > 0 ? "green" : "red" }}>
        {_24hourChange ? _24hourChange.toFixed(2) : "--"}%
      </td>
    )}
    {showUSD && (
      <td style={{ color: _1weekChange > 0 ? "green" : "red" }}>
        {_1weekChange ? _1weekChange.toFixed(2) : "--"}%
      </td>
    )}
  </tr>
);

const CustomTooltip = (props) => {
  useEffect(() => {
    if (props.active && props.payload && props.payload[0]) {
      props.setTransaction(props.payload[0].payload);
    }
  });

  return (
    <div className="CustomTooltip">
      {props.payload &&
        props.payload[0] &&
        listParams({
          date: new Date(
            props.payload[0].payload.timeStamp * 1000
          ).toDateString(),
          Total: `$${reduce(
            props.payload[0].payload.balancesUSD,
            (sum, bal) => bal + sum
          ).toFixed(2)}`,
        })}
      <table>
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
                  _24hourChange={props.payload[0].payload._24hourChange[key]}
                  _1weekChange={props.payload[0].payload._1weekChange[key]}
                />
              );
            }
          )}
      </table>
    </div>
  );
};

export default CustomTooltip;
