import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { ImageUploader } from "../../components/expert/ImageUploader";
import { SectionCard } from "../../components/common/SectionCard";
import { Cpu, ArrowRight, XCircle, Database } from "lucide-react";

export function ImageAnalysisPage() {
  const navigate = useNavigate();
  const { heritageSites, architecturalRegions, setPendingAnalysis, aiEngineStatus } = useApp();

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

  const [captureDate, setCaptureDate] = useState(new Date().toISOString().split("T")[0]);
  const [sensorSpec, setSensorSpec] = useState("Calibrated DSLR / Mirrorless (60MP+ Full-Frame)");
  const [observationNotes, setObservationNotes] = useState("");

  const getSiteDefaultImage = (siteId, regionId) => {
    const site = heritageSites.find((s) => s.id === siteId);
    const region = architecturalRegions.find((r) => r.id === regionId);

    const url =
      region?.image_url ||
      region?.image ||
      site?.image_url ||
      site?.image ||
      "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800";

    const cleanSiteName = site?.name?.split(",")[0]?.replace(/[^a-zA-Z0-9]/g, "_").toLowerCase() || "heritage_site";
    const cleanRegName = region?.name?.replace(/[^a-zA-Z0-9]/g, "_").toLowerCase() || "zone";
    const name = `${cleanSiteName}_${cleanRegName}_observation.jpg`;

    return { url, name, isCustomUpload: false };
  };

  const [selectedImageData, setSelectedImageData] = useState(() => getSiteDefaultImage(selectedSiteId, selectedRegionId));

  // Sync image with selected monument/region directly from DB record if not manually uploaded by user
  useEffect(() => {
    if (selectedSiteId && !selectedImageData?.isCustomUpload) {
      setSelectedImageData(getSiteDefaultImage(selectedSiteId, selectedRegionId));
    }
  }, [selectedSiteId, selectedRegionId, heritageSites, architecturalRegions]);

  // Dynamically derive preset test assets from actual database heritage sites
  const presetSamples = heritageSites.slice(0, 8).map((site) => ({
    name: site.name.split(",")[0],
    url: site.image_url || site.image || "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
  }));

  const canSubmit = aiEngineStatus.online && aiEngineStatus.modelState !== "ERROR" && aiEngineStatus.modelState !== "MAINTENANCE";

  const handleStartAnalysis = async () => {
    if (!canSubmit) return;

    const siteObj = heritageSites.find((s) => s.id === selectedSiteId);
    const regionObj = architecturalRegions.find((r) => r.id === selectedRegionId);

    let fileToUpload = selectedImageData.file;

    // If using a preset sample URL without a direct local file upload, fetch or generate a real File blob
    if (!fileToUpload) {
      try {
        const response = await fetch(selectedImageData.url);
        const blob = await response.blob();
        fileToUpload = new File([blob], selectedImageData.name || "observation_sample.jpg", {
          type: blob.type || "image/jpeg",
        });
      } catch {
        // Fallback: create a 600x600 high-contrast test stone texture on canvas
        const canvas = document.createElement("canvas");
        canvas.width = 600;
        canvas.height = 600;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#8E857B";
        ctx.fillRect(0, 0, 600, 600);
        ctx.fillStyle = "#333333";
        ctx.beginPath();
        ctx.arc(300, 300, 50, 0, Math.PI * 2);
        ctx.fill();
        const blob = await new Promise((res) => canvas.toBlob(res, "image/jpeg", 0.9));
        fileToUpload = new File([blob], "synthetic_observation.jpg", { type: "image/jpeg" });
      }
    }

    setPendingAnalysis({
      siteId: selectedSiteId,
      siteName: siteObj ? siteObj.name : "Heritage Monument",
      regionId: selectedRegionId,
      regionName: regionObj ? regionObj.name : "Architectural Region",
      captureDate,
      sensorSpec,
      notes: observationNotes,
      imageUrl: selectedImageData.url,
      imageFile: fileToUpload,
    });

    navigate("/expert/ai-analysis");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header */}
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
                    <option value="">No monuments available</option>
                  )}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">ARCHITECTURAL REGION *</label>
                <select
                  className="form-select"
                  value={selectedRegionId}
                  onChange={(e) => setSelectedRegionId(e.target.value)}
                >
                  {filteredRegions.length > 0 ? (
                    filteredRegions.map((reg) => (
                      <option key={reg.id} value={reg.id}>
                        [{reg.code || "REG"}] {reg.name}
                      </option>
                    ))
                  ) : (
                    <option value="">No regions registered for this monument</option>
                  )}
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
                <span>Spatial coordinate anchoring & sequential ORB alignment</span>
              </div>
              <div style={styles.pipelineItem}>
                <span style={styles.pipelineNum}>03.</span>
                <span>Lithic damage segmentation & SSIM defect bounding box extraction</span>
              </div>
              <div style={styles.pipelineItem}>
                <span style={styles.pipelineNum}>04.</span>
                <span>Consensus state update & structural health index calculation</span>
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
                cursor: canSubmit ? "pointer" : "not-allowed",
              }}
              disabled={!canSubmit}
            >
              <span>{canSubmit ? "Submit & Run AI Perception Pipeline" : "AI Engine Offline / Maintenance"}</span>
              <ArrowRight size={14} />
            </button>
          </div>

          <div style={styles.simCard}>
            <div style={styles.simHeader}>
              <Database size={15} color="#8E857B" />
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#8E857B", letterSpacing: "0.06em" }}>
                LIVE DATABASE PIPELINE
              </span>
            </div>
            <p style={{ fontSize: "11.5px", color: "var(--text-secondary)", lineHeight: "1.4" }}>
              Submitting this intake form connects directly to the backend FastAPI server, saves the observation to PostgreSQL, executes Module 1 sequential alignment and Module 4 SSIM defect validation.
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
    color: "#DC2626",
  },
  pipelineHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    paddingBottom: "10px",
    borderBottom: "1px solid var(--border-light)",
    marginBottom: "12px",
  },
  pipelineSteps: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  pipelineItem: {
    display: "flex",
    alignItems: "flex-start",
    gap: "6px",
    fontSize: "11.5px",
    color: "var(--text-secondary)",
  },
  pipelineNum: {
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    color: "#8E857B",
  },
  simCard: {
    backgroundColor: "#F5F1E9",
    border: "1px solid #E3DDD3",
    borderRadius: "6px",
    padding: "14px",
  },
  simHeader: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    marginBottom: "6px",
  },
};
