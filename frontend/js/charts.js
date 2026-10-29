/**
 * Brutalist Entropy Visualizer for ExportGuard.
 * Uses strict 5-Color Palette: Paper ground, Ink borders, Cobalt curve, Emerald safe band, Crimson hazard points.
 */

window.renderEntropyChart = function(containerId, profilePoints, anomalies) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  const width = container.clientWidth || 640;
  const height = container.clientHeight || 230;
  const padding = { top: 22, right: 30, bottom: 28, left: 45 };
  
  if (!profilePoints || profilePoints.length === 0) {
    container.innerHTML = `
      <div style="height:100%; display:flex; align-items:center; justify-content:center; color:var(--ink); font-family:var(--font-mono); font-size:12px;">
        NO ENTROPY TELEMETRY AVAILABLE FOR THIS CONTAINER
      </div>
    `;
    return;
  }
  
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  
  // Y-Scale: 0.0 to 8.0 bits/byte
  const yScale = (val) => {
    const clamped = Math.max(0, Math.min(8.0, val));
    return padding.top + plotHeight - (clamped / 8.0) * plotHeight;
  };
  
  // X-Scale: 0 to N points
  const xScale = (idx) => {
    return padding.left + (idx / Math.max(1, profilePoints.length - 1)) * plotWidth;
  };
  
  // Build SVG Path
  let pathD = "";
  profilePoints.forEach((pt, idx) => {
    const x = xScale(idx);
    const y = yScale(pt.entropy);
    if (idx === 0) {
      pathD += `M ${x.toFixed(1)} ${y.toFixed(1)}`;
    } else {
      pathD += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
    }
  });
  
  // Anomaly circles
  let anomalySvg = "";
  if (anomalies && anomalies.length > 0) {
    anomalies.forEach((a) => {
      const matchingIdx = profilePoints.findIndex(p => Math.abs(p.offset - a.offset) < 8192);
      if (matchingIdx >= 0) {
        const ax = xScale(matchingIdx);
        const ay = yScale(a.entropy);
        anomalySvg += `
          <circle cx="${ax.toFixed(1)}" cy="${ay.toFixed(1)}" r="6" fill="#E63946" stroke="#111215" stroke-width="2">
            <title>${a.type}: ${a.detail}</title>
          </circle>
        `;
      }
    });
  }
  
  const yNormalMin = yScale(4.0);
  const yNormalMax = yScale(6.0);
  const yZeroZone = yScale(1.0);
  
  const svgHtml = `
    <svg viewBox="0 0 ${width} ${height}" style="width:100%; height:100%;">
      <!-- Structured Text Band (4.0 - 6.0 bits/byte) -->
      <rect x="${padding.left}" y="${yNormalMax}" width="${plotWidth}" height="${yNormalMin - yNormalMax}" fill="rgba(15, 169, 88, 0.12)" stroke="rgba(15, 169, 88, 0.3)" stroke-width="1" />
      
      <!-- Critical Zeroed Block Line (<= 1.0b) -->
      <line x1="${padding.left}" y1="${yZeroZone}" x2="${width - padding.right}" y2="${yZeroZone}" stroke="#E63946" stroke-width="1.5" stroke-dasharray="4,4" />
      
      <!-- Baseline Guides -->
      <line x1="${padding.left}" y1="${yNormalMin}" x2="${width - padding.right}" y2="${yNormalMin}" stroke="rgba(17, 18, 21, 0.2)" stroke-dasharray="2,2" />
      <line x1="${padding.left}" y1="${yNormalMax}" x2="${width - padding.right}" y2="${yNormalMax}" stroke="rgba(17, 18, 21, 0.2)" stroke-dasharray="2,2" />
      
      <!-- Axis Labels in Monospace -->
      <text x="${padding.left - 8}" y="${yScale(8.0) + 4}" fill="#111215" font-size="10" font-family="JetBrains Mono, monospace" font-weight="700" text-anchor="end">8.0b</text>
      <text x="${padding.left - 8}" y="${yScale(5.0) + 4}" fill="#111215" font-size="10" font-family="JetBrains Mono, monospace" font-weight="700" text-anchor="end">5.0b</text>
      <text x="${padding.left - 8}" y="${yScale(2.0) + 4}" fill="#111215" font-size="10" font-family="JetBrains Mono, monospace" font-weight="700" text-anchor="end">2.0b</text>
      <text x="${padding.left - 8}" y="${yScale(0.0) + 4}" fill="#E63946" font-size="10" font-family="JetBrains Mono, monospace" font-weight="700" text-anchor="end">0.0b</text>
      
      <!-- Entropy Curve in Cobalt Blue -->
      <path id="entropy-line-path" d="${pathD}" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
      
      <!-- Anomaly Points in Crimson Hazard -->
      ${anomalySvg}
    </svg>
  `;
  
  container.innerHTML = svgHtml;
  
  const linePath = document.getElementById('entropy-line-path');
  if (window.ExportGuardAnimations) {
    window.ExportGuardAnimations.animateEntropyLine(linePath);
  }
};
