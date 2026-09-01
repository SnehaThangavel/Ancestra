import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { ImageUploader } from "../../components/expert/ImageUploader";
import { SectionCard } from "../../components/common/SectionCard";
import { Cpu, ArrowRight, Info, XCircle } from "lucide-react";

export function ImageAnalysisPage() {
  const navigate = useNavigate();
  const { heritageSites, architecturalRegions, setPendingAnalysis, aiEngineStatus } = useApp();

  const [selectedSiteId, setSelectedSiteId] = useState(heritageSites[0]?.id || "site_01");
  const filteredRegions = architecturalRegions.filter((r) => r.siteId === selectedSiteId);
  const [selectedRegionId, setSelectedRegionId] = useState(filteredRegions[0]?.id || "reg_01");
  
  const [captureDate, setCaptureDate] = useState(new Date().toISOString().split("T")[0]);
  const [sensorSpec, setSensorSpec] = useState("Calibrated DSLR / Mirrorless (60MP+ Full-Frame)");
  const [observationNotes, setObservationNotes] = useState("");

  const [selectedImageData, setSelectedImageData] = useState({
    url: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
    name: "shore_temple_vimana_east_macro.jpg"
  });

  const presetSamples = [
    {
      name: "Shore Temple Crack",
      url: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
    },
    {
      name: "Konark Roof Spalling",
      url: "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800"
    },
    {
      name: "Hampi Chariot Fractures",
      url: "https://images.unsplash.com/photo-1627894099419-f5ebba5e3f42?auto=format&fit=crop&q=80&w=800"
    }
  ];

  const canSubmit = aiEngineStatus.online && aiEngineStatus.modelState !== "ERROR" && aiEngineStatus.modelState !== "MAINTENANCE";

  const handleStartAnalysis = () => {
    if (!canSubmit) return;

    const siteObj = heritageSites.find((s) => s.id === selectedSiteId);
    const regionObj = architecturalRegions.find((r) => r.id === selectedRegionId);

    setPendingAnalysis({
      siteId: selectedSiteId,
      siteName: siteObj ? siteObj.name : "Shore Temple, Mahabalipuram",
      regionId: selectedRegionId,
      regionName: regionObj ? regionObj.name : "East-Facing Rajasimhesvara Vimana",
      captureDate,
      sensorSpec,
      notes: observationNotes,
      imageUrl: selectedImageData.url
    });

    navigate("/expert/ai-analysis");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header (No Module ID) */}
      <div>
        <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: "0 0 4px 0" }}>
          IMAGE ANALYSIS & OBSERVATION INTAKE
        </h1>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
          Upload high-resolution photographic documentation for AI lithic deterioration segmentation & structural damage estimation.
        </p>
      </div>

      {/* System Offline / Maintenance Notice Banner */}
      {!canSubmit && (
        <div style={styles.engineNoticeBanner}>
          <XCircle size={16} color="#DC2626" />
          <span>
            <strong>AI ASSESSMENT ENGINE UNAVAILABLE:</strong> System is currently <strong>{aiEngineStatus.online ? aiEngineStatus.modelState : "OFFLINE"}</strong>. New image analysis submissions are suspended until system maintenance completes.
          </span>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "2.3fr 1fr", gap: "22px" }}>
        {/* Left Intake Form */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Section 1 */}
          <SectionCard title="1. SPATIAL & MONUMENT METADATA" subtitle="Specify the structural asset and architectural region represented in the observation.">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "14px" }}>
              <div className="form-group">
                <label className="form-label">TARGET MONUMENT *</label>
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

              <div className="form-group">
                <label className="form-label">ARCHITECTURAL REGION *</label>
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

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "14px" }}>
              <div className="form-group">
                <label className="form-label">CAPTURE DATE *</label>
                <input
                  type="date"
                  className="form-input"
                  value={captureDate}
                  onChange={(e) => setCaptureDate(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">DEVICE / SENSOR SPEC</label>
                <select
                  className="form-select"
                  value={sensorSpec}
                  onChange={(e) => setSensorSpec(e.target.value)}
                >
                  <option value="Calibrated DSLR / Mirrorless (60MP+ Full-Frame)">Calibrated DSLR / Mirrorless (60MP+ Full-Frame)</option>
                  <option value="UAV / Drone Photogrammetry Array">UAV / Drone Photogrammetry Array</option>
                  <option value="Terrestrial Laser Scan Texture Capture">Terrestrial Laser Scan Texture Capture</option>
                  <option value="Mobile Field Scanner">Mobile Field Scanner</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">FIELD OBSERVATION NOTES (OPTIONAL)</label>
              <textarea
                className="form-textarea"
                placeholder="Detail current ambient humidity, noticeable macro fractures, or recent rainfall context..."
                value={observationNotes}
                onChange={(e) => setObservationNotes(e.target.value)}
              />
            </div>
          </SectionCard>

          {/* Section 2 */}
          <SectionCard title="2. LITHIC IMAGERY ASSET" subtitle="Upload RAW or lossless TIFF/JPEG photographic documentation.">
            <ImageUploader
              selectedImage={selectedImageData}
              onImageSelect={(imgData) => setSelectedImageData(imgData)}
              sampleImages={presetSamples}
            />
          </SectionCard>
        </div>

        {/* Right Info Panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          <div className="ancestra-card">
            <div style={styles.pipelineHeader}>
              <Cpu size={16} color="#A04022" />
              <h3 className="font-serif-heading" style={{ fontSize: "14px", margin: 0 }}>
                PERCEPTION PIPELINE
              </h3>
            </div>

            <div style={styles.pipelineSteps}>
              <div style={styles.pipelineItem}>
                <span style={styles.pipelineNum}>01.</span>
                <span>Photometric calibration & color-checker normalization</span>
              </div>
              <div style={styles.pipelineItem}>
                <span style={styles.pipelineNum}>02.</span>
                <span>Spatial coordinate anchoring to historical region polygon</span>
              </div>
              <div style={styles.pipelineItem}>
                <span style={styles.pipelineNum}>03.</span>
                <span>Lithic damage segmentation (cracks, salt efflorescence, spalling)</span>
              </div>
              <div style={styles.pipelineItem}>
                <span style={styles.pipelineNum}>04.</span>
                <span>Cross-temporal consensus weight calculation</span>
              </div>
            </div>

            <button
              onClick={handleStartAnalysis}
              className="btn-primary"
              style={{
                width: "100%",
                padding: "12px",
                marginTop: "16px",
                opacity: canSubmit ? 1 : 0.5,
                cursor: canSubmit ? "pointer" : "not-allowed"
              }}
              disabled={!canSubmit}
            >
              <span>{canSubmit ? "Submit & Run Simulated Analysis" : "AI Engine Offline / Maintenance"}</span>
              <ArrowRight size={14} />
            </button>
          </div>

          <div style={styles.simCard}>
            <div style={styles.simHeader}>
              <Info size={15} color="#8E857B" />
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#8E857B", letterSpacing: "0.06em" }}>
                SIMULATION NOTE
              </span>
            </div>
            <p style={{ fontSize: "11.5px", color: "var(--text-secondary)", lineHeight: "1.4" }}>
              In this development foundation phase, submitting this form will simulate perceptual analysis execution and redirect to the structural assessment result record.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  engineNoticeBanner: {
    padding: "10px 14px",
    backgroundColor: "#FEF2F2",
    border: "1px solid #FCA5A5",
    borderRadius: "6px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    fontSize: "12px",
    color: "#DC2626"
  },
  pipelineHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    paddingBottom: "10px",
    borderBottom: "1px solid var(--border-light)",
    marginBottom: "12px"
  },
  pipelineSteps: {
    display: "flex",
    flexDirection: "column",
    gap: "10px"
  },
  pipelineItem: {
    display: "flex",
    alignItems: "flex-start",
    gap: "6px",
    fontSize: "11.5px",
    color: "var(--text-secondary)"
  },
  pipelineNum: {
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    color: "#8E857B"
  },
  simCard: {
    backgroundColor: "#F5F1E9",
    border: "1px solid #E3DDD3",
    borderRadius: "6px",
    padding: "14px"
  },
  simHeader: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    marginBottom: "6px"
  }
};
