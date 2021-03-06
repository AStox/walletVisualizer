import { map, shuffle } from "lodash";
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
import LineFactory, { AreaFactory, GradientFactory } from "./LineFactory";

import "./WalletGraph.sass";

interface Props {
  targetRef: MutableRefObject<undefined>;
  setTransaction: Dispatch<SetStateAction<Transaction>>;
  transactions: Transaction[];
  allTokens: string[];
  showUSD: boolean;
}

const WalletGraph = ({
  targetRef,
  transactions,
  allTokens,
  setTransaction,
  showUSD,
}: Props) => {
  let colorsArray = [
    "#C6920C",
    "#1DB6D4",
    "#E25635",
    "#08A984",
    "#A959F1",
    "#CBBE3B",
    "#DAD6D6",
    "#F7B538",
    "#C9FBFF",
    "#A1E8AF",
    "#7FB069",
    "#CC2936",
    "#FF8811",
    "#3C91E6",
    "#CE4257",
    "#A3C4BC",
  ];
  // colors = shuffle(colors);
  const [colors, setColors] = useState(shuffle(colorsArray));
  const colorChooser = (index: number) => {
    return colors[index % colors.length];
  };

  const symbolColorMap: { [key: string]: string } = {};
  let index = 0;
  if (allTokens && allTokens.length > 0) {
    map(allTokens, (key) => {
      symbolColorMap[key] = colorChooser(index);
      index += 1;
    });
  }
  return (
    <div className="WalletGraph">
      <AreaChart
        width={targetRef.current ? targetRef.current.offsetWidth : 10}
        height={400}
        data={transactions}
      >
        {GradientFactory(transactions, allTokens, symbolColorMap)}
        {/* {LineFactory(transactions, allTokens, showUSD, chooseColor )} */}
        {AreaFactory(transactions, allTokens, showUSD, symbolColorMap)}
        <Tooltip
          content={
            <CustomTooltip
              setTransaction={setTransaction}
              showUSD={showUSD}
              colorMap={symbolColorMap}
            />
          }
        />

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
