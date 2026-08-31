import React, { useState } from "react";
import { useApp } from "../../context/AppContext";
import { DataTable } from "../../components/common/DataTable";
import { StatusBadge } from "../../components/common/StatusBadge";
import { RegionModal } from "../../components/admin/RegionModal";
import { Modal } from "../../components/common/Modal";
import { Plus, Search, Edit3, Trash2, AlertTriangle } from "lucide-react";

export function RegionsPage() {
  const { architecturalRegions, deleteArchitecturalRegion, currentUser } = useApp();
  const isAdmin = currentUser?.role === "ADMINISTRATOR";

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [regionToEdit, setRegionToEdit] = useState(null);
  const [regionToDelete, setRegionToDelete] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredRegions = architecturalRegions.filter(
    (r) =>
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.siteName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleConfirmDelete = () => {
    if (regionToDelete) {
      deleteArchitecturalRegion(regionToDelete.id);
      setRegionToDelete(null);
    }
  };

  const columns = [
    {
      header: "REGION ID",
      accessor: "code",
      render: (row) => <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--accent-primary)" }}>{row.code}</span>
    },
    {
      header: "HERITAGE MONUMENT",
      accessor: "siteName",
      render: (row) => <strong>{row.siteName}</strong>
    },
    {
      header: "ARCHITECTURAL REGION",
      accessor: "name"
    },
    {
      header: "TYPE",
      accessor: "type",
      render: (row) => <span className="version-pill">{row.type}</span>
    },
    {
      header: "STRUCTURAL IMPORTANCE",
      accessor: "importance"
    },
    {
      header: "RISK LEVEL",
      accessor: "riskLevel",
      render: (row) => <StatusBadge status={row.riskLevel} size="sm" />
    },
    {
      header: "LAST ASSESSMENT",
      accessor: "lastAssessment",
      render: (row) => <span style={{ fontFamily: "var(--font-mono)" }}>{row.lastAssessment}</span>
    }
  ];

  // Add Action column for Administrator ONLY
  if (isAdmin) {
    columns.push({
      header: "ACTIONS",
      align: "right",
      render: (row) => (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "6px" }}>
          <button
            onClick={() => setRegionToEdit(row)}
            className="btn-secondary"
            style={{ padding: "4px 8px", fontSize: "11px" }}
            title="Edit Architectural Region"
          >
            <Edit3 size={12} color="#A04022" />
            <span>Edit</span>
          </button>
          <button
            onClick={() => setRegionToDelete(row)}
            className="btn-outline-danger"
            style={{ padding: "4px 8px", fontSize: "11px" }}
            title="Delete Architectural Region"
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
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
            <span className="module-badge">ADM-03</span>
            <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: 0 }}>
              ARCHITECTURAL REGION MANAGEMENT
            </h1>
          </div>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            Deconstruct heritage structures into monitored structural regions (Vimanas, Plinths, Pillars, Domes, Sculptures).
          </p>
        </div>

        {isAdmin && (
          <button onClick={() => setIsAddModalOpen(true)} className="btn-primary">
            <Plus size={15} />
            <span>Add Region</span>
          </button>
        )}
      </div>

      {/* Search Bar */}
      <div className="ancestra-card" style={styles.filterCard}>
        <div style={styles.searchGroup}>
          <Search size={15} color="#8E857B" />
          <input
            type="text"
            className="form-input"
            style={{ border: "none", background: "none" }}
            placeholder="Search architectural regions by name, monument, or region type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Regions Data Table */}
      <DataTable columns={columns} data={filteredRegions} emptyMessage="No architectural regions found matching query." />

      {/* Add Modal */}
      <RegionModal isOpen={isAddModalOpen} onClose={() => setIsAddModalOpen(false)} />

      {/* Edit Modal */}
      {regionToEdit && (
        <RegionModal
          isOpen={Boolean(regionToEdit)}
          onClose={() => setRegionToEdit(null)}
          regionToEdit={regionToEdit}
        />
      )}

      {/* Delete Confirmation Modal */}
      {regionToDelete && (
        <Modal
          isOpen={Boolean(regionToDelete)}
          onClose={() => setRegionToDelete(null)}
          title="DELETE ARCHITECTURAL REGION?"
          width="440px"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
              <AlertTriangle size={20} color="#DC2626" style={{ flexShrink: 0, marginTop: "2px" }} />
              <div>
                <strong style={{ fontSize: "14px", color: "var(--text-primary)" }}>{regionToDelete.name}</strong>
                <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px", lineHeight: "1.4" }}>
                  ARE YOU SURE YOU WANT TO DELETE THIS ARCHITECTURAL REGION FROM MONITORED RECORDS?
                </p>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
              <button onClick={() => setRegionToDelete(null)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                className="btn-primary"
                style={{ backgroundColor: "#DC2626", borderColor: "#DC2626" }}
              >
                Delete Region
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
  }
};
