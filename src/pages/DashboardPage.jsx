import React from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { StatCard } from "../components/common/StatCard";
import { StatusBadge } from "../components/common/StatusBadge";
import { Landmark, Scan, Binary, ShieldAlert, ArrowRight, Camera, Plus, CheckCircle2, Clock } from "lucide-react";

export function DashboardPage() {
  const navigate = useNavigate();
  const { heritageSites, assessments, notifications, currentUser, setActiveSiteId } = useApp();
  const isExpert = currentUser.role === "CONSERVATION_EXPERT";

  const criticalCount = assessments.filter((a) => a.emergencyLevel === "Critical" || a.severity === "High").length;
  const pendingCount = assessments.filter((a) => a.status === "Pending Review").length;

  const handleInspectSite = (siteId) => {
    setActiveSiteId(siteId);
    if (isExpert) {
      navigate("/expert/image-analysis");
    } else {
      navigate("/admin/architectural-regions");
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Top Banner Header Section */}
      <div style={styles.topHeaderRow}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <span className="module-badge">MOD-01</span>
            <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: 0 }}>
              HERITAGE STRUCTURAL INTELLIGENCE OVERVIEW
            </h1>
          </div>
          <p style={styles.headerDescription}>
            Autonomous heritage monitoring orchestration: <span style={{ color: "#3B6978" }}>cross-temporal perceptual consensus</span>,{" "}
            <span style={{ color: "#3B6978" }}>lithic deterioration detection</span>, and conservation planning.
          </p>
        </div>

        <div>
          <button
            onClick={() => navigate(isExpert ? "/expert/image-analysis" : "/admin/heritage-sites")}
            className="btn-primary"
            style={{ padding: "9px 16px" }}
          >
            <Plus size={15} />
            <span>{isExpert ? "Intake New Observation" : "Add Heritage Site"}</span>
          </button>
        </div>
      </div>

      {/* Top 4 Metrics Cards Grid */}
      <div style={styles.metricsGrid}>
        <StatCard
          label="MONITORED ASSETS"
          value={heritageSites.length}
          subtitle={`${heritageSites.length} ASI Circles Active`}
          icon={Landmark}
          iconBg="#F7EDE9"
          iconColor="#A04022"
        />
        <StatCard
          label="TOTAL OBSERVATIONS"
          value="670"
          subtitle={<span style={{ color: "#16A34A" }}>{pendingCount} pending consensus</span>}
          icon={Scan}
          iconBg="#DCFCE7"
          iconColor="#16A34A"
        />
        <StatCard
          label="CONSENSUS MEMORY"
          value="94.2%"
          subtitle="Mean agreement index"
          icon={Binary}
          iconBg="#EFF6FF"
          iconColor="#2563EB"
        />
        <StatCard
          label="INTERVENTIONS"
          value={criticalCount}
          subtitle={<span style={{ color: "#D97706" }}>1 urgent desalination</span>}
          icon={ShieldAlert}
          iconBg="#FEF3C7"
          iconColor="#D97706"
        />
      </div>

      {/* Section 1: Monitored Heritage Sites Grid */}
      <div>
        <div style={styles.sectionTitleRow}>
          <h2 className="font-serif-heading" style={styles.sectionTitle}>
            MONITORED HERITAGE SITES
          </h2>
          <button
            onClick={() => navigate(isExpert ? "/expert/damage-history" : "/admin/heritage-sites")}
            style={styles.linkBtn}
          >
            <span>View All Monuments</span>
            <ArrowRight size={14} />
          </button>
        </div>

        <div style={styles.sitesGrid}>
          {heritageSites.map((site) => (
            <div key={site.id} className="ancestra-card" style={styles.siteCard}>
              {/* Image Banner */}
              <div style={styles.cardImageWrapper}>
                <img src={site.image} alt={site.name} style={styles.cardImage} />
                <div style={styles.cardOverlayTop}>
                  <span style={styles.dynastyBadge}>{site.period}</span>
                  <span style={styles.scoreBadge}>SCORE: {site.healthScore}/100</span>
                </div>
              </div>

              {/* Card Body */}
              <div style={styles.cardBody}>
                <h3 className="font-serif-heading" style={styles.siteName}>
                  {site.name.toUpperCase()}
                </h3>
                <div style={styles.siteSubMeta}>
                  {site.location} • {site.period}
                </div>
                <p style={styles.siteDesc}>{site.description}</p>
              </div>

              {/* Card Footer */}
              <div style={styles.cardFooter}>
                <span style={styles.footerRegionsText}>{site.regionsCount} Architectural Regions</span>
                <button onClick={() => handleInspectSite(site.id)} style={styles.inspectBtn}>
                  <span>Inspect</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 2: Recent AI Observations & Alerts */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "20px" }}>
        {/* Recent Assessments Table */}
        <div className="ancestra-card">
          <div style={styles.cardHeaderRow}>
            <h3 className="font-serif-heading" style={{ fontSize: "15px", margin: 0 }}>
              RECENT AI STRUCTURAL ASSESSMENTS
            </h3>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
              LIVE FEED
            </span>
          </div>
          <div style={styles.recentList}>
            {assessments.slice(0, 3).map((asm) => (
              <div key={asm.id} style={styles.recentRow}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                    <span style={styles.asmCode}>{asm.id}</span>
                    <StatusBadge status={asm.severity} size="sm" />
                    <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{asm.date}</span>
                  </div>
                  <div style={{ fontWeight: 600, fontSize: "13px" }}>{asm.siteName}</div>
                  <div style={{ fontSize: "11px", color: "var(--text-secondary)" }}>
                    Region: {asm.regionName} • Finding: <strong>{asm.damageType}</strong>
                  </div>
                </div>
                <button
                  onClick={() => navigate("/expert/results")}
                  className="btn-secondary"
                  style={{ padding: "5px 10px", fontSize: "11px" }}
                >
                  Review Result
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Notifications Quick Panel */}
        <div className="ancestra-card">
          <div style={styles.cardHeaderRow}>
            <h3 className="font-serif-heading" style={{ fontSize: "15px", margin: 0 }}>
              SYSTEM NOTIFICATIONS
            </h3>
            <span className="version-pill">{notifications.length} ALERTS</span>
          </div>
          <div style={styles.notifList}>
            {notifications.slice(0, 4).map((n) => (
              <div key={n.id} style={styles.notifItem}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={styles.notifTitle}>{n.title}</span>
                  <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>{n.time}</span>
                </div>
                <div style={styles.notifDesc}>{n.description}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  topHeaderRow: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between"
  },
  headerDescription: {
    fontSize: "13px",
    color: "#57534E",
    maxWidth: "800px"
  },
  metricsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: "16px"
  },
  sectionTitleRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "14px"
  },
  sectionTitle: {
    fontSize: "16px",
    letterSpacing: "0.04em",
    margin: 0
  },
  linkBtn: {
    background: "none",
    border: "none",
    fontSize: "12px",
    fontFamily: "var(--font-sans)",
    fontWeight: "600",
    color: "var(--accent-primary)",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "4px"
  },
  sitesGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "18px"
  },
  siteCard: {
    padding: 0,
    overflow: "hidden",
    display: "flex",
    flexDirection: "column"
  },
  cardImageWrapper: {
    position: "relative",
    height: "170px",
    width: "100%",
    backgroundColor: "#E2DDD5"
  },
  cardImage: {
    width: "100%",
    height: "100%",
    objectFit: "cover"
  },
  cardOverlayTop: {
    position: "absolute",
    top: "10px",
    left: "10px",
    right: "10px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between"
  },
  dynastyBadge: {
    backgroundColor: "rgba(28, 25, 23, 0.8)",
    color: "#FFFFFF",
    fontSize: "10px",
    fontFamily: "var(--font-sans)",
    padding: "3px 8px",
    borderRadius: "3px"
  },
  scoreBadge: {
    backgroundColor: "rgba(255, 255, 255, 0.9)",
    color: "var(--text-primary)",
    fontSize: "10px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    padding: "3px 8px",
    borderRadius: "3px",
    border: "1px solid var(--border-color)"
  },
  cardBody: {
    padding: "16px",
    flex: 1
  },
  siteName: {
    fontSize: "15px",
    margin: 0,
    lineHeight: "1.3"
  },
  siteSubMeta: {
    fontSize: "11px",
    color: "var(--text-muted)",
    marginTop: "4px",
    marginBottom: "8px"
  },
  siteDesc: {
    fontSize: "12px",
    color: "var(--text-secondary)",
    display: "-webkit-box",
    WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
    overflow: "hidden"
  },
  cardFooter: {
    padding: "12px 16px",
    borderTop: "1px solid var(--border-light)",
    backgroundColor: "#FAF8F5",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between"
  },
  footerRegionsText: {
    fontSize: "11px",
    color: "var(--text-muted)",
    fontFamily: "var(--font-mono)"
  },
  inspectBtn: {
    background: "none",
    border: "none",
    fontSize: "12px",
    fontWeight: "600",
    color: "var(--accent-primary)",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "4px"
  },
  cardHeaderRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    paddingBottom: "12px",
    borderBottom: "1px solid var(--border-light)",
    marginBottom: "12px"
  },
  recentList: {
    display: "flex",
    flexDirection: "column",
    gap: "10px"
  },
  recentRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "10px",
    backgroundColor: "#FAF8F5",
    border: "1px solid var(--border-light)",
    borderRadius: "4px"
  },
  asmCode: {
    fontFamily: "var(--font-mono)",
    fontSize: "10.5px",
    fontWeight: "700",
    color: "var(--accent-primary)"
  },
  notifList: {
    display: "flex",
    flexDirection: "column",
    gap: "10px"
  },
  notifItem: {
    padding: "8px 10px",
    borderBottom: "1px solid var(--border-light)"
  },
  notifTitle: {
    fontSize: "11px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    color: "var(--text-primary)"
  },
  notifDesc: {
    fontSize: "11.5px",
    color: "var(--text-secondary)",
    marginTop: "2px"
  }
};
