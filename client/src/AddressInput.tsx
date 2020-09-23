import { disconnect } from "process";
import React from "react";
import { Field, Form } from "react-final-form";
import "./AddressInput.sass";

interface Props {
  onSubmit(data: any): void;
}

const AddressInput = ({ onSubmit }: Props) => {
  return (
    <div className="AddressInput">
      <Form
        onSubmit={onSubmit}
        render={({ handleSubmit }) => (
          <form onSubmit={handleSubmit}>
            <Field name="address" component="input" placeholder="0x" />
          </form>
        )}
      />
    </div>
  );
};

export default AddressInput;
