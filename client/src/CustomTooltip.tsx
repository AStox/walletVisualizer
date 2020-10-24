import { map, reduce } from "lodash";
import React, { useEffect } from "react";
import "./CustomTooltip.sass";

const ColoredBalance = ({
  symbol,
  val,
  showUSD,
  color,
  _24hourChange,
  _1weekChange,
  price,
}: {
  symbol: string;
  val: number;
  showUSD: boolean;
  color: string;
  _24hourChange: number;
  _1weekChange: number;
  price: number;
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
    <td>${price.toFixed(2)}</td>
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
      {props.payload && props.payload[0] && (
        <>
          <div className="date">
            {new Date(props.payload[0].payload.timeStamp * 1000).toDateString()}
          </div>
          <div className="total-balance">
            {`$${reduce(
              props.payload[0].payload.balancesUSD,
              (sum, bal) => bal + sum
            ).toFixed(2)}`}
          </div>
        </>
      )}
      <table>
        <tr>
          <th>Token</th>
          <th>Value</th>
          <th>24hr</th>
          <th>1wk</th>
          <th>Price</th>
        </tr>
        {props.payload &&
          props.payload[0] &&
          map(
            map(
              props.showUSD
                ? props.payload[0].payload.balancesUSD
                : props.payload[0].payload.balances,
              (val, key) => [val, key]
            ).reverse(),
            (arr) => {
              const val = arr[0];
              const key = arr[1];
              return (
                <ColoredBalance
                  key={key}
                  symbol={key}
                  val={val}
                  showUSD={props.showUSD}
                  color={props.colorMap[key]}
                  _24hourChange={props.payload[0].payload._24hourChange[key]}
                  _1weekChange={props.payload[0].payload._1weekChange[key]}
                  price={props.payload[0].payload.prices[key]}
                />
              );
            }
          )}
      </table>
    </div>
  );
};

export default CustomTooltip;
