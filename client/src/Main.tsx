import React, { useEffect, useState } from "react";
import mapKeys from "lodash/mapKeys";
import { Form, Field } from "react-final-form";
import validateEthereumAddress from "./validators";

import "./Main.sass";
import { isObject, isString, map, toPairs } from "lodash";

const Main = () => {
  const [transactions, setTransactions] = useState([]);

  const onSubmit = (data: any) => {
    const address = data.address;
    console.log("hello");
    fetch(`/api/wallet/${address}`)
      .then((res) => res.json())
      .then((data) => setTransactions(data.transactions));
    // .then((data) => {
    //   setTransactions(data);
    // });
  };

  console.log(transactions);

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
                value="0x225ef95fa90f4F7938A5b34234d14768cB4263dd"
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
      {transactions.length > 0 &&
        map(transactions, (transaction) => (
          <ul key={transaction.hash}>
            {map(toPairs(transaction), (value) => (
              <li key={`${transaction.hash}-${value[0]}`}>
                {value[0]}: {value[1]}
              </li>
            ))}
          </ul>
        ))}
    </div>
  );
};

export default Main;
