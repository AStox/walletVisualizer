import React, { useEffect, useMemo, useRef, useState } from "react";

import "./Main.sass";
import { forEach, isObject, map, reduce, toPairs } from "lodash";
import AddressInput from "./AddressInput";
import WalletGraph from "./WalletGraph";
import { listParams } from "./Utils";

const Main = () => {
  const targetRef = useRef();
  const [transactions, setTransactions] = useState<Transaction[] | undefined>(
    undefined
  );
  const [transaction, setTransaction] = useState({});
  const [address, setAddress] = useState("");

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
        setTransactions(
          formatTransactions(data.transactions as Transaction[], address)
        );
        setAddress(address);
      });
  };

  return (
    <div className="Main" data-testid="Main">
      <div className="flex-container">
        <div className="input-container">
          <AddressInput onSubmit={onSubmit} />
        </div>
      </div>
      <div ref={targetRef}>
        <WalletGraph
          targetRef={targetRef}
          setTransaction={setTransaction}
          transactions={transactions}
        />
      </div>
      <div>
        <ul>{listParams(transaction)}</ul>
      </div>
    </div>
  );
};

const formatTransactions = (transactions: Transaction[], wallet: string) => {
  let ret = [] as Transaction[];
  reduce(
    transactions,
    (balances, transaction) => {
      const flow = transaction.to === wallet ? 1 : -1;
      let tempBal = {} as Values;
      forEach(transaction.values, (value, key) => {
        console.log(key, value);
        tempBal = { ...balances };
        if (transaction.isError == 0) {
          tempBal[key] = (balances[key] || 0) + value;
          balances[key] = tempBal[key];
        }
        console.log(tempBal[key]);
      });
      const newTrans = { ...transaction, balances: tempBal };
      ret.push(newTrans);
      return balances;
    },
    {} as Values
  );
  return ret;
};

export default Main;
