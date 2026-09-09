import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider, useApp } from "./context/AppContext";
import { AppShell } from "./components/layout/AppShell";

// Pages
import { LoginPage } from "./pages/LoginPage";
import { AuthCallback } from "./pages/AuthCallback";
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
  const { isAuthenticated, isAuthLoading } = useApp();

  if (isAuthLoading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", backgroundColor: "var(--bg-app)" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--text-muted)", letterSpacing: "0.08em" }}>
          INITIALIZING WORKSPACE...
        </div>
      </div>
    );
  }

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
          <Route path="/auth/callback" element={<AuthCallback />} />

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
