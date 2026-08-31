import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { Clock, Plus, Landmark, Bell } from "lucide-react";

export function TopHeader() {
  const navigate = useNavigate();
  const { heritageSites, activeSiteId, setActiveSiteId, currentUser, notifications } = useApp();
  const [currentTime, setCurrentTime] = useState("");

  const unreadCount = notifications.filter((n) => !n.read).length;
  const isExpert = currentUser?.role === "CONSERVATION_EXPERT";

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString("en-US", { hour12: false }) + " GMT+5:30";
      setCurrentTime(timeStr);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleActionClick = () => {
    if (isExpert) {
      navigate("/expert/image-analysis");
    } else {
      navigate("/admin/heritage-sites");
    }
  };

  return (
    <header style={styles.headerContainer}>
      <div style={styles.headerMain}>
        {/* Heritage Site Context Selector */}
        <div style={styles.focusSelectorGroup}>
          <Landmark size={14} color="#8E857B" />
          <span style={styles.focusLabel}>FOCUS:</span>
          <select
            value={activeSiteId}
            onChange={(e) => setActiveSiteId(e.target.value)}
            style={styles.focusSelect}
          >
            {heritageSites.map((site) => (
              <option key={site.id} value={site.id}>
                {site.name.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Header Right Tools */}
        <div style={styles.headerRightGroup}>
          {/* Live System Clock */}
          <div style={styles.clockBox}>
            <Clock size={13} color="#8E857B" />
            <span style={styles.clockText}>{currentTime || "12:04:02 GMT+5:30"}</span>
          </div>

          {/* Notification Quick Bell */}
          <button
            onClick={() => navigate("/notifications")}
            style={styles.bellBtn}
            title="Notifications"
          >
            <Bell size={15} color="#57534E" />
            {unreadCount > 0 && <span style={styles.bellBadge}>{unreadCount}</span>}
          </button>

          {/* Action Button */}
          <button onClick={handleActionClick} className="btn-primary" style={{ padding: "6px 14px", height: "32px" }}>
            <Plus size={14} />
            <span>{isExpert ? "Upload Observation" : "Add Heritage Site"}</span>
          </button>
        </div>
      </div>
    </header>
  );
}

const styles = {
  headerContainer: {
    position: "sticky",
    top: 0,
    zIndex: 30,
    backgroundColor: "var(--bg-header)",
    borderBottom: "1px solid var(--border-color)"
  },
  headerMain: {
    height: "var(--header-height)",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 20px"
  },
  focusSelectorGroup: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    backgroundColor: "#FFFFFF",
    padding: "4px 10px",
    border: "1px solid var(--border-color)",
    borderRadius: "6px"
  },
  focusLabel: {
    fontSize: "10px",
    fontFamily: "var(--font-sans)",
    fontWeight: "700",
    letterSpacing: "0.08em",
    color: "#8E857B"
  },
  focusSelect: {
    border: "none",
    background: "none",
    fontFamily: "var(--font-serif)",
    fontWeight: "700",
    fontSize: "12px",
    color: "var(--text-primary)",
    cursor: "pointer",
    outline: "none"
  },
  headerRightGroup: {
    display: "flex",
    alignItems: "center",
    gap: "14px"
  },
  clockBox: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    backgroundColor: "#FFFFFF",
    padding: "5px 10px",
    border: "1px solid var(--border-color)",
    borderRadius: "6px"
  },
  clockText: {
    fontFamily: "var(--font-mono)",
    fontSize: "11px",
    color: "#57534E"
  },
  bellBtn: {
    position: "relative",
    background: "#FFFFFF",
    border: "1px solid var(--border-color)",
    borderRadius: "6px",
    width: "32px",
    height: "32px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer"
  },
  bellBadge: {
    position: "absolute",
    top: "-3px",
    right: "-3px",
    backgroundColor: "var(--accent-primary)",
    color: "#FFFFFF",
    fontSize: "9px",
    fontWeight: "700",
    borderRadius: "8px",
    padding: "1px 4px"
  }
};
