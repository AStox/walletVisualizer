import "react-hot-loader/patch";
import React from "react";
import ReactDom from "react-dom";
import App from "./App";

if (typeof window !== "undefined") {
  ReactDom.render(<App />, document.getElementById("root"));
}
