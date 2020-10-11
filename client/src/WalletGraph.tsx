import { map } from "lodash";
import React, { Dispatch, MutableRefObject, SetStateAction, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import CustomTooltip from "./CustomTooltip";
import LineFactory from "./LineFactory";

import "./walletGraph.sass";

interface Props {
  targetRef: MutableRefObject<undefined>;
  setTransaction: Dispatch<SetStateAction<Transaction>>;
  transactions: Transaction[];
  showUSD: boolean;
}





const WalletGraph = ({
  targetRef,
  transactions,
  setTransaction,
  showUSD,
}: Props) => {
  // console.log(transactions);
  // console.log(showUSD);

  const [colorIndex, setColorIndex] = useState(0)

  const chooseColor = () => {
    const colors = [
      "#C6920C",
      "#1DB6D4",
      '#E25635',
      "#08A984",
      "#A959F1"
    ];
    setColorIndex(colorIndex + 1);
    return colors[colorIndex - 1];
  }

  
  return (
    <div className="WalletGraph">
      <LineChart
        width={targetRef.current ? targetRef.current.offsetWidth : 10}
        height={400}
        data={transactions}
      >
        <Tooltip
          content={
            <CustomTooltip setTransaction={setTransaction} showUSD={showUSD} />
          }
        />
        {LineFactory(transactions,showUSD, chooseColor )}
        {/* <Line
          type="monotone"
          dataKey={showUSD ? "balancesUSD.ETH" : "balances.ETH"}
          stroke="#C6920C"
          strokeWidth="3"
        />
        <Line
          type="monotone"
          dataKey={showUSD ? "balancesUSD.DAI" : "balances.DAI"}
          stroke="#1DB6D4"
          strokeWidth="3"
        />
         <Line
          type="monotone"
          dataKey={showUSD ? "balancesUSD.ETH/DAI" : "balances.ETH/DAI"}
          stroke="#E25635"
          strokeWidth="3"
        /> */}
        {/*<Line
          type="monotone"
          dataKey={showUSD ? "balancesUSD.USDT" : "balances.USDT"}
          stroke="#E25635"
          strokeWidth="3"
        />
        <Line
          type="monotone"
          dataKey={showUSD ? "balancesUSD.LINK" : "balances.LINK"}
          stroke="#08A984"
          strokeWidth="3"
        />
        <Line
          type="monotone"
          dataKey={showUSD ? "balancesUSD.PUD" : "balances.PUD"}
          stroke="#A959F1"
          strokeWidth="3"
        /> */}
        <CartesianGrid stroke="#2B1820" vertical={false} />
        <XAxis
          dataKey="timeStamp"
          stroke="#C52E52"
          tick={false}
          axisLine={false}
          padding={{ left: 60, right: 60 }}
        />
        <YAxis
          stroke="#C52E52"
          tickSize={0}
          axisLine={false}
          mirror={true}
          tickMargin={150}
        />
      </LineChart>
    </div>
  );
};

export default WalletGraph;