import React, { Dispatch, SetStateAction, useEffect } from "react";
import { Tooltip, TooltipProps } from "recharts";
import "./CustomTooltip.sass";
import { listParams } from "./Utils";

// interface Props extends TooltipProps {
//   onChange: Dispatch<SetStateAction<{}>>;
// }

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
          name: props.payload[0].payload.name,
          from: props.payload[0].payload.fromName,
          to: props.payload[0].payload.toName,
          balances: props.showUSD
            ? props.payload[0].payload.balancesUSD
            : props.payload[0].payload.balances,
        })}
    </div>
  );
};

// const CustomTooltip = (props: Props) => {
//   if (props.payload && props.payload[0]) {
//     props.onChange(props.payload[0].payload);
//   }
//   return <div class="CustomTooltip"></div>;
// };

export default CustomTooltip;
