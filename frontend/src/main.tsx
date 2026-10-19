import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ToastProvider } from "./ui";
import App from "./App";
import { UploadProvider } from "./Uploads";
import ErrorBoundary from "./ErrorBoundary";
import "./styles.css";
import "./workspace.css";
import "./agent.css";
import "./capabilities.css";
import "./polish.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <ToastProvider>
          <UploadProvider>
            <App />
          </UploadProvider>
        </ToastProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>,
);
