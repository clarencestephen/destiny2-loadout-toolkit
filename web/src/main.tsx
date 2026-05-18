import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./App";
import Dashboard from "./pages/Dashboard";
import Landing from "./pages/Landing";
import Chat from "./pages/Chat";
import Link from "./pages/Link";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Landing />} />
          <Route path="app" element={<Dashboard />} />
          <Route path="chat" element={<Chat />} />
          <Route path="link" element={<Link />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
