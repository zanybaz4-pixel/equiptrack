import React from "react";
import { createRoot } from "react-dom/client";
import SessionGate from "./SessionGate.jsx";
import "./styles.css";
import "./workspace.css";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <SessionGate />
  </React.StrictMode>,
);
