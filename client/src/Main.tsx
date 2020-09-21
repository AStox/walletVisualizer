import React, { useEffect, useState } from "react";
import { Form, Field } from "react-final-form";
import validateEthereumAddress from "./validators";
import { LineChart, Line, CartesianGrid, XAxis, YAxis } from "recharts";

import "./Main.sass";
import { isObject, isString, map, reduce, toPairs } from "lodash";

const Main = () => {
  const [transactions, setTransactions] = useState([]);
  const [address, setAddress] = useState("");
  const balance;

  const onSubmit = (data: any) => {
    // const address = data.address;
    const address = "0x225ef95fa90f4F7938a5b34234d14768cb4263dd".toLowerCase();
    console.log("hello");
    fetch(`/api/wallet/${address}`)
      .then((res) => res.json())
      .then((data) => {
        setTransactions(data.transactions);
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
      {/* {transactions.length > 0 &&
        map(transactions, (transaction) => (
          <ul key={transaction.hash}>
            {map(toPairs(transaction), (value) => (
              <li key={`${transaction.hash}-${value[0]}`}>
                {value[0]}: {value[1]}
              </li>
            ))}
          </ul>
        ))} */}
      <LineChart
        width={800}
        height={400}
        data={formatTransactions(transactions, address)}
      >
        <Line type="monotone" dataKey="balance" stroke="#8884d8" />
        <CartesianGrid stroke="#ccc" />
        <XAxis dataKey="timestamp" />
        <YAxis />
      </LineChart>
    </div>
  );
};

const formatTransactions = (transactions, wallet) => {
  let ret = [];
  reduce(
    map(transactions, (transaction) => ({
      ...transaction,
      value: transaction.value * 0.000000000000000001,
    })),
    (balance, transaction) => {
      console.log(wallet, transaction.to);
      transaction.to === wallet
        ? (balance += transaction.value)
        : (balance -= transaction.value);
      // transaction.balance = balance;
      ret.push({ ...transaction, balance });
      return balance;
    },
    0
  );
  // for (let i = 0; i < transactions.length; i++) {
  //   let balance;
  //   console.log(transactions[i].value);
  //   if (transactions[i].value) {
  //     balance =
  //       i === 0
  //         ? transactions[i].value
  //         : transactions[i - 1].balance + transactions[i].value;
  //   } else {
  //     balance = i === 0 ? 0 : transactions[i - 1].balance;
  //   }
  //   ret.push({
  //     ...transactions[i],
  //     balance,
  //   });
  // }
  console.log(ret);
  return ret;
};

export default Main;
