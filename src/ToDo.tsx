import React from "react";

const ToDo = ({ items }: { items: string[] }) => {
  return (
    <li>
      {items.map(item => (
        <ul>{item}</ul>
      ))}
    </li>
  );
};

export default ToDo;
