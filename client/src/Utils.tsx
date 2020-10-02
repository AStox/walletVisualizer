import React from "react";
import { isObject, map, toPairs } from "lodash";

export const listParams = (obj: object) => {
  return map(toPairs(obj), (value) => {
    return !isObject(value[1]) ? (
      <li key={value[0]}>
        {value[0]}: {value[1]}
      </li>
    ) : (
      <li key={value[0]}>
        {value[0]}:<ul>{listParams(value[1])}</ul>
      </li>
    );
  });
};
