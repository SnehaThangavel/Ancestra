import React, { useState } from "react";
import { useApp } from "../../context/AppContext";
import { DataTable } from "../../components/common/DataTable";
import { StatusBadge } from "../../components/common/StatusBadge";
import { SiteModal } from "../../components/admin/SiteModal";
import { RequestReviewModal } from "../../components/admin/RequestReviewModal";
import { Modal } from "../../components/common/Modal";
import { Plus, Search, Edit3, Trash2, AlertTriangle, FileCheck, Eye } from "lucide-react";

export function HeritageSitesPage() {
  const { heritageSites, siteRequests, deleteHeritageSite, currentUser } = useApp();
  const isAdmin = currentUser?.role === "ADMINISTRATOR";

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [siteToEdit, setSiteToEdit] = useState(null);
  const [siteToDelete, setSiteToDelete] = useState(null);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [prefillRequestData, setPrefillRequestData] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  const pendingRequests = siteRequests.filter((r) => r.status === "PENDING ADMIN APPROVAL");

  const filteredSites = heritageSites.filter(
    (s) =>
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.material && s.material.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleConfirmDelete = () => {
    if (siteToDelete) {
      deleteHeritageSite(siteToDelete.id);
      setSiteToDelete(null);
    }
  };

  const handleOpenAddWithPrefill = (reqData) => {
    setPrefillRequestData({
      name: reqData.siteName,
      location: reqData.location,
      circle: reqData.circle,
      material: reqData.material,
      category: reqData.category,
      description: reqData.description,
      image: reqData.image
    });
    setIsAddModalOpen(true);
  };

  const columns = [
    {
      header: "SITE ID",
      accessor: "code",
      render: (row) => <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--accent-primary)" }}>{row.code}</span>
    },
    {
      header: "HERITAGE SITE NAME",
      accessor: "name",
      render: (row) => (
        <div>
          <strong style={{ fontSize: "13px" }}>{row.name}</strong>
          <div style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>{row.location}</div>
        </div>
      )
    },
    {
      header: "MATERIAL",
      accessor: "material"
    },
    {
      header: "REGIONS",
      accessor: "regionsCount",
      align: "center",
      render: (row) => <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{row.regionsCount || 0}</span>
    },
    {
      header: "CURRENT RISK",
      accessor: "status",
      render: (row) => <StatusBadge status={row.status} size="sm" />
    },
    {
      header: "LAST ASSESSMENT",
      accessor: "lastAssessment",
      render: (row) => <span style={{ fontFamily: "var(--font-mono)" }}>{row.lastAssessment}</span>
    }
  ];

  if (isAdmin) {
    columns.push({
      header: "ACTIONS",
      align: "right",
      render: (row) => (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "6px" }}>
          <button
            onClick={() => setSiteToEdit(row)}
            className="btn-secondary"
            style={{ padding: "4px 8px", fontSize: "11px" }}
            title="Edit Heritage Site"
          >
            <Edit3 size={12} color="#A04022" />
            <span>Edit</span>
          </button>
          <button
            onClick={() => setSiteToDelete(row)}
            className="btn-outline-danger"
            style={{ padding: "4px 8px", fontSize: "11px" }}
            title="Delete Heritage Site"
          >
            <Trash2 size={12} />
            <span>Delete</span>
          </button>
        </div>
      )
    });
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: "0 0 4px 0" }}>
            HERITAGE SITE MANAGEMENT
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            Register, configure, and maintain national protected heritage monument records.
          </p>
        </div>

        {isAdmin && (
          <button onClick={() => { setPrefillRequestData(null); setIsAddModalOpen(true); }} className="btn-primary">
            <Plus size={15} />
            <span>Add Heritage Site</span>
          </button>
        )}
      </div>

      {/* Admin Pending Site Requests Banner */}
      {isAdmin && pendingRequests.length > 0 && (
        <div style={styles.requestAlertCard} className="ancestra-card">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <FileCheck size={18} color="#A04022" />
            <div>
              <strong style={{ fontSize: "13px", color: "#1C1917" }}>
                PENDING HERITAGE SITE REQUESTS ({pendingRequests.length})
              </strong>
              <div style={{ fontSize: "11.5px", color: "var(--text-secondary)", marginTop: "2px" }}>
                Conservation Experts have submitted proposal requests requiring Administrator review and approval.
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {pendingRequests.map((req) => (
              <button
                key={req.id}
                onClick={() => setSelectedRequest(req)}
                className="btn-secondary"
                style={{ padding: "5px 12px", fontSize: "11.5px", borderColor: "rgba(160, 64, 34, 0.4)" }}
              >
                <Eye size={12} color="#A04022" />
                <span>Review Proposal: {req.siteName}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="ancestra-card" style={styles.filterCard}>
        <div style={styles.searchGroup}>
          <Search size={15} color="#8E857B" />
          <input
            type="text"
            className="form-input"
            style={{ border: "none", background: "none" }}
            placeholder="Search heritage sites by name, location, or material..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Sites Data Table */}
      <DataTable columns={columns} data={filteredSites} emptyMessage="No heritage sites found matching query." />

      {/* Register / Edit Modal */}
      <SiteModal
        isOpen={isAddModalOpen}
        onClose={() => { setIsAddModalOpen(false); setPrefillRequestData(null); }}
        prefillData={prefillRequestData}
      />

      {siteToEdit && (
        <SiteModal
          isOpen={Boolean(siteToEdit)}
          onClose={() => setSiteToEdit(null)}
          siteToEdit={siteToEdit}
        />
      )}

      {/* Request Review Modal */}
      {selectedRequest && (
        <RequestReviewModal
          isOpen={Boolean(selectedRequest)}
          onClose={() => setSelectedRequest(null)}
          request={selectedRequest}
          onAddDetails={(reqData) => handleOpenAddWithPrefill(reqData)}
        />
      )}

      {/* Delete Confirmation Modal */}
      {siteToDelete && (
        <Modal
          isOpen={Boolean(siteToDelete)}
          onClose={() => setSiteToDelete(null)}
          title="DELETE HERITAGE SITE?"
          width="440px"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
              <AlertTriangle size={20} color="#DC2626" style={{ flexShrink: 0, marginTop: "2px" }} />
              <div>
                <strong style={{ fontSize: "14px", color: "var(--text-primary)" }}>{siteToDelete.name}</strong>
                <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px", lineHeight: "1.4" }}>
                  THIS ACTION WILL REMOVE THE SITE FROM THE ACTIVE HERITAGE SITE LIST AND DELETE ALL ASSOCIATED REGION LOGS.
                </p>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
              <button onClick={() => setSiteToDelete(null)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                className="btn-primary"
                style={{ backgroundColor: "#DC2626", borderColor: "#DC2626" }}
              >
                Delete Site
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

const styles = {
  requestAlertCard: {
    backgroundColor: "#F7EDE9",
    border: "1px solid rgba(160, 64, 34, 0.3)",
    padding: "14px 18px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between"
  },
  filterCard: {
    padding: "10px 14px"
  },
  searchGroup: {
    display: "flex",
    alignItems: "center",
    gap: "8px"
  }
};
