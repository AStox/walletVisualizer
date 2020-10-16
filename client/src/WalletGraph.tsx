import { map } from "lodash";
import React, {
  Dispatch,
  MutableRefObject,
  SetStateAction,
  useState,
} from "react";
import {
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import CustomTooltip from "./CustomTooltip";
import LineFactory, { AreaFactory } from "./LineFactory";

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

  const [colorIndex, setColorIndex] = useState(0);

  const chooseColor = () => {
    const colors = ["#C6920C", "#1DB6D4", "#E25635", "#08A984", "#A959F1"];
    setColorIndex(colorIndex + 1);
    return colors[colorIndex - 1];
  };

  return (
    <div className="WalletGraph">
      <AreaChart
        width={targetRef.current ? targetRef.current.offsetWidth : 10}
        height={400}
        data={transactions}
      >
        <Tooltip
          content={
            <CustomTooltip setTransaction={setTransaction} showUSD={showUSD} />
          }
        />
        {/* {LineFactory(transactions,showUSD, chooseColor )} */}
        {AreaFactory(transactions, showUSD, chooseColor)}
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
      </AreaChart>
    </div>
  );
};

export default WalletGraph;
