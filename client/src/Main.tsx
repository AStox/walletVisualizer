import React, { useEffect, useRef, useState } from "react";

import AddressInput from "./AddressInput";
import WalletGraph from "./WalletGraph";
import { listParams } from "./Utils";
import Toggle from "react-toggle";
import { IoLogoUsd } from "react-icons/io";
import { FaEthereum } from "react-icons/fa";

import "./Main.sass";
import "react-toggle/style.css";
import { filter, forEach, includes } from "lodash";

const Main = () => {
  const targetRef = useRef();
  const [addressData, setAddressData] = useState<
    | {
        transactions: Transaction[];
        all_tokens: string[];
        last_block_number: number;
      }
    | undefined
  >(undefined);
  const [transaction, setTransaction] = useState({});
  const [address, setAddress] = useState("");
  const [showUSD, setShowUSD] = useState(true);
  const [taskId, setTaskId] = useState(null);

  useEffect(() => {
    if (taskId) {
      fetchTaskStatus();
    }
  }, [taskId]);

  const fetchTaskStatus = () => {
    const url = `/api/status/${taskId}`;
    fetch(url)
      .then((res) => res.json())
      .then((res) => {
        console.log(res);
        if (res.state != "PENDING" && res.state != "PROGRESS") {
          console.log(res);
        } else {
          setTimeout(() => fetchTaskStatus(), 1000);
        }
      });
  };

  const formatRawData = (data) => {
    const mergeArrays = (
      transactions1: Transaction[],
      transactions2: Transaction[]
    ) => {
      let dupesArray: number[] = [];
      let returnArray: Transaction[] = [];
      transactions1.pop();
      forEach(transactions1, (tx1) => {
        let dupe = false;
        forEach(transactions2, (tx2: Transaction) => {
          if (tx1.timeStamp === tx2.timeStamp) {
            dupesArray.push(transactions2.indexOf(tx2));
            dupe = true;
            // returnArray.push({
            //   ...tx1,
            //   ...tx2,
            //   balances: { ...tx1.balances, ...tx2.balances },
            //   balancesUSD: { ...tx1.balancesUSD, ...tx2.balancesUSD },
            // });
          }
        });
        if (!dupe) {
          returnArray.push(tx1);
        }
      });
      const lastTx = returnArray[returnArray.length - 1];
      // returnArray.pop();
      forEach(transactions2, (tx) => {
        if (!includes(dupesArray, transactions2.indexOf(tx))) {
          returnArray.push({
            ...lastTx,
            ...tx,
            balances: { ...lastTx.balances, ...tx.balances },
            balancesUSD: { ...lastTx.balancesUSD, ...tx.balancesUSD },
          });
        }
      });
      return returnArray;
    };

    if (addressData) {
      const transactions = mergeArrays(
        addressData.transactions,
        data.transactions
      );

      console.log("old: ", addressData.transactions);
      console.log("new: ", transactions);

      setAddressData({
        last_block_number: addressData?.last_block_number,
        transactions: transactions,
        all_tokens: [...addressData?.all_tokens, ...data.all_tokens],
      });
    } else {
      setAddressData(data);
    }
    setAddress(address);
  };

  const onSubmit = (data: any) => {
    const address = data.address.toLowerCase();
    const blockNumber = addressData?.last_block_number || 0;
    const url = `/api/wallet/${address}?blockNumber=${blockNumber}`;

    fetch(url)
      .then((res) => res.json())
      .then((res) => setTaskId(res.task_id));
    // .then((res) => res.json())
    // .then((data) => formatRawData(data));
  };

  return (
    <div className="Main" data-testid="Main">
      <div className="flex-container">
        <div className="input-flex-container">
          <div className="input-container">
            <AddressInput onSubmit={onSubmit} />
          </div>
        </div>
        <div className="toggle-flex-container">
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
      </div>
      <div ref={targetRef}>
        <WalletGraph
          targetRef={targetRef}
          setTransaction={setTransaction}
          transactions={addressData?.transactions}
          allTokens={addressData?.all_tokens}
          showUSD={showUSD}
        />
      </div>
      <div>
        <ul>{listParams(transaction)}</ul>
      </div>
    </div>
  );
};

export default Main;
