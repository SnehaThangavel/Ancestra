import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider, useApp } from "./context/AppContext";
import { AppShell } from "./components/layout/AppShell";

// Pages
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ImageAnalysisPage } from "./pages/expert/ImageAnalysisPage";
import { AIAnalysisPage } from "./pages/expert/AIAnalysisPage";
import { ResultsPage } from "./pages/expert/ResultsPage";
import { DamageHistoryPage } from "./pages/expert/DamageHistoryPage";
import { HeritageSitesPage } from "./pages/admin/HeritageSitesPage";
import { RegionsPage } from "./pages/admin/RegionsPage";
import { ReportsPage } from "./pages/ReportsPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { ProfilePage } from "./pages/ProfilePage";

function ProtectedRoutes() {
  const { isAuthenticated } = useApp();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <AppShell />;
}

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<ProtectedRoutes />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            
            {/* Expert Routes */}
            <Route path="/expert/image-analysis" element={<ImageAnalysisPage />} />
            <Route path="/expert/ai-analysis" element={<AIAnalysisPage />} />
            <Route path="/expert/results" element={<ResultsPage />} />
            <Route path="/expert/damage-history" element={<DamageHistoryPage />} />
            
            {/* Admin Routes */}
            <Route path="/admin/heritage-sites" element={<HeritageSitesPage />} />
            <Route path="/admin/architectural-regions" element={<RegionsPage />} />
            
            {/* Common Routes */}
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<ProfilePage />} />
          </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}
