import React, { useState, useEffect } from "react";
import { Modal } from "../common/Modal";
import { useApp } from "../../context/AppContext";

export function SiteModal({ isOpen, onClose, siteToEdit = null }) {
  const { addHeritageSite, updateHeritageSite } = useApp();

  const [formData, setFormData] = useState({
    name: "",
    location: "",
    period: "Chola Dynasty • 1000 CE",
    category: "UNESCO World Heritage Site",
    structureType: "Monolithic Dry-Stone Granite",
    material: "Granite Masonry",
    circle: "Chennai Circle (ASI)",
    description: "",
    status: "STABLE",
    image: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
  });

  useEffect(() => {
    if (siteToEdit) {
      setFormData({
        name: siteToEdit.name || "",
        location: siteToEdit.location || "",
        period: siteToEdit.period || "",
        category: siteToEdit.category || "UNESCO World Heritage Site",
        structureType: siteToEdit.structureType || "",
        material: siteToEdit.material || "",
        circle: siteToEdit.circle || "Chennai Circle (ASI)",
        description: siteToEdit.description || "",
        status: siteToEdit.status || "STABLE",
        image: siteToEdit.image || "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
      });
    } else {
      setFormData({
        name: "",
        location: "",
        period: "Chola Dynasty • 1000 CE",
        category: "UNESCO World Heritage Site",
        structureType: "Monolithic Dry-Stone Granite",
        material: "Granite Masonry",
        circle: "Chennai Circle (ASI)",
        description: "",
        status: "STABLE",
        image: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
      });
    }
  }, [siteToEdit, isOpen]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.name) return;

    if (siteToEdit) {
      updateHeritageSite(siteToEdit.id, formData);
    } else {
      addHeritageSite(formData);
    }
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={siteToEdit ? "EDIT HERITAGE MONUMENT SITE" : "REGISTER NEW HERITAGE MONUMENT SITE"}
      width="580px"
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <div className="form-group">
          <label className="form-label">HERITAGE SITE NAME *</label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g. Airavatesvara Temple, Darasuram"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div className="form-group">
            <label className="form-label">LOCATION & STATE</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Darasuram, Tamil Nadu"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">ASI CIRCLE</label>
            <input
              type="text"
              className="form-input"
              value={formData.circle}
              onChange={(e) => setFormData({ ...formData, circle: e.target.value })}
            />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div className="form-group">
            <label className="form-label">ERA / HISTORICAL PERIOD</label>
            <input
              type="text"
              className="form-input"
              value={formData.period}
              onChange={(e) => setFormData({ ...formData, period: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">MONITORING STATUS</label>
            <select
              className="form-select"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            >
              <option value="STABLE">STABLE</option>
              <option value="ATTENTION">ATTENTION</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div className="form-group">
            <label className="form-label">STRUCTURE TYPE</label>
            <input
              type="text"
              className="form-input"
              value={formData.structureType}
              onChange={(e) => setFormData({ ...formData, structureType: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">CONSTRUCTION MATERIAL</label>
            <input
              type="text"
              className="form-input"
              value={formData.material}
              onChange={(e) => setFormData({ ...formData, material: e.target.value })}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">HERITAGE CATEGORY</label>
          <select
            className="form-select"
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
          >
            <option value="UNESCO World Heritage Site">UNESCO World Heritage Site</option>
            <option value="National Protected Monument (ASI)">National Protected Monument (ASI)</option>
            <option value="State Protected Monument">State Protected Monument</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">REFERENCE IMAGE URL</label>
          <input
            type="text"
            className="form-input"
            value={formData.image}
            onChange={(e) => setFormData({ ...formData, image: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label">HISTORICAL ARCHITECTURAL DESCRIPTION</label>
          <textarea
            className="form-textarea"
            placeholder="Detail structural composition, masonry techniques, and environmental exposure..."
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary">
            {siteToEdit ? "Save Changes" : "Register Heritage Site"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
