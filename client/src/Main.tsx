import React, { useState } from "react";
import { Form, Field } from "react-final-form";
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

import "./Main.sass";
import { forEach, isObject, map, reduce, toPairs } from "lodash";
import Transaction from "./Transaction";

const Main = () => {
  const [transactions, setTransactions] = useState<Transaction[] | undefined>(
    undefined
  );
  const [transaction, setTransaction] = useState({});
  const [address, setAddress] = useState("");

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
      <div>Welcome</div>
      <div>
        <Form
          onSubmit={onSubmit}
          render={({ handleSubmit }) => (
            <form onSubmit={handleSubmit}>
              <Field
                name="address"
                component="input"
                placeholder="0x"
                // validate={validateEthereumAddress}
                render={({ input, meta }) => (
                  <div>
                    <label>Address</label>
                    <input {...input} />
                    {meta.touched && meta.error && (
                      <span style={{ color: "red" }}>{meta.error}</span>
                    )}
                  </div>
                )}
              />
              <div>
                <button type="submit">Pull</button>
              </div>
            </form>
          )}
        />
      </div>
      <div>
        <LineChart width={800} height={400} data={transactions}>
          {/* <Tooltip content={<Transaction onChange={setTransaction} />} />
           */}
          <Tooltip />
          <Line type="monotone" dataKey="balances.ETH" stroke="#8884d8" />
          <Line type="monotone" dataKey="balances.UNI" stroke="#8884d8" />
          <Line type="monotone" dataKey="balances.USDT" stroke="#8884d8" />
          <CartesianGrid stroke="#ccc" />
          <XAxis dataKey="timestamp" />
          <YAxis />
        </LineChart>
      </div>
      <div>
        <ul>{listParams(transaction)}</ul>
      </div>
    </div>
  );
};

const listParams = (obj: object) => {
  return map(toPairs(obj), (value) => {
    return !isObject(value[1]) ? (
      <li key={value[0]}>
        {value[0]}: {value[1]}
      </li>
    ) : (
      <li>
        {value[0]}:<ul>{listParams(value[1])}</ul>
      </li>
    );
  });
};

const formatTransactions = (transactions: Transaction[], wallet: string) => {
  let ret = [] as Transaction[];
  reduce(
    transactions,
    (balances, transaction) => {
      const flow = transaction.to === wallet ? 1 : -1;
      // console.log(balances);
      let tempBal = {} as Values;
      forEach(transaction.values, (value, key) => {
        // console.log(key, key === "ETH");
        tempBal = { ...balances };
        tempBal[key] =
          key === "ETH"
            ? (balances[key] || 0) + value * flow
            : (balances[key] || 0) + value * flow * -1;
        balances[key] =
          key === "ETH"
            ? (balances[key] || 0) + value * flow
            : (balances[key] || 0) + value * flow * -1;
      });
      console.log(tempBal);
      const newTrans = { ...transaction, balances: tempBal };
      console.log(newTrans);
      // console.log(balances);
      ret.push(newTrans);
      console.log(ret);
      return balances;
    },
    {} as Values
  );
  return ret;
};

export default Main;
