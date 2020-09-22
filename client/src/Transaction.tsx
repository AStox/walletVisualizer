import React, { Dispatch, SetStateAction } from "react";
import { TooltipProps } from "recharts";
import "./Transaction.sass";

interface Props extends TooltipProps {
  onChange: Dispatch<SetStateAction<{}>>;
}

const Transaction = ({ payload, onChange }: Props) => {
  if (payload && payload[0]) {
    onChange(payload[0].payload);
  }
  return null;
};

export default Transaction;
