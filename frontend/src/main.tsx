import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import App from "./App.tsx";
import "./index.css";
import "@/shared/styles/main.scss";
import { AppProvider } from "@/shared/context/app-context";
import { queryClient } from "@/shared/lib/query-client";
import { LanguageProvider } from "@/features/i18n";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AppProvider>
        <LanguageProvider>
          <App />
        </LanguageProvider>
      </AppProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
