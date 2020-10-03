import React, { useEffect, useMemo, useRef, useState } from "react";

import { forEach, isObject, map, reduce, sortBy, toPairs } from "lodash";
import AddressInput from "./AddressInput";
import WalletGraph from "./WalletGraph";
import { listParams } from "./Utils";
import Toggle from "react-toggle";
import { IoLogoUsd } from "react-icons/io";
import { FaEthereum } from "react-icons/fa";

import "./Main.sass";
import "react-toggle/style.css";

const Main = () => {
  const targetRef = useRef();
  const [transactions, setTransactions] = useState<Transaction[] | undefined>(
    undefined
  );
  const [transaction, setTransaction] = useState({});
  const [address, setAddress] = useState("");
  const [showUSD, setShowUSD] = useState(true);

  // useEffect(() => {
  //   // if (targetRef.current) {
  //   //   setDimensions({
  //   //     width: targetRef.current.offsetWidth,
  //   //     height: targetRef.current.offsetHeight,
  //   //   });
  //   // }
  //   const data = {
  //     address: "0x225ef95fa90f4F7938a5b34234d14768cb4263dd".toLowerCase(),
  //   };
  //   useMemo(() => onSubmit(data), [data]), [];
  // });

  const onSubmit = (data: any) => {
    const address = data.address.toLowerCase();
    // const address = "0x225ef95fa90f4F7938a5b34234d14768cb4263dd".toLowerCase();

    fetch(`/api/wallet/${address}`)
      .then((res) => res.json())
      .then((data) => {
        setTransactions(data.transactions);
        setAddress(address);
      });
  };

  return (
    <div className="Main" data-testid="Main">
      <div className="flex-container">
        <div className="input-container">
          <AddressInput onSubmit={onSubmit} />
        </div>
        <div className="toggle-container">
          <Toggle
            className={"custom-toggle"}
            onChange={() => setShowUSD(!showUSD)}
            icons={{
              checked: <FaEthereum />,
              unchecked: <IoLogoUsd />,
            }}
          />
        </div>
      </div>
      <div ref={targetRef}>
        <WalletGraph
          targetRef={targetRef}
          setTransaction={setTransaction}
          transactions={transactions}
          showUSD={showUSD}
        />
      </div>
      <div>
        <ul>{listParams(transaction)}</ul>
      </div>
    </div>
  );
};

// const formatTransactions = (transactions: Transaction[]) => {
//   let ret = [] as Transaction[];
//   reduce(
//     transactions,
//     (balances, transaction) => {
//       let tempBal = {} as Values;
//       forEach(transaction.values, (value, key) => {
//         tempBal = { ...balances };
//         if (transaction.isError == 0) {
//           tempBal[key] = (balances[key] || 0) + value;
//           balances[key] = tempBal[key];
//         }
//       });
//       const usd = reduce(
//         tempBal,
//         (obj, value, key) => ({
//           ...obj,
//           [key]: value * transaction.prices[key],
//         }),
//         {}
//       );
//       const newTrans = { ...transaction, balances: tempBal, balancesUSD: usd };
//       ret.push(newTrans);
//       return balances;
//     },
//     {} as Values
//   );
//   // return sortBy(ret, "timeStamp");
//   return ret;
// };

export default Main;
