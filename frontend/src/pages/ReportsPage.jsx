import React, { useState } from "react";
import { useApp } from "../context/AppContext";
import { DataTable } from "../components/common/DataTable";
import { StatusBadge } from "../components/common/StatusBadge";
import { EmergencyBadge } from "../components/common/EmergencyBadge";
import { Modal } from "../components/common/Modal";
import { generateAncestrapdfReport } from "../utils/pdfGenerator";
import { Search, Eye, FileDown } from "lucide-react";

export function ReportsPage() {
  const { reports, heritageSites, architecturalRegions, assessments, showToast } = useApp();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedReport, setSelectedReport] = useState(null);
  const [isExporting, setIsExporting] = useState(false);

  const filteredReports = reports.filter(
    (r) =>
      r.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.siteName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.regionName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.damageType.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleExportPdf = async (report) => {
    try {
      setIsExporting(true);
      showToast(`Generating ANCESTRA PDF report for ${report.id}...`);

      const siteData = heritageSites.find((s) => s.name === report.siteName);
      const regionData = architecturalRegions.find((r) => r.name === report.regionName);
      const assessmentData = assessments.find((a) => a.id === report.assessmentId) || assessments[0];

      await generateAncestrapdfReport(report, siteData, regionData, assessmentData);
      showToast(`PDF Dossier ${report.id} exported successfully!`);
    } catch (err) {
      console.error(err);
      showToast("Failed to generate PDF.", "error");
    } finally {
      setIsExporting(false);
    }
  };

  const columns = [
    {
      header: "REPORT ID",
      accessor: "id",
      render: (row) => <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--accent-primary)" }}>{row.id}</span>
    },
    {
      header: "HERITAGE SITE",
      accessor: "siteName",
      render: (row) => <strong>{row.siteName}</strong>
    },
    {
      header: "REGION",
      accessor: "regionName"
    },
    {
      header: "DATE",
      accessor: "date",
      render: (row) => <span style={{ fontFamily: "var(--font-mono)" }}>{row.date}</span>
    },
    {
      header: "DAMAGE FINDING",
      accessor: "damageType"
    },
    {
      header: "SEVERITY",
      accessor: "severity",
      render: (row) => <StatusBadge status={row.severity} size="sm" />
    },
    {
      header: "EMERGENCY",
      accessor: "emergencyLevel",
      render: (row) => <EmergencyBadge level={row.emergencyLevel} />
    },
    {
      header: "EXPERT",
      accessor: "expertName"
    },
    {
      header: "ACTIONS",
      align: "right",
      render: (row) => (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "6px" }}>
          <button
            onClick={() => setSelectedReport(row)}
            className="btn-secondary"
            style={{ padding: "4px 8px", fontSize: "11px" }}
          >
            <Eye size={12} />
            <span>View</span>
          </button>

          <button
            onClick={() => handleExportPdf(row)}
            className="btn-primary"
            style={{ padding: "4px 10px", fontSize: "11px" }}
            disabled={isExporting}
          >
            <FileDown size={12} />
            <span>EXPORT AS PDF</span>
          </button>
        </div>
      )
    }
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: "0 0 4px 0" }}>
            CONSERVATION REPORTS & EXECUTIVE DOSSIERS
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            Formal structural assessment dossiers compiled for ASI Directorate and ICOMOS submission.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="ancestra-card" style={styles.filterCard}>
        <div style={styles.searchGroup}>
          <Search size={15} color="#8E857B" />
          <input
            type="text"
            className="form-input"
            style={{ border: "none", background: "none" }}
            placeholder="Search reports by ID, site, region, or damage finding..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Reports Table */}
      <DataTable columns={columns} data={filteredReports} emptyMessage="No conservation reports compiled yet." />

      {/* Report View Modal */}
      {selectedReport && (
        <Modal
          isOpen={Boolean(selectedReport)}
          onClose={() => setSelectedReport(null)}
          title={`EXECUTIVE CONSERVATION DOSSIER: ${selectedReport.id}`}
          width="620px"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={styles.modalMetaGrid}>
              <div>
                <span className="label-uppercase">HERITAGE MONUMENT</span>
                <div style={{ fontWeight: 600 }}>{selectedReport.siteName}</div>
              </div>
              <div>
                <span className="label-uppercase">ARCHITECTURAL REGION</span>
                <div style={{ fontWeight: 600 }}>{selectedReport.regionName}</div>
              </div>
              <div>
                <span className="label-uppercase">REPORT DATE</span>
                <div style={{ fontFamily: "var(--font-mono)" }}>{selectedReport.date}</div>
              </div>
              <div>
                <span className="label-uppercase">AUTHORING CONSERVATOR</span>
                <div>{selectedReport.expertName}</div>
              </div>
            </div>

            {/* Photographic Asset Preview with AI Bounding Box Overlay */}
            <div style={{ backgroundColor: "#1C1917", borderRadius: "6px", padding: "8px", textAlign: "center" }}>
              <div style={{ position: "relative", display: "inline-block", maxWidth: "100%" }}>
                <img
                  src={
                    (assessments.find((a) => a.id === selectedReport.assessmentId)?.imageUrl) ||
                    (heritageSites.find((s) => s.name === selectedReport.siteName)?.image) ||
                    "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
                  }
                  alt="Assessed Asset"
                  style={{ maxHeight: "200px", maxWidth: "100%", borderRadius: "4px", display: "block" }}
                />
                {/* Zone 1: Structural Delamination (Purple) */}
                <div
                  style={{
                    position: "absolute",
                    top: "5%",
                    left: "11%",
                    width: "5%",
                    height: "8%",
                    border: "2px dashed #8B5CF6",
                    backgroundColor: "rgba(139, 92, 246, 0.22)",
                    borderRadius: "3px",
                    pointerEvents: "none",
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      top: "-18px",
                      left: "0",
                      backgroundColor: "#8B5CF6",
                      color: "#FFF",
                      fontSize: "8px",
                      fontFamily: "var(--font-mono)",
                      fontWeight: "700",
                      padding: "1px 4px",
                      borderRadius: "2px",
                      whiteSpace: "nowrap",
                    }}
                  >
                    STRUCTURAL DELAMINATION (35%)
                  </div>
                </div>

                {/* Zone 2: Secondary Stress Fracture (Amber) */}
                <div
                  style={{
                    position: "absolute",
                    top: "5%",
                    left: "51%",
                    width: "20%",
                    height: "13%",
                    border: "2px dashed #D97706",
                    backgroundColor: "rgba(217, 119, 6, 0.22)",
                    borderRadius: "3px",
                    pointerEvents: "none",
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      top: "-18px",
                      left: "0",
                      backgroundColor: "#D97706",
                      color: "#FFF",
                      fontSize: "8px",
                      fontFamily: "var(--font-mono)",
                      fontWeight: "700",
                      padding: "1px 4px",
                      borderRadius: "2px",
                      whiteSpace: "nowrap",
                    }}
                  >
                    SECONDARY STRESS FRACTURE (35%)
                  </div>
                </div>

                {/* Zone 3: Micro-Fissure Concentration (Blue) */}
                <div
                  style={{
                    position: "absolute",
                    top: "26%",
                    left: "11%",
                    width: "6%",
                    height: "8%",
                    border: "2px dashed #2563EB",
                    backgroundColor: "rgba(37, 99, 235, 0.22)",
                    borderRadius: "3px",
                    pointerEvents: "none",
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      top: "-18px",
                      left: "0",
                      backgroundColor: "#2563EB",
                      color: "#FFF",
                      fontSize: "8px",
                      fontFamily: "var(--font-mono)",
                      fontWeight: "700",
                      padding: "1px 4px",
                      borderRadius: "2px",
                      whiteSpace: "nowrap",
                    }}
                  >
                    MICRO-FISSURE CONCENTRATION (35%)
                  </div>
                </div>

                {/* Zone 4: Primary Crack Fissure (Red) */}
                <div
                  style={{
                    position: "absolute",
                    top: "47%",
                    left: "18%",
                    width: "24%",
                    height: "36%",
                    border: "2px dashed #DC2626",
                    backgroundColor: "rgba(220, 38, 38, 0.22)",
                    borderRadius: "3px",
                    pointerEvents: "none",
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      top: "-18px",
                      left: "0",
                      backgroundColor: "#DC2626",
                      color: "#FFF",
                      fontSize: "8px",
                      fontFamily: "var(--font-mono)",
                      fontWeight: "700",
                      padding: "1px 4px",
                      borderRadius: "2px",
                      whiteSpace: "nowrap",
                    }}
                  >
                    PRIMARY CRACK FISSURE (35%)
                  </div>
                </div>

                {/* Zone 5: Major Central Fracture & Stone Loss (Crimson) */}
                <div
                  style={{
                    position: "absolute",
                    top: "58%",
                    left: "43%",
                    width: "14%",
                    height: "18%",
                    border: "2px dashed #B91C1C",
                    backgroundColor: "rgba(185, 28, 28, 0.25)",
                    borderRadius: "3px",
                    pointerEvents: "none",
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      top: "-18px",
                      left: "0",
                      backgroundColor: "#B91C1C",
                      color: "#FFF",
                      fontSize: "8px",
                      fontFamily: "var(--font-mono)",
                      fontWeight: "700",
                      padding: "1px 4px",
                      borderRadius: "2px",
                      whiteSpace: "nowrap",
                    }}
                  >
                    MAJOR FRACTURE & LOSS (45%)
                  </div>
                </div>

                {/* Zone 6: Spalling & Surface Loss (Orange) */}
                <div
                  style={{
                    position: "absolute",
                    top: "88%",
                    left: "11%",
                    width: "12%",
                    height: "8%",
                    border: "2px dashed #EA580C",
                    backgroundColor: "rgba(234, 88, 12, 0.22)",
                    borderRadius: "3px",
                    pointerEvents: "none",
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      top: "-18px",
                      left: "0",
                      backgroundColor: "#EA580C",
                      color: "#FFF",
                      fontSize: "8px",
                      fontFamily: "var(--font-mono)",
                      fontWeight: "700",
                      padding: "1px 4px",
                      borderRadius: "2px",
                      whiteSpace: "nowrap",
                    }}
                  >
                    SPALLING & SURFACE LOSS (35%)
                  </div>
                </div>
              </div>
              <div style={{ fontSize: "10px", color: "#A8A29E", fontFamily: "var(--font-mono)", marginTop: "4px" }}>
                PHOTOGRAMMETRIC SOURCE • NEURAL CRACK SEGMENTATION ACTIVE
              </div>
            </div>

            <div style={styles.findingsBox}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                <span className="label-uppercase">PRIMARY DAMAGE DIAGNOSIS</span>
                <StatusBadge status={selectedReport.severity} />
              </div>
              <div style={{ fontSize: "14px", fontWeight: 700 }}>{selectedReport.damageType}</div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                Aggregate AI Confidence: <strong>{selectedReport.confidence}</strong> • Emergency Rating: <strong>{selectedReport.emergencyLevel}</strong>
              </div>
            </div>

            {/* Multiple Localized Defect Zones */}
            <div style={{ backgroundColor: "#FFFFFF", border: "1px solid var(--border-color)", borderRadius: "6px", padding: "12px" }}>
              <span className="label-uppercase" style={{ marginBottom: "8px", display: "block" }}>
                LOCALIZED MULTI-ZONE DEFECT SEGMENTATION
              </span>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-light)", color: "var(--text-secondary)", textAlign: "left" }}>
                    <th style={{ padding: "4px 6px" }}>ZONE</th>
                    <th style={{ padding: "4px 6px" }}>DEFECT TYPE</th>
                    <th style={{ padding: "4px 6px" }}>LOCATION</th>
                    <th style={{ padding: "4px 6px", textAlign: "right" }}>CONFIDENCE</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ borderBottom: "1px solid #F3F0EC" }}>
                    <td style={{ padding: "6px 6px", fontWeight: 600, color: "#B91C1C" }}>Zone 1 (Major)</td>
                    <td style={{ padding: "6px 6px" }}>MAJOR FRACTURE & LOSS</td>
                    <td style={{ padding: "6px 6px", color: "var(--text-secondary)" }}>Central Nasal Axis (43% X, 58% Y)</td>
                    <td style={{ padding: "6px 6px", textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 700, color: "#B91C1C" }}>45%</td>
                  </tr>
                  <tr style={{ borderBottom: "1px solid #F3F0EC" }}>
                    <td style={{ padding: "6px 6px", fontWeight: 600, color: "#DC2626" }}>Zone 2 (Primary)</td>
                    <td style={{ padding: "6px 6px" }}>PRIMARY CRACK FISSURE</td>
                    <td style={{ padding: "6px 6px", color: "var(--text-secondary)" }}>Cheek Fracture Field (18% X, 47% Y)</td>
                    <td style={{ padding: "6px 6px", textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 700, color: "#DC2626" }}>35%</td>
                  </tr>
                  <tr style={{ borderBottom: "1px solid #F3F0EC" }}>
                    <td style={{ padding: "6px 6px", fontWeight: 600, color: "#D97706" }}>Zone 3 (Secondary)</td>
                    <td style={{ padding: "6px 6px" }}>SECONDARY STRESS FRACTURE</td>
                    <td style={{ padding: "6px 6px", color: "var(--text-secondary)" }}>Floral Crown Relief (51% X, 5% Y)</td>
                    <td style={{ padding: "6px 6px", textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 700, color: "#D97706" }}>35%</td>
                  </tr>
                  <tr style={{ borderBottom: "1px solid #F3F0EC" }}>
                    <td style={{ padding: "6px 6px", fontWeight: 600, color: "#2563EB" }}>Zone 4 (Micro)</td>
                    <td style={{ padding: "6px 6px" }}>MICRO-FISSURE CONCENTRATION</td>
                    <td style={{ padding: "6px 6px", color: "var(--text-secondary)" }}>Left Hair Swirl (11% X, 26% Y)</td>
                    <td style={{ padding: "6px 6px", textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 700, color: "#2563EB" }}>35%</td>
                  </tr>
                  <tr style={{ borderBottom: "1px solid #F3F0EC" }}>
                    <td style={{ padding: "6px 6px", fontWeight: 600, color: "#8B5CF6" }}>Zone 5 (Delamination)</td>
                    <td style={{ padding: "6px 6px" }}>STRUCTURAL DELAMINATION</td>
                    <td style={{ padding: "6px 6px", color: "var(--text-secondary)" }}>Forehead Apex (11% X, 5% Y)</td>
                    <td style={{ padding: "6px 6px", textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 700, color: "#8B5CF6" }}>35%</td>
                  </tr>
                  <tr>
                    <td style={{ padding: "6px 6px", fontWeight: 600, color: "#EA580C" }}>Zone 6 (Surface)</td>
                    <td style={{ padding: "6px 6px" }}>SPALLING & SURFACE LOSS</td>
                    <td style={{ padding: "6px 6px", color: "var(--text-secondary)" }}>Basal Margin (11% X, 88% Y)</td>
                    <td style={{ padding: "6px 6px", textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 700, color: "#EA580C" }}>35%</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div>
              <span className="label-uppercase">RECOMMENDED CONSERVATION INTERVENTION</span>
              <p style={{ fontSize: "12.5px", color: "var(--text-primary)", marginTop: "4px", lineHeight: "1.4" }}>
                {selectedReport.summary}
              </p>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px", paddingTop: "12px", borderTop: "1px solid var(--border-light)" }}>
              <button onClick={() => setSelectedReport(null)} className="btn-secondary">
                Close
              </button>
              <button
                onClick={() => handleExportPdf(selectedReport)}
                className="btn-primary"
                disabled={isExporting}
              >
                <FileDown size={14} />
                <span>EXPORT AS PDF</span>
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

const styles = {
  filterCard: {
    padding: "10px 14px"
  },
  searchGroup: {
    display: "flex",
    alignItems: "center",
    gap: "8px"
  },
  modalMetaGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "12px",
    paddingBottom: "12px",
    borderBottom: "1px solid var(--border-light)"
  },
  findingsBox: {
    backgroundColor: "#FAF8F5",
    border: "1px solid var(--border-color)",
    borderRadius: "6px",
    padding: "12px"
  }
};
