import React, { Dispatch, MutableRefObject, SetStateAction } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import CustomTooltip from "./CustomTooltip";

import "./walletGraph.sass";

interface Props {
  targetRef: MutableRefObject<undefined>;
  setTransaction: Dispatch<SetStateAction<Transaction>>;
  transactions: Transaction[];
}

const WalletGraph = ({ targetRef, transactions, setTransaction }: Props) => {
  return (
    <div className="WalletGraph">
      <LineChart
        width={targetRef.current ? targetRef.current.offsetWidth : 10}
        height={400}
        data={transactions}
      >
        <Tooltip content={<CustomTooltip setTransaction={setTransaction} />} />
        <Line
          type="monotone"
          dataKey="balances.ETH"
          stroke="#BEBBBB"
          strokeWidth="3"
        />
        <Line
          type="monotone"
          dataKey="balances.UNI"
          stroke="#BEBBBB"
          strokeWidth="3"
        />
        <Line
          type="monotone"
          dataKey="balances.USDT"
          stroke="#BEBBBB"
          strokeWidth="3"
        />
        <CartesianGrid stroke="#BEBBBB" vertical={false} />
        <XAxis
          dataKey="timestamp"
          stroke="#BEBBBB"
          tick={false}
          axisLine={false}
          padding={{ left: 60, right: 60 }}
        />
        <YAxis
          stroke="#BEBBBB"
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
