import React, { useState } from "react";
import { BrowserRouter as Router, Route, Link } from "react-router-dom";

import Main from "./Main";
import ToDo from "./ToDo";

import "./App.sass";

const App = () => {
  const toDoItems = ["build", "destroy"];
  return (
    <Router>
      <div className="App">
        <Main>
          <Route path="/todo">
            <ToDo items={toDoItems} />
            <Link to="/">Back</Link>
          </Route>
          <Route exact path="/">
            <Link to="/todo">Todo</Link>
            <Main />
          </Route>
        </Main>
      </div>
    </Router>
  );
};

export default App;
