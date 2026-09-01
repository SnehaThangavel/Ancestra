import React, { useState, useEffect } from "react";
import { useApp } from "../../context/AppContext";
import { Modal } from "../common/Modal";
import { ImageUploaderInput } from "../common/ImageUploaderInput";

export function SiteModal({ isOpen, onClose, siteToEdit = null, prefillData = null }) {
  const { addHeritageSite, updateHeritageSite } = useApp();

  const isEditing = Boolean(siteToEdit);
  const initialData = siteToEdit || prefillData;

  const [formData, setFormData] = useState({
    name: "",
    location: "",
    circle: "ASI Chennai Circle",
    material: "Granite & Freestone Blockwork",
    category: "UNESCO World Heritage Site",
    description: "",
    image: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
    status: "CRITICAL"
  });

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || "",
        location: initialData.location || "",
        circle: initialData.circle || "ASI Chennai Circle",
        material: initialData.material || "Granite & Freestone Blockwork",
        category: initialData.category || "UNESCO World Heritage Site",
        description: initialData.description || "",
        image: initialData.image || "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
        status: initialData.status || "CRITICAL"
      });
    } else {
      setFormData({
        name: "",
        location: "",
        circle: "ASI Chennai Circle",
        material: "Granite & Freestone Blockwork",
        category: "UNESCO World Heritage Site",
        description: "",
        image: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
        status: "CRITICAL"
      });
    }
  }, [initialData, isOpen]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.name || !formData.location) return;

    if (isEditing) {
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
      title={isEditing ? "EDIT HERITAGE MONUMENT SITE" : "REGISTER NEW HERITAGE MONUMENT SITE"}
      width="580px"
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <div className="form-group">
          <label className="form-label">HERITAGE SITE NAME *</label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g. Shore Temple, Mahabalipuram"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div className="form-group">
            <label className="form-label">LOCATION & STATE *</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Mahabalipuram, Tamil Nadu"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">ASI CIRCLE</label>
            <select
              className="form-select"
              value={formData.circle}
              onChange={(e) => setFormData({ ...formData, circle: e.target.value })}
            >
              <option value="ASI Chennai Circle">ASI Chennai Circle</option>
              <option value="ASI Bengaluru Circle">ASI Bengaluru Circle</option>
              <option value="ASI Bhubaneswar Circle">ASI Bhubaneswar Circle</option>
              <option value="ASI Agra Circle">ASI Agra Circle</option>
              <option value="ASI Delhi Circle">ASI Delhi Circle</option>
            </select>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div className="form-group">
            <label className="form-label">CONSTRUCTION MATERIAL</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Cut Granite Blocks & Mortar"
              value={formData.material}
              onChange={(e) => setFormData({ ...formData, material: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">HERITAGE CATEGORY</label>
            <select
              className="form-select"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            >
              <option value="UNESCO World Heritage Site">UNESCO World Heritage Site</option>
              <option value="National Monument of Importance">National Monument of Importance</option>
              <option value="State Protected Structural Site">State Protected Structural Site</option>
            </select>
          </div>
        </div>

        {/* Drag & Drop File Picker Image Component */}
        <ImageUploaderInput
          value={formData.image}
          onChange={(imgData) => setFormData({ ...formData, image: imgData })}
          label="HERITAGE SITE PHOTOGRAPH *"
        />

        <div className="form-group">
          <label className="form-label">HISTORICAL ARCHITECTURAL DESCRIPTION</label>
          <textarea
            className="form-textarea"
            rows="3"
            placeholder="Brief architectural notes, structural layout, load bearing systems..."
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary">
            {isEditing ? "Save Changes" : "Register Site"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
