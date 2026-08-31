import React, { useState } from "react";
import { useApp } from "../context/AppContext";
import { DataTable } from "../components/common/DataTable";
import { StatusBadge } from "../components/common/StatusBadge";
import { EmergencyBadge } from "../components/common/EmergencyBadge";
import { Modal } from "../components/common/Modal";
import { generateAncestrapdfReport } from "../utils/pdfGenerator";
import { FileText, Download, Search, Eye, FileDown } from "lucide-react";

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

          {/* Button text MUST be exactly 'EXPORT AS PDF' */}
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
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
            <span className="module-badge">REP-07</span>
            <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: 0 }}>
              CONSERVATION REPORTS & EXECUTIVE DOSSIERS
            </h1>
          </div>
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

            <div style={styles.findingsBox}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                <span className="label-uppercase">AI DETECTED DAMAGE FINDING</span>
                <StatusBadge status={selectedReport.severity} />
              </div>
              <div style={{ fontSize: "14px", fontWeight: 700 }}>{selectedReport.damageType}</div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                AI Confidence Level: <strong>{selectedReport.confidence}</strong>
              </div>
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
