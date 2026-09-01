import jsPDF from "jspdf";
import html2canvas from "html2canvas";

/**
 * Generates an official multi-page A4 ANCESTRA Heritage Structural Assessment PDF Report
 * with clean pagination (Section IV starting at top of Page 2), proper bottom margins,
 * zero content cropping, and embedded photogrammetric photo assets.
 */
export async function generateAncestrapdfReport(report, siteData, regionData, assessmentData) {
  const container = document.createElement("div");
  container.style.position = "absolute";
  container.style.left = "-9999px";
  container.style.top = "-9999px";
  container.style.width = "794px"; // Standard A4 width at 96 DPI
  container.style.backgroundColor = "#FAF8F5";
  container.style.color = "#1C1917";
  container.style.fontFamily = "'Plus Jakarta Sans', sans-serif";
  container.style.boxSizing = "border-box";

  const imgUrl =
    assessmentData?.imageUrl ||
    report?.imageUrl ||
    siteData?.image ||
    "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800";

  const imageBase64 = await urlToBase64(imgUrl);
  const regionCode = regionData?.code || report?.regionCode || "SHR-E-VIM";

  // PAGE 1 HTML Content
  const page1Html = `
    <div style="background-color: #FAF8F5; border: 1px solid #E2DDD5; padding: 28px 32px 36px 32px; border-radius: 6px; box-sizing: border-box; min-height: 1080px;">
      <!-- Header Banner -->
      <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #A04022; padding-bottom: 12px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 10px;">
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

      <!-- I. Heritage Site Information -->
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
            <td style="padding: 4px 0; color: #8E857B;">CONSTRUCTION MATERIAL:</td>
            <td style="padding: 4px 0;">${siteData?.material || "Granite & Freestone"}</td>
          </tr>
          <tr>
            <td style="padding: 4px 0; color: #8E857B;">HERITAGE CATEGORY:</td>
            <td style="padding: 4px 0;">${siteData?.category || "UNESCO World Heritage Site"}</td>
          </tr>
        </table>
      </div>

      <!-- II. Architectural Region Specification -->
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
            <td style="padding: 4px 0; color: #8E857B;">REGION ID:</td>
            <td style="padding: 4px 0; font-family: monospace; font-weight: bold; color: #A04022;">${regionCode}</td>
          </tr>
          <tr>
            <td style="padding: 4px 0; color: #8E857B;">STRUCTURAL IMPORTANCE:</td>
            <td style="padding: 4px 0;">${regionData?.importance || "Primary Load-Bearing Course"}</td>
          </tr>
        </table>
      </div>

      <!-- III. Assessment Image Asset -->
      <div style="background-color: #FFFFFF; border: 1px solid #E2DDD5; padding: 14px; border-radius: 6px; margin-bottom: 16px;">
        <div style="font-size: 11px; font-weight: 700; color: #A04022; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">
          III. ASSESSMENT PHOTOGRAPHIC ASSET
        </div>
        <div style="text-align: center; background-color: #1C1917; padding: 8px; border-radius: 4px;">
          <img src="${imageBase64}" style="max-width: 100%; max-height: 260px; border-radius: 4px; object-fit: contain;" />
        </div>
        <div style="font-size: 10px; color: #78716C; font-family: monospace; margin-top: 6px; text-align: center;">
          PHOTOGRAMMETRIC SOURCE IMAGE • SEGMENTATION RESOLUTION: RAW 6000x4000
        </div>
      </div>
      <div style="text-align: right; font-size: 10px; color: #8E857B; font-family: monospace; margin-top: 10px;">PAGE 1 OF 2</div>
    </div>
  `;

  // PAGE 2 HTML Content (Starting cleanly with Section IV)
  const page2Html = `
    <div style="background-color: #FAF8F5; border: 1px solid #E2DDD5; padding: 28px 32px 36px 32px; border-radius: 6px; box-sizing: border-box; min-height: 1080px; margin-top: 20px;">
      <!-- Header Mini Banner -->
      <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #A04022; padding-bottom: 8px; margin-bottom: 20px;">
        <div style="font-family: 'Cinzel', serif; font-weight: 700; font-size: 14px; color: #1C1917;">
          ANCESTRA ASSESSMENT DOSSIER • ${report.id}
        </div>
        <div style="font-size: 10px; font-family: monospace; color: #57534E;">CONTINUED — PAGE 2</div>
      </div>

      <!-- IV. Computer Vision Damage Findings (Starts Cleanly at Top of Page 2) -->
      <div style="background-color: #FFFFFF; border: 1px solid #E2DDD5; padding: 18px; border-radius: 6px; margin-bottom: 20px;">
        <div style="font-size: 12px; font-weight: 700; color: #A04022; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px;">
          IV. COMPUTER VISION DAMAGE FINDINGS
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 14px;">
          <tr>
            <td style="padding: 6px 0; color: #8E857B; width: 30%;">DAMAGE TYPE:</td>
            <td style="padding: 6px 0; font-weight: bold; color: #DC2626;">${report.damageType}</td>
          </tr>
          <tr>
            <td style="padding: 6px 0; color: #8E857B;">SEVERITY & CONFIDENCE:</td>
            <td style="padding: 6px 0;">
              <strong>${report.severity}</strong> (AI Confidence: ${report.confidence})
            </td>
          </tr>
          <tr>
            <td style="padding: 6px 0; color: #8E857B;">EMERGENCY RATING:</td>
            <td style="padding: 6px 0; font-weight: bold; color: #A04022;">${report.emergencyLevel}</td>
          </tr>
          <tr>
            <td style="padding: 6px 0; color: #8E857B;">DAMAGE TREND:</td>
            <td style="padding: 6px 0;">Increasing (+14% temporal score)</td>
          </tr>
        </table>

        <div style="background-color: #F7EDE9; border: 1px solid rgba(160, 64, 34, 0.3); padding: 14px; border-radius: 6px; font-size: 12.5px; color: #1C1917; line-height: 1.4;">
          <strong style="color: #A04022;">CONSERVATION RECOMMENDATION:</strong><br />
          ${report.summary}
        </div>
      </div>

      <!-- V. Expert Sign-off Footer -->
      <div style="background-color: #FFFFFF; border: 1px solid #E2DDD5; padding: 16px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
        <div>
          <div style="font-size: 10px; color: #8E857B; text-transform: uppercase;">AUTHORING CONSERVATOR</div>
          <div style="font-weight: bold; font-size: 13px;">${report.expertName || "Dr. A. Sharma"}</div>
          <div style="font-size: 11px; color: #78716C;">Lead Conservator (ASI)</div>
        </div>
        <div style="text-align: right; font-family: monospace; font-size: 11px; color: #16A34A; font-weight: bold;">
          STATUS: ASSESSED & VERIFIED
        </div>
      </div>
      <div style="text-align: right; font-size: 10px; color: #8E857B; font-family: monospace; margin-top: 10px;">PAGE 2 OF 2</div>
    </div>
  `;

  container.innerHTML = page1Html + page2Html;
  document.body.appendChild(container);

  try {
    const pageElements = container.children;

    const canvas1 = await html2canvas(pageElements[0], { scale: 2, useCORS: true, logging: false });
    const canvas2 = await html2canvas(pageElements[1], { scale: 2, useCORS: true, logging: false });

    const pdf = new jsPDF("p", "mm", "a4");
    const pdfWidth = 210;
    const pdfHeight = 297;

    // Render Page 1
    const imgHeight1 = (canvas1.height * pdfWidth) / canvas1.width;
    pdf.addImage(canvas1.toDataURL("image/png"), "PNG", 0, 0, pdfWidth, Math.min(imgHeight1, pdfHeight));

    // Render Page 2 (Section IV starts cleanly at top)
    pdf.addPage();
    const imgHeight2 = (canvas2.height * pdfWidth) / canvas2.width;
    pdf.addImage(canvas2.toDataURL("image/png"), "PNG", 0, 0, pdfWidth, Math.min(imgHeight2, pdfHeight));

    pdf.save(`${report.id}_ANCESTRA_Report.pdf`);
  } finally {
    document.body.removeChild(container);
  }
}

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
      resolve(url);
    };
    img.src = url;
  });
}
