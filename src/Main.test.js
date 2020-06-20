import React from "react";
import { render } from "@testing-library/react";

import Main from "./Main";

it("renders the container div", () => {
  const { getByTestId } = render(<Main />);
  getByTestId('Main');
});
