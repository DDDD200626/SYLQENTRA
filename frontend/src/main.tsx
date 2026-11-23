import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

const savedPath = sessionStorage.getItem("sylqentra-path");
if (savedPath) {
  sessionStorage.removeItem("sylqentra-path");
  const base = import.meta.env.BASE_URL.replace(/\/$/, "");
  const path = savedPath.startsWith("/") ? savedPath : `/${savedPath}`;
  window.history.replaceState(null, "", path === "/" ? `${base}/` : `${base}${path}`);
}

document.title = "SYLQENTRA";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
