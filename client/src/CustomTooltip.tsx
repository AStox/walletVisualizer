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

  return (
    <div className="CustomTooltip">
      {props.payload &&
        props.payload[0] &&
        listParams({
          name: props.payload[0].payload.name,
          from: props.payload[0].payload.fromName,
          to: props.payload[0].payload.toName,
          balances: props.payload[0].payload.balances,
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
