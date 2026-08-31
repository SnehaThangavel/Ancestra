import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { DamageChart } from "../../components/expert/DamageChart";
import { DataTable } from "../../components/common/DataTable";
import { StatusBadge } from "../../components/common/StatusBadge";
import { EmergencyBadge } from "../../components/common/EmergencyBadge";
import { TrendingUp, AlertCircle, Calendar, Eye } from "lucide-react";

export function DamageHistoryPage() {
  const navigate = useNavigate();
  const { heritageSites, architecturalRegions, assessments, setActiveResult } = useApp();

  const [selectedSiteId, setSelectedSiteId] = useState(heritageSites[0]?.id || "site_01");
  const filteredRegions = architecturalRegions.filter((r) => r.siteId === selectedSiteId);
  const [selectedRegionId, setSelectedRegionId] = useState(filteredRegions[0]?.id || "reg_01");

  const activeRegion = architecturalRegions.find((r) => r.id === selectedRegionId) || filteredRegions[0];
  const regionAssessments = assessments.filter((a) => a.regionId === selectedRegionId);

  const columns = [
    {
      header: "DATE",
      accessor: "date",
      render: (row) => <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{row.date}</span>
    },
    {
      header: "DAMAGE TYPE",
      accessor: "damageType",
      render: (row) => <strong>{row.damageType}</strong>
    },
    {
      header: "SEVERITY",
      accessor: "severity",
      render: (row) => <StatusBadge status={row.severity} size="sm" />
    },
    {
      header: "AI CONFIDENCE",
      accessor: "confidence",
      render: (row) => (
        <span style={{ fontFamily: "var(--font-mono)" }}>
          {typeof row.confidence === "number" ? `${(row.confidence * 100).toFixed(0)}%` : row.confidence}
        </span>
      )
    },
    {
      header: "EMERGENCY",
      accessor: "emergencyLevel",
      render: (row) => <EmergencyBadge level={row.emergencyLevel} />
    },
    {
      header: "STATUS",
      accessor: "status",
      render: (row) => <StatusBadge status={row.status} size="sm" />
    },
    {
      header: "ACTION",
      align: "right",
      render: (row) => (
        <button
          onClick={() => {
            setActiveResult(row);
            navigate("/expert/results");
          }}
          className="btn-secondary"
          style={{ padding: "4px 8px", fontSize: "11px" }}
        >
          <Eye size={12} />
          <span>View</span>
        </button>
      )
    }
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header */}
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
          <span className="module-badge">HIS-06</span>
          <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: 0 }}>
            STRUCTURAL DAMAGE TEMPORAL HISTORY
          </h1>
        </div>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
          Cross-temporal degradation metrics and predictive deterioration trends for architectural regions.
        </p>
      </div>

      {/* Selectors Bar */}
      <div className="ancestra-card" style={styles.selectorCard}>
        <div style={{ display: "flex", alignItems: "center", gap: "16px", flex: 1 }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">SELECT HERITAGE MONUMENT</label>
            <select
              className="form-select"
              value={selectedSiteId}
              onChange={(e) => {
                setSelectedSiteId(e.target.value);
                const regs = architecturalRegions.filter((r) => r.siteId === e.target.value);
                if (regs.length > 0) setSelectedRegionId(regs[0].id);
              }}
            >
              {heritageSites.map((site) => (
                <option key={site.id} value={site.id}>
                  {site.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">SELECT ARCHITECTURAL REGION</label>
            <select
              className="form-select"
              value={selectedRegionId}
              onChange={(e) => setSelectedRegionId(e.target.value)}
            >
              {filteredRegions.map((reg) => (
                <option key={reg.id} value={reg.id}>
                  [{reg.code}] {reg.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Mandatory Technical Disclaimer Banner */}
      <div style={styles.disclaimerBanner}>
        <AlertCircle size={15} color="#A04022" style={{ flexShrink: 0 }} />
        <span>
          <strong>TEMPORAL METHODOLOGY NOTICE:</strong> DAMAGE TREND IS ESTIMATED FROM AVAILABLE HISTORICAL ASSESSMENTS OF THE SAME ARCHITECTURAL REGION.
        </span>
      </div>

      {/* Condition Overview Summary Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px" }}>
        <div className="ancestra-card">
          <span className="label-uppercase">CURRENT CONDITION</span>
          <div style={{ marginTop: "6px" }}>
            <StatusBadge status={activeRegion?.condition || "MONITOR"} />
          </div>
        </div>
        <div className="ancestra-card">
          <span className="label-uppercase">RISK SEVERITY</span>
          <div style={{ marginTop: "6px" }}>
            <StatusBadge status={activeRegion?.riskLevel || "MEDIUM"} />
          </div>
        </div>
        <div className="ancestra-card">
          <span className="label-uppercase">ESTIMATED TREND</span>
          <div style={{ fontSize: "16px", fontWeight: 700, color: "#DC2626", marginTop: "4px" }}>
            Increasing (+14%)
          </div>
        </div>
        <div className="ancestra-card">
          <span className="label-uppercase">LAST INSPECTED</span>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "14px", fontWeight: 600, marginTop: "4px" }}>
            {activeRegion?.lastAssessment || "2026-08-26"}
          </div>
        </div>
      </div>

      {/* Temporal Line Chart */}
      <div className="ancestra-card">
        <div style={styles.chartHeader}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <TrendingUp size={16} color="#A04022" />
            <h3 className="font-serif-heading" style={{ fontSize: "15px", margin: 0 }}>
              TEMPORAL DAMAGE SEVERITY TREND (JAN 2026 – AUG 2026)
            </h3>
          </div>
          <span className="version-pill">METRIC: STRESS INDEX</span>
        </div>
        <DamageChart />
      </div>

      {/* Historical Records Table */}
      <div className="ancestra-card">
        <h3 className="font-serif-heading" style={{ fontSize: "15px", marginBottom: "12px" }}>
          HISTORICAL ASSESSMENT LOGS
        </h3>
        <DataTable
          columns={columns}
          data={regionAssessments.length > 0 ? regionAssessments : assessments}
          emptyMessage="No temporal observations recorded for this region."
        />
      </div>
    </div>
  );
}

const styles = {
  selectorCard: {
    padding: "14px 18px"
  },
  disclaimerBanner: {
    backgroundColor: "#F7EDE9",
    border: "1px solid rgba(160, 64, 34, 0.25)",
    borderRadius: "6px",
    padding: "10px 14px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    fontSize: "11px",
    fontFamily: "var(--font-mono)",
    color: "#883419"
  },
  chartHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "16px",
    paddingBottom: "10px",
    borderBottom: "1px solid var(--border-light)"
  }
};
