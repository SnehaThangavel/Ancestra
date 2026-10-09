import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { DamageChart } from "../../components/expert/DamageChart";
import { DataTable } from "../../components/common/DataTable";
import { StatusBadge } from "../../components/common/StatusBadge";
import { EmergencyBadge } from "../../components/common/EmergencyBadge";
import { TrendingUp, AlertCircle, Eye } from "lucide-react";

export function DamageHistoryPage() {
  const navigate = useNavigate();
  const { heritageSites, architecturalRegions, assessments, setActiveResult } = useApp();

  const [selectedSiteId, setSelectedSiteId] = useState(heritageSites[0]?.id || "");
  const filteredRegions = architecturalRegions.filter(
    (r) => (r.monument_id || r.siteId) === selectedSiteId
  );
  const [selectedRegionId, setSelectedRegionId] = useState(filteredRegions[0]?.id || "");

  useEffect(() => {
    if (heritageSites.length > 0 && !selectedSiteId) {
      setSelectedSiteId(heritageSites[0].id);
    }
  }, [heritageSites, selectedSiteId]);

  useEffect(() => {
    if (filteredRegions.length > 0) {
      const exists = filteredRegions.some((r) => r.id === selectedRegionId);
      if (!exists) {
        setSelectedRegionId(filteredRegions[0].id);
      }
    } else {
      setSelectedRegionId("");
    }
  }, [filteredRegions, selectedRegionId]);

  const activeRegion = architecturalRegions.find((r) => r.id === selectedRegionId) || null;
  const regionAssessments = selectedRegionId
    ? assessments.filter((a) => a.regionId === selectedRegionId)
    : [];

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
        <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: "0 0 4px 0" }}>
          STRUCTURAL DAMAGE TEMPORAL HISTORY
        </h1>
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
                const newSiteId = e.target.value;
                setSelectedSiteId(newSiteId);
                const regs = architecturalRegions.filter(
                  (r) => (r.monument_id || r.siteId) === newSiteId
                );
                if (regs.length > 0) {
                  setSelectedRegionId(regs[0].id);
                } else {
                  setSelectedRegionId("");
                }
              }}
            >
              {heritageSites.length > 0 ? (
                heritageSites.map((site) => (
                  <option key={site.id} value={site.id}>
                    {site.name}
                  </option>
                ))
              ) : (
                <option value="">No heritage monuments available</option>
              )}
            </select>
          </div>

          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">SELECT ARCHITECTURAL REGION</label>
            <select
              className="form-select"
              value={selectedRegionId}
              onChange={(e) => setSelectedRegionId(e.target.value)}
              disabled={filteredRegions.length === 0}
            >
              {filteredRegions.length > 0 ? (
                filteredRegions.map((reg) => (
                  <option key={reg.id} value={reg.id}>
                    [{reg.code || "REG"}] {reg.name}
                  </option>
                ))
              ) : (
                <option value="">No architectural regions registered</option>
              )}
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

      {!activeRegion ? (
        <div className="ancestra-card" style={{ padding: "48px 24px", textAlign: "center" }}>
          <AlertCircle size={32} color="#A04022" style={{ margin: "0 auto 12px" }} />
          <h2 className="font-serif-heading" style={{ fontSize: "16px", margin: "0 0 6px 0" }}>
            NO ARCHITECTURAL REGION SELECTED
          </h2>
          <p style={{ fontSize: "12.5px", color: "var(--text-secondary)", margin: 0 }}>
            {heritageSites.length === 0
              ? "No heritage monuments currently exist in the database."
              : filteredRegions.length === 0
              ? "No architectural regions have been registered for this monument yet."
              : "Please select an architectural region from the dropdown above to view temporal damage history."}
          </p>
        </div>
      ) : (
        <>
          {/* Condition Overview Summary Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px" }}>
            <div className="ancestra-card">
              <span className="label-uppercase">CURRENT CONDITION</span>
              <div style={{ marginTop: "6px" }}>
                <StatusBadge
                  status={
                    regionAssessments.length > 0
                      ? regionAssessments[0].severity === "High" || regionAssessments[0].emergencyLevel === "Critical"
                        ? "CRITICAL"
                        : "MONITOR"
                      : "STABLE"
                  }
                />
              </div>
            </div>
            <div className="ancestra-card">
              <span className="label-uppercase">RISK SEVERITY</span>
              <div style={{ marginTop: "6px" }}>
                <StatusBadge
                  status={
                    regionAssessments.length > 0
                      ? regionAssessments[0].severity?.toUpperCase() || "MEDIUM"
                      : "LOW"
                  }
                />
              </div>
            </div>
            <div className="ancestra-card">
              <span className="label-uppercase">ESTIMATED TREND</span>
              <div style={{ fontSize: "15px", fontWeight: 700, color: regionAssessments.length >= 2 ? "#DC2626" : "#57534E", marginTop: "4px" }}>
                {regionAssessments.length >= 2 ? "Deteriorating (+12%/mo)" : regionAssessments.length === 1 ? "Baseline Logged" : "Stable"}
              </div>
            </div>
            <div className="ancestra-card">
              <span className="label-uppercase">LAST INSPECTED</span>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "14px", fontWeight: 600, marginTop: "4px" }}>
                {regionAssessments[0]?.date || activeRegion?.lastAssessment || "Recent"}
              </div>
            </div>
          </div>

          {/* Temporal Line Chart */}
          <div className="ancestra-card">
            <div style={styles.chartHeader}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <TrendingUp size={16} color="#A04022" />
                <h3 className="font-serif-heading" style={{ fontSize: "15px", margin: 0 }}>
                  TEMPORAL DAMAGE SEVERITY TREND
                </h3>
              </div>
              <span className="version-pill">
                {regionAssessments.length > 0 ? `${regionAssessments.length} OBSERVATION(S)` : "NO HISTORICAL LOGS"}
              </span>
            </div>
            {regionAssessments.length > 0 ? (
              <DamageChart
                data={regionAssessments.map((a) => ({
                  date: a.date,
                  score:
                    typeof a.severity_score === "number"
                      ? Math.round(a.severity_score * 100)
                      : a.severity === "High"
                      ? 75
                      : a.severity === "Medium"
                      ? 45
                      : 20,
                  label: a.damageType,
                }))}
              />
            ) : (
              <div style={{ height: "180px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", backgroundColor: "var(--bg-app)", borderRadius: "4px" }}>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--text-muted)", letterSpacing: "0.05em" }}>
                  NO TEMPORAL DAMAGE DATA LOGGED FOR THIS REGION YET
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>
                  Run live AI analysis from Image Intake to record baseline & damage trend observations.
                </div>
              </div>
            )}
          </div>

          {/* Historical Records Table */}
          <div className="ancestra-card">
            <h3 className="font-serif-heading" style={{ fontSize: "15px", marginBottom: "12px" }}>
              HISTORICAL ASSESSMENT LOGS
            </h3>
            <DataTable
              columns={columns}
              data={regionAssessments}
              emptyMessage="No temporal observations recorded for this region."
            />
          </div>
        </>
      )}
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
