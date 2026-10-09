import React from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { StatCard } from "../components/common/StatCard";
import { StatusBadge } from "../components/common/StatusBadge";
import { Landmark, Scan, Activity, ArrowRight, Cpu, Play } from "lucide-react";

export function DashboardPage() {
  const navigate = useNavigate();
  const {
    heritageSites,
    architecturalRegions = [],
    assessments,
    notifications,
    currentUser,
    setActiveSiteId,
    pipelineStep,
    isPipelineComplete
  } = useApp();
  const isExpert = currentUser?.role === "CONSERVATION_EXPERT";

  // Derive latest recent activity dynamically from actual application state
  const latestNotif = notifications[0];
  const latestAssessment = assessments[0];
  
  const recentActivityTitle = isPipelineComplete
    ? (latestAssessment?.damageType
        ? `${latestAssessment.damageType.toUpperCase()} ASSESSMENT`
        : "AI DAMAGE ASSESSMENT")
    : `AI PIPELINE STEP 0${pipelineStep}/09 IN PROGRESS`;

  const recentActivityTime = latestNotif?.time || "JUST NOW";

  const pipelineStepNames = [
    "Photometric Calibration",
    "Spatial Polygon Anchoring",
    "Contrast & Noise Normalization",
    "Lithic Texture Extraction",
    "Crack Segmentation Masking",
    "Salt Efflorescence Estimation",
    "Severity & Risk Scoring",
    "Temporal Consensus Matrix",
    "Conservation Recommendation"
  ];

  const currentStepName = pipelineStepNames[pipelineStep - 1] || "Neural Processing";

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
      {/* Top Header Section */}
      <div style={styles.topHeaderRow}>
        <div>
          <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: "0 0 6px 0" }}>
            HERITAGE STRUCTURAL INTELLIGENCE OVERVIEW
          </h1>
          <p style={styles.headerDescription}>
            Autonomous heritage monitoring orchestration: <span style={{ color: "#3B6978" }}>cross-temporal perceptual consensus</span>,{" "}
            <span style={{ color: "#3B6978" }}>lithic deterioration detection</span>, and conservation planning.
          </p>
        </div>
      </div>

      {/* Top 3 Summary Cards Grid (All 3 Cards strictly STATIC, 3-Column Layout) */}
      <div style={styles.metricsGrid}>
        {/* Card 1: MONITORED SITES (Static) */}
        <StatCard
          label="MONITORED SITES"
          value={heritageSites.length}
          icon={Landmark}
          iconBg="#F7EDE9"
          iconColor="#A04022"
        />

        {/* Card 2: ARCHITECTURAL REGIONS (Real backend count) */}
        <StatCard
          label="ARCHITECTURAL REGIONS"
          value={architecturalRegions.length}
          icon={Scan}
          iconBg="#DCFCE7"
          iconColor="#16A34A"
        />

        {/* Card 3: LAST RECENT ACTIVITY (Static Information Card) */}
        <StatCard
          label="LAST RECENT ACTIVITY"
          value={
            <div style={{ fontSize: "13.5px", fontFamily: "var(--font-mono)", fontWeight: 700, color: "#1C1917", lineHeight: "1.3" }}>
              {recentActivityTitle}
            </div>
          }
          subtitle={
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "10.5px", color: "var(--accent-primary)", fontWeight: 700 }}>
              {recentActivityTime.toUpperCase()}
            </span>
          }
          icon={Activity}
          iconBg="#EFF6FF"
          iconColor="#2563EB"
        />
      </div>

      {/* Monitored Heritage Sites Cards Grid */}
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

        {/* Heritage Site Cards */}
        <div style={styles.sitesGrid}>
          {heritageSites.map((site) => (
            <div key={site.id} className="ancestra-card" style={styles.siteCard}>
              <div
                onClick={() => handleInspectSite(site.id)}
                style={styles.clickableImageWrapper}
                title={`Inspect ${site.name}`}
              >
                <img src={site.image} alt={site.name} style={styles.cleanImage} />
              </div>

              <div style={styles.cardFooter}>
                <h3 className="font-serif-heading" style={styles.siteName}>
                  {site.name.toUpperCase()}
                </h3>
                <button onClick={() => handleInspectSite(site.id)} style={styles.inspectBtn}>
                  <span>INSPECT</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent AI Observations & System Notifications */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "20px" }}>
        
        {/* Change 2: RECENT AI STRUCTURAL ASSESSMENTS Section (Only shows results after pipeline completion; shows live pipeline step when incomplete) */}
        <div className="ancestra-card">
          <div style={styles.cardHeaderRow}>
            <h3 className="font-serif-heading" style={{ fontSize: "15px", margin: 0 }}>
              RECENT AI STRUCTURAL ASSESSMENTS
            </h3>
            <span style={{ fontSize: "11px", color: isPipelineComplete ? "#16A34A" : "var(--accent-primary)", fontFamily: "var(--font-mono)", fontWeight: 700 }}>
              {isPipelineComplete ? "RESULTS PUBLISHED" : "PIPELINE ACTIVE"}
            </span>
          </div>

          {isPipelineComplete ? (
            /* Display actual published AI Structural Assessment Results */
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
          ) : (
            /* Display Live AI Perception Pipeline Activity Status (No Fake Results) */
            <div style={styles.pipelineProgressBox}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                <Cpu size={20} color="#A04022" />
                <div>
                  <div style={{ fontSize: "12px", fontFamily: "var(--font-mono)", fontWeight: 700, color: "#A04022" }}>
                    AI PERCEPTION PIPELINE — STEP 0{pipelineStep} OF 09
                  </div>
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "#1C1917" }}>
                    {currentStepName.toUpperCase()} — IN PROGRESS
                  </div>
                </div>
              </div>
              <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: "0 0 12px 0" }}>
                Complete all 9 AI perception pipeline steps to publish the official computer vision structural damage assessment findings.
              </p>
              <button
                onClick={() => navigate("/expert/ai-analysis")}
                className="btn-primary"
                style={{ padding: "6px 14px", fontSize: "11.5px" }}
              >
                <Play size={12} />
                <span>Go to AI Perception Pipeline ({pipelineStep}/9)</span>
              </button>
            </div>
          )}
        </div>

        {/* Change 1: FULLY CLICKABLE SYSTEM NOTIFICATIONS CARD (Navigates to /notifications) */}
        <div
          onClick={() => navigate("/notifications")}
          className="ancestra-card"
          style={{ ...styles.clickableNotifCard, cursor: "pointer" }}
          title="Click to view System Notifications & Conservation Alerts"
        >
          <div style={styles.cardHeaderRow}>
            <h3 className="font-serif-heading" style={{ fontSize: "15px", margin: 0 }}>
              SYSTEM NOTIFICATIONS
            </h3>
            <span style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--accent-primary)", fontWeight: 700 }}>
              {notifications.filter((n) => !n.read).length} UNREAD
            </span>
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
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "18px"
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
  clickableImageWrapper: {
    position: "relative",
    height: "200px",
    width: "100%",
    backgroundColor: "#1C1917",
    cursor: "pointer",
    overflow: "hidden"
  },
  cleanImage: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    transition: "transform 0.2s ease"
  },
  cardFooter: {
    padding: "16px",
    backgroundColor: "#FFFFFF",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "12px"
  },
  siteName: {
    fontSize: "13px",
    margin: 0,
    lineHeight: "1.35",
    flex: 1,
    paddingRight: "8px",
    wordBreak: "break-word"
  },
  inspectBtn: {
    background: "none",
    border: "none",
    fontSize: "12px",
    fontWeight: "700",
    color: "var(--accent-primary)",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "4px",
    letterSpacing: "0.04em",
    flexShrink: 0
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
  pipelineProgressBox: {
    padding: "14px",
    backgroundColor: "#FAF8F5",
    border: "1px solid var(--border-light)",
    borderRadius: "4px"
  },
  clickableNotifCard: {
    transition: "transform 0.12s ease, border-color 0.12s ease"
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
