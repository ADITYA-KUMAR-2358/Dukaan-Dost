import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { OverviewPage } from "./features/dashboard/OverviewPage";
import { ImportPage } from "./features/imports/ImportPage";
import { InventoryPage } from "./features/inventory/InventoryPage";
import { ForecastPage } from "./features/forecasts/ForecastPage";
import { RecommendationsPage } from "./features/recommendations/RecommendationsPage";
import { ReportsPage } from "./features/reports/ReportsPage";
import { SettingsPage } from "./features/settings/SettingsPage";
import { ServerWake } from "./components/ServerWake";
import { MarketingPage } from "./pages/MarketingPage";
import { LimitsPage, NotFoundPage, RouteErrorPage } from "./pages/PublicPages";
import "./styles/tokens.css";

const router = createBrowserRouter([
  { path: "/", element: <MarketingPage />, errorElement: <RouteErrorPage /> },
  { path: "/limits", element: <LimitsPage /> },
  {
    path: "/app",
    element: <AppLayout />,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: "import", element: <ImportPage /> },
      { path: "inventory", element: <InventoryPage /> },
      { path: "forecasts", element: <ForecastPage /> },
      { path: "recommendations", element: <RecommendationsPage /> },
      { path: "reports", element: <ReportsPage /> },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ServerWake />
    <RouterProvider router={router} />
  </StrictMode>,
);
