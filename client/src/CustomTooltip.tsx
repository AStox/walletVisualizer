import { isNumber, map, reduce } from "lodash";
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
    {showUSD && _24hourChange && (
      <td style={{ color: _24hourChange[symbol] > 0 ? "green" : "red" }}>
        {_24hourChange[symbol] ? _24hourChange[symbol].toFixed(2) : "--"}%
      </td>
    )}
    {showUSD && _1weekChange && (
      <td style={{ color: _1weekChange[symbol] > 0 ? "green" : "red" }}>
        {_1weekChange[symbol] ? _1weekChange[symbol].toFixed(2) : "--"}%
      </td>
    )}
    <td>${isNumber(price) ? price.toFixed(2) : "--"}</td>
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
          <table className="total-balance-table">
            <tr>
              <td className="total-balance" style={{ display: "inline" }}>
                {`$${props.payload[0].payload.total_balance_USD.toFixed(2)}`}
              </td>
              <td className="percent-change">
                <tr>
                  {props.payload[0].payload._24hourChange && (
                    <td
                      style={{
                        color:
                          (props.payload[0].payload._24hourChange.total || 0) >
                          0
                            ? "green"
                            : "red",
                      }}
                    >
                      {(
                        props.payload[0].payload._24hourChange.total || 0
                      ).toFixed(2)}
                      %
                    </td>
                  )}
                  {props.payload[0].payload._1weekChange && (
                    <td
                      style={{
                        color:
                          (props.payload[0].payload._1weekChange.total || 0) > 0
                            ? "green"
                            : "red",
                      }}
                    >
                      {(
                        props.payload[0].payload._1weekChange.total || 0
                      ).toFixed(2)}
                      %
                    </td>
                  )}
                </tr>
                <tr>
                  <th>24hr</th>
                  <th>1wk</th>
                </tr>
              </td>
            </tr>
          </table>
        </>
      )}
      <table className="token-balance-table">
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
                  _24hourChange={props.payload[0].payload._24hourChange}
                  _1weekChange={props.payload[0].payload._1weekChange}
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
