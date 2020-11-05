import React, { useRef, useState } from "react";

import AddressInput from "./AddressInput";
import WalletGraph from "./WalletGraph";
import { listParams } from "./Utils";
import Toggle from "react-toggle";
import { IoLogoUsd } from "react-icons/io";
import { FaEthereum } from "react-icons/fa";

import "./Main.sass";
import "react-toggle/style.css";
import { filter, forEach } from "lodash";

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
  // const [allTokens, setAllTokens] = useState<string[] | undefined>(undefined);
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
    const blockNumber = addressData?.last_block_number || 0;
    const url = `/api/wallet/${address}?blockNumber=${blockNumber}`;
    // url.search = new URLSearchParams(params).toString();
    // console.log(url.toString());

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        if (addressData) {
          let transactions = [
            ...addressData?.transactions,
            ...data.transactions,
          ];
          transactions = [...new Set(transactions)];
          const checkDupes = (tx2: Transaction) => {
            forEach(transactions, (tx1: Transaction) => {
              if (tx1.timeStamp === tx2.timeStamp) {
                return false;
              }
            });
            return true;
          };
          // transactions = filter(transactions, checkDupes);
          setAddressData({
            last_block_number: addressData?.last_block_number,
            transactions: transactions,
            all_tokens: [...addressData?.transactions, ...data.transactions],
          });
        } else {
          setAddressData(data);
        }
        setAddress(address);
      });
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
