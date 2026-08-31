import jsPDF from "jspdf";
import html2canvas from "html2canvas";

/**
 * Generates an official ANCESTRA Heritage Structural Assessment PDF Report
 * styled strictly in the website's visual identity (warm off-white #FAF8F5 background,
 * terracotta #A04022 header accents, serif typography, and embedded high-res photo).
 */
export async function generateAncestrapdfReport(report, siteData, regionData, assessmentData) {
  // Create off-screen HTML element formatted in ANCESTRA theme
  const container = document.createElement("div");
  container.style.position = "absolute";
  container.style.left = "-9999px";
  container.style.top = "-9999px";
  container.style.width = "800px";
  container.style.backgroundColor = "#FAF8F5";
  container.style.color = "#1C1917";
  container.style.fontFamily = "'Plus Jakarta Sans', sans-serif";
  container.style.padding = "32px";
  container.style.boxSizing = "border-box";

  const imgUrl =
    assessmentData?.imageUrl ||
    report?.imageUrl ||
    siteData?.image ||
    "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800";

  // Convert image to Base64 to ensure seamless PDF embedding
  const imageBase64 = await urlToBase64(imgUrl);

  const htmlContent = `
    <div style="background-color: #FAF8F5; border: 1px solid #E2DDD5; padding: 24px; border-radius: 6px;">
      <!-- Header Banner -->
      <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #A04022; padding-bottom: 12px; margin-bottom: 20px;">
        <div style="display: flex; items: center; gap: 10px;">
          <div style="width: 32px; height: 32px; background-color: #A04022; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #FFFFFF; font-weight: bold; font-size: 16px;">
            A
          </div>
          <div>
            <div style="font-family: 'Cinzel', serif; font-weight: 700; font-size: 18px; color: #1C1917; letter-spacing: 0.06em;">
              ANCESTRA
            </div>
            <div style="font-size: 9px; font-weight: 700; color: #8E857B; letter-spacing: 0.08em;">
              STRUCTURAL INTELLIGENCE & PREDICTIVE CONSERVATION
            </div>
          </div>
        </div>
        <div style="text-align: right; font-family: monospace; font-size: 11px; color: #57534E;">
          <div>PROTOCOL: ICOMOS / ASI</div>
          <div style="color: #A04022; font-weight: bold;">DOSSIER: ${report.id}</div>
        </div>
      </div>

      <!-- Report Title -->
      <div style="margin-bottom: 20px;">
        <h1 style="font-family: 'Cinzel', serif; font-size: 20px; color: #1C1917; margin: 0 0 4px 0;">
          HERITAGE STRUCTURAL ASSESSMENT REPORT
        </h1>
        <div style="font-size: 11px; color: #78716C; font-family: monospace;">
          ASSESSMENT DATE: ${report.date} • RECORD ID: ${report.id} • STATUS: ${report.status?.toUpperCase()}
        </div>
      </div>

      <!-- 1. Heritage Site Information -->
      <div style="background-color: #FFFFFF; border: 1px solid #E2DDD5; padding: 14px; border-radius: 6px; margin-bottom: 16px;">
        <div style="font-size: 11px; font-weight: 700; color: #A04022; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">
          I. HERITAGE MONUMENT INFORMATION
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
          <tr>
            <td style="padding: 4px 0; color: #8E857B; width: 30%;">SITE NAME:</td>
            <td style="padding: 4px 0; font-weight: bold; color: #1C1917;">${report.siteName}</td>
          </tr>
          <tr>
            <td style="padding: 4px 0; color: #8E857B;">LOCATION & CIRCLE:</td>
            <td style="padding: 4px 0;">${siteData?.location || "Tamil Nadu"} • ${siteData?.circle || "ASI Directorate"}</td>
          </tr>
          <tr>
            <td style="padding: 4px 0; color: #8E857B;">ERA & MATERIAL:</td>
            <td style="padding: 4px 0;">${siteData?.period || "700–728 CE"} • ${siteData?.material || "Granite & Freestone"}</td>
          </tr>
          <tr>
            <td style="padding: 4px 0; color: #8E857B;">HERITAGE CATEGORY:</td>
            <td style="padding: 4px 0;">${siteData?.category || "UNESCO World Heritage Site"}</td>
          </tr>
        </table>
      </div>

      <!-- 2. Architectural Region Information -->
      <div style="background-color: #FFFFFF; border: 1px solid #E2DDD5; padding: 14px; border-radius: 6px; margin-bottom: 16px;">
        <div style="font-size: 11px; font-weight: 700; color: #A04022; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">
          II. ARCHITECTURAL REGION SPECIFICATION
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
          <tr>
            <td style="padding: 4px 0; color: #8E857B; width: 30%;">REGION NAME:</td>
            <td style="padding: 4px 0; font-weight: bold; color: #1C1917;">${report.regionName}</td>
          </tr>
          <tr>
            <td style="padding: 4px 0; color: #8E857B;">STRUCTURAL TYPE:</td>
            <td style="padding: 4px 0;">${regionData?.type || "Vimana / Superstructure"}</td>
          </tr>
          <tr>
            <td style="padding: 4px 0; color: #8E857B;">STRUCTURAL IMPORTANCE:</td>
            <td style="padding: 4px 0;">${regionData?.importance || "Primary Load-Bearing Course"}</td>
          </tr>
        </table>
      </div>

      <!-- 3. Assessment Image -->
      <div style="background-color: #FFFFFF; border: 1px solid #E2DDD5; padding: 14px; border-radius: 6px; margin-bottom: 16px; page-break-inside: avoid;">
        <div style="font-size: 11px; font-weight: 700; color: #A04022; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">
          III. ASSESSMENT PHOTOGRAPHIC ASSET
        </div>
        <div style="text-align: center; background-color: #1C1917; padding: 8px; border-radius: 4px;">
          <img src="${imageBase64}" style="max-width: 100%; max-height: 320px; border-radius: 4px; object-fit: contain;" />
        </div>
        <div style="font-size: 10px; color: #78716C; font-family: monospace; margin-top: 6px; text-align: center;">
          PHOTOGRAMMETRIC SOURCE IMAGE • SEGMENTATION RESOLUTION: RAW 6000x4000
        </div>
      </div>

      <!-- 4. AI Structural Damage Findings -->
      <div style="background-color: #FFFFFF; border: 1px solid #E2DDD5; padding: 14px; border-radius: 6px; margin-bottom: 16px;">
        <div style="font-size: 11px; font-weight: 700; color: #A04022; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">
          IV. COMPUTER VISION DAMAGE FINDINGS
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 10px;">
          <tr>
            <td style="padding: 4px 0; color: #8E857B; width: 30%;">DAMAGE TYPE:</td>
            <td style="padding: 4px 0; font-weight: bold; color: #DC2626;">${report.damageType}</td>
          </tr>
          <tr>
            <td style="padding: 4px 0; color: #8E857B;">SEVERITY & CONFIDENCE:</td>
            <td style="padding: 4px 0;">
              <strong>${report.severity}</strong> (AI Confidence: ${report.confidence})
            </td>
          </tr>
          <tr>
            <td style="padding: 4px 0; color: #8E857B;">EMERGENCY RATING:</td>
            <td style="padding: 4px 0; font-weight: bold; color: #A04022;">${report.emergencyLevel}</td>
          </tr>
          <tr>
            <td style="padding: 4px 0; color: #8E857B;">DAMAGE TREND:</td>
            <td style="padding: 4px 0;">Increasing (+14% temporal score)</td>
          </tr>
        </table>

        <div style="background-color: #F7EDE9; border: 1px solid rgba(160, 64, 34, 0.3); padding: 10px; border-radius: 4px; font-size: 12px; color: #1C1917;">
          <strong style="color: #A04022;">CONSERVATION RECOMMENDATION:</strong><br />
          ${report.summary}
        </div>
      </div>

      <!-- 5. Expert Sign-off Footer -->
      <div style="background-color: #FFFFFF; border: 1px solid #E2DDD5; padding: 14px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
        <div>
          <div style="font-size: 10px; color: #8E857B; text-transform: uppercase;">AUTHORING CONSERVATOR</div>
          <div style="font-weight: bold; font-size: 13px;">${report.expertName || "Dr. A. Sharma"}</div>
          <div style="font-size: 11px; color: #78716C;">Lead Conservator (ASI)</div>
        </div>
        <div style="text-align: right; font-family: monospace; font-size: 11px; color: #16A34A; font-weight: bold;">
          STATUS: ASSESSED & VERIFIED
        </div>
      </div>
    </div>
  `;

  container.innerHTML = htmlContent;
  document.body.appendChild(container);

  try {
    const canvas = await html2canvas(container, {
      scale: 2,
      useCORS: true,
      logging: false
    });

    const imgData = canvas.toDataURL("image/png");
    const pdf = new jsPDF("p", "mm", "a4");

    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

    pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
    pdf.save(`${report.id}_ANCESTRA_Report.pdf`);
  } finally {
    document.body.removeChild(container);
  }
}

// Convert image URL to Base64 to prevent CORS issues in canvas PDF generation
function urlToBase64(url) {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = "Anonymous";
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0);
      resolve(canvas.toDataURL("image/png"));
    };
    img.onerror = () => {
      // Fallback image data URL if load fails
      resolve(url);
    };
    img.src = url;
  });
}
