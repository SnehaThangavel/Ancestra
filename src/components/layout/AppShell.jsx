import React from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopHeader } from "./TopHeader";
import { Toast } from "../common/Toast";
import { useApp } from "../../context/AppContext";

export function AppShell() {
  const { toast } = useApp();

  return (
    <div style={styles.appWrapper} className="paper-grid">
      <Sidebar />
      <div style={styles.mainContainer}>
        <TopHeader />
        <main style={styles.contentArea}>
          <Outlet />
        </main>
      </div>
      <Toast toast={toast} />
    </div>
  );
}

const styles = {
  appWrapper: {
    display: "flex",
    minHeight: "100vh",
    width: "100%"
  },
  mainContainer: {
    marginLeft: "var(--sidebar-width)",
    flex: 1,
    display: "flex",
    flexDirection: "column",
    minWidth: 0
  },
  contentArea: {
    flex: 1,
    padding: "24px 28px",
    maxWidth: "1400px"
  }
};
