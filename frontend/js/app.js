/**
 * Main Frontend Application Controller for ExportGuard (Mechay Theme)
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Gate Sequence
  const urlParams = new URLSearchParams(window.location.search);
  const skipGate = urlParams.get('skip_gate') === 'true';
  const initialScenario = urlParams.get('scenario') || 'high_compression';
  const openReceipt = urlParams.get('receipt') === 'open';

  const gateEl = document.getElementById('gate-curtain');
  if (skipGate && gateEl) {
    gateEl.classList.add('gate-unlocked');
  } else if (window.ExportGuardAnimations) {
    window.ExportGuardAnimations.initGateSequence();
  }

  // Highlight active scenario button
  document.querySelectorAll('.btn-scenario').forEach(b => {
    if (b.getAttribute('data-scenario') === initialScenario) {
      b.classList.add('active');
    } else {
      b.classList.remove('active');
    }
  });

  loadScenario(initialScenario);
  setupEventListeners();

  if (openReceipt && window.ExportGuardAnimations) {
    window.ExportGuardAnimations.openReceiptModal();
  }
});

function setupEventListeners() {
  // Scenario button toggles
  document.querySelectorAll('.btn-scenario').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-scenario').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const scenario = btn.getAttribute('data-scenario');
      loadScenario(scenario);
    });
  });

  // Pull-ticket button (opens receipt modal)
  const pullTicketBtn = document.getElementById('pull-ticket-btn');
  if (pullTicketBtn && window.ExportGuardAnimations) {
    pullTicketBtn.addEventListener('click', () => {
      window.ExportGuardAnimations.openReceiptModal();
    });
  }

  // Close receipt modal
  const closeReceiptBtn = document.getElementById('btn-close-receipt');
  if (closeReceiptBtn && window.ExportGuardAnimations) {
    closeReceiptBtn.addEventListener('click', () => {
      window.ExportGuardAnimations.closeReceiptModal();
    });
  }

  const receiptModal = document.getElementById('receipt-modal');
  if (receiptModal && window.ExportGuardAnimations) {
    receiptModal.addEventListener('click', (e) => {
      if (e.target === receiptModal) {
        window.ExportGuardAnimations.closeReceiptModal();
      }
    });
  }

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && window.ExportGuardAnimations) {
      window.ExportGuardAnimations.closeReceiptModal();
    }
  });

  // Custom upload form & brutalist file pickers
  const fileExportInput = document.getElementById('file-export') || document.getElementById('upload-export-file');
  const btnBrowseExport = document.getElementById('btn-browse-export');
  const fileExportName = document.getElementById('file-export-name');
  const pickerExport = document.getElementById('picker-export');

  if (btnBrowseExport && fileExportInput) {
    btnBrowseExport.addEventListener('click', (e) => {
      e.preventDefault();
      fileExportInput.click();
    });
  }

  if (fileExportInput && fileExportName) {
    fileExportInput.addEventListener('change', () => {
      if (fileExportInput.files.length) {
        const file = fileExportInput.files[0];
        const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
        fileExportName.textContent = `✓ ${file.name} (${sizeMB} MB)`;
        fileExportName.classList.add('selected');
        if (pickerExport) pickerExport.classList.add('has-file');
      } else {
        fileExportName.textContent = 'NO FILE CHOSEN';
        fileExportName.classList.remove('selected');
        if (pickerExport) pickerExport.classList.remove('has-file');
      }
    });
  }

  const fileLogInput = document.getElementById('file-log') || document.getElementById('upload-log-file');
  const btnBrowseLog = document.getElementById('btn-browse-log');
  const fileLogName = document.getElementById('file-log-name');
  const pickerLog = document.getElementById('picker-log');

  if (btnBrowseLog && fileLogInput) {
    btnBrowseLog.addEventListener('click', (e) => {
      e.preventDefault();
      fileLogInput.click();
    });
  }

  if (fileLogInput && fileLogName) {
    fileLogInput.addEventListener('change', () => {
      if (fileLogInput.files.length) {
        const file = fileLogInput.files[0];
        fileLogName.textContent = `✓ ${file.name}`;
        fileLogName.classList.add('selected');
        if (pickerLog) pickerLog.classList.add('has-file');
      } else {
        fileLogName.textContent = 'NO FILE CHOSEN';
        fileLogName.classList.remove('selected');
        if (pickerLog) pickerLog.classList.remove('has-file');
      }
    });
  }

  const uploadForm = document.getElementById('upload-form');
  if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const exportFileInput = document.getElementById('file-export') || document.getElementById('upload-export-file');
      const logFileInput = document.getElementById('file-log') || document.getElementById('upload-log-file');
      
      if (!exportFileInput || !exportFileInput.files.length) {
        alert("Please select a .gz export file to analyze.");
        return;
      }
      
      const formData = new FormData();
      formData.append('export_file', exportFileInput.files[0]);
      if (logFileInput && logFileInput.files.length) {
        formData.append('log_file', logFileInput.files[0]);
      }
      
      try {
        setLoadingState(true);
        const res = await fetch('/api/analyze', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        renderReport(data);
      } catch (err) {
        alert("Analysis error: " + err.message);
      } finally {
        setLoadingState(false);
      }
    });
  }
}

async function loadScenario(scenarioName) {
  try {
    setLoadingState(true);
    const res = await fetch(`/api/demo/${scenarioName}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    renderReport(data);
  } catch (err) {
    console.error("Failed to load scenario:", err);
  } finally {
    setLoadingState(false);
  }
}

function setLoadingState(loading) {
  const banner = document.getElementById('verdict-banner');
  if (loading && banner) {
    banner.style.opacity = '0.6';
  } else if (banner) {
    banner.style.opacity = '1';
  }
}

function renderReport(report) {
  // 1. Verdict Certificate Banner
  const banner = document.getElementById('verdict-banner');
  const isIntact = (report.verdict === 'INTACT');
  banner.className = `certificate-card ${isIntact ? 'cert-intact' : 'cert-corrupted'}`;
  
  const stampTitle = document.getElementById('verdict-status-title');
  stampTitle.textContent = report.verdict;
  stampTitle.style.color = isIntact ? 'var(--signal-safe)' : 'var(--signal-warn)';
  
  document.getElementById('verdict-summary').textContent = report.verdict_summary;
  document.getElementById('verdict-explanation').textContent = report.root_cause_explanation;
  document.getElementById('verdict-job-id').textContent = `AUDIT-ID: ${report.job_id} // FILE: ${report.export_filename}`;

  // 2. Metrics Grid
  const currRows = report.tier2 ? report.tier2.streaming_row_count : (report.tier1.log_parser ? report.tier1.log_parser.total_rows : 0);
  const anomaly = report.tier1.anomaly_scorer;
  
  const elRows = document.getElementById('metric-rows');
  elRows.textContent = currRows.toLocaleString();
  elRows.setAttribute('data-value', currRows);
  document.getElementById('metric-rows-delta').textContent = `${anomaly.row_growth_pct > 0 ? '+' : ''}${anomaly.row_growth_pct}%`;
  document.getElementById('metric-rows-delta').className = `brick-badge ${anomaly.row_growth_pct > 0 ? 'badge-emerald' : 'badge-crimson'}`;
  
  const compSizeMB = (report.tier1.gzip_container.file_size_bytes / (1024 * 1024)).toFixed(2);
  const elSize = document.getElementById('metric-size');
  elSize.textContent = compSizeMB;
  elSize.setAttribute('data-value', compSizeMB);
  document.getElementById('metric-size-delta').textContent = `${anomaly.size_growth_pct}%`;
  
  const bytesPerRow = anomaly.curr_bytes_per_row || ((report.tier1.gzip_container.file_size_bytes / Math.max(1, currRows)).toFixed(1));
  const elBPR = document.getElementById('metric-bpr');
  elBPR.textContent = typeof bytesPerRow === 'number' ? bytesPerRow.toFixed(2) : bytesPerRow;
  elBPR.setAttribute('data-value', bytesPerRow);
  
  const elScore = document.getElementById('metric-score');
  elScore.textContent = anomaly.anomaly_score;
  elScore.setAttribute('data-value', anomaly.anomaly_score);
  
  // 3. Pipeline Tier Cards
  const t1 = report.tier1;
  const pillT1 = document.getElementById('tier1-pill');
  pillT1.textContent = t1.passed ? 'PASS' : 'FAIL';
  pillT1.className = `tier-status-stamp ${t1.passed ? 'pass' : 'fail'}`;
  
  const t1Sentinel = document.getElementById('t1-sentinel');
  t1Sentinel.textContent = t1.sentinel_check.passed ? 'Verified Intact' : 'MISSING (TRUNCATED)';
  t1Sentinel.style.color = t1.sentinel_check.passed ? 'var(--signal-safe)' : 'var(--signal-warn)';
  
  const elT1Container = document.getElementById('t1-gzip') || document.getElementById('t1-container');
  if (elT1Container) {
    elT1Container.textContent = t1.gzip_container.gzip_t_passed ? `RFC 1952 OK (${t1.gzip_container.stored_crc32})` : 'CRC CORRUPT';
  }
  
  const elT14gb = document.getElementById('t1-isize') || document.getElementById('t1-4gb');
  if (elT14gb) {
    elT14gb.textContent = t1.gzip_container.isize_wrapped_4gb ? 'Wrapped (>4GB ISIZE)' : 'Normal (< 4GB)';
  }
  
  const elT1Log = document.getElementById('t1-log');
  if (elT1Log) {
    elT1Log.textContent = (t1.log_parser && t1.log_parser.provided) 
      ? (t1.log_parser.completed_cleanly ? 'Job Clean (0 Errors)' : 'Errors Logged') : 'Not Provided';
  }

  // Tier 2
  const t2 = report.tier2;
  const pillT2 = document.getElementById('tier2-pill');
  if (t2) {
    pillT2.textContent = t2.passed ? 'PASS' : 'FAIL';
    pillT2.className = `tier-status-stamp ${t2.passed ? 'pass' : 'fail'}`;
    document.getElementById('t2-rows').textContent = `${t2.streaming_row_count.toLocaleString()} rows`;
    document.getElementById('t2-schema').textContent = t2.header_fingerprint.slice(0, 14) + '...';
    document.getElementById('t2-boundary').textContent = t2.boundary_validation.last_row_matches_header_width ? 'Complete Fields' : 'Field Truncated';
    document.getElementById('t2-xor').textContent = t2.calculated_xor_checksum;
  } else {
    pillT2.textContent = 'SKIPPED';
    pillT2.className = 'tier-status-stamp fail';
    document.getElementById('t2-rows').textContent = 'N/A';
    document.getElementById('t2-schema').textContent = 'N/A';
    document.getElementById('t2-boundary').textContent = 'N/A';
    document.getElementById('t2-xor').textContent = 'N/A';
  }

  // Tier 3
  const t3 = report.tier3;
  const pillT3 = document.getElementById('tier3-pill');
  if (t3) {
    pillT3.textContent = t3.passed ? 'PASS' : 'ANOMALY';
    pillT3.className = `tier-status-stamp ${t3.passed ? 'pass' : 'fail'}`;
    document.getElementById('t3-entropy').textContent = `${t3.entropy_analysis.average_entropy} b/byte`;
    document.getElementById('t3-anomalies').textContent = `${t3.entropy_analysis.anomalies_detected} flagged`;
    document.getElementById('t3-merkle').textContent = t3.block_merkle_verification.merkle_root.slice(0, 14) + '...';
  } else {
    pillT3.textContent = 'SKIPPED';
    pillT3.className = 'tier-status-stamp fail';
    document.getElementById('t3-entropy').textContent = 'N/A';
    document.getElementById('t3-anomalies').textContent = 'N/A';
    document.getElementById('t3-merkle').textContent = 'N/A';
  }

  // 4. Render Entropy Chart
  if (t3 && window.renderEntropyChart) {
    window.renderEntropyChart(
      'entropy-chart-target',
      t3.entropy_analysis.profile_sample,
      t3.entropy_analysis.anomalies
    );
  }

  // 5. Boundary Terminal Preview
  const boundaryPreview = document.getElementById('boundary-preview');
  if (t2 && t2.boundary_validation) {
    const first3 = t2.boundary_validation.first_sample.join('\n');
    const last3 = t2.boundary_validation.last_sample.join('\n');
    boundaryPreview.textContent = `=== [START OF STREAM: HEADER & FIRST 3 RECORDS] ===\n${first3}\n\n... [${(t2.streaming_row_count - 6).toLocaleString()} INTERMEDIATE ROWS STREAM-VERIFIED] ...\n\n=== [END OF STREAM: LAST 3 RECORDS & SENTINEL] ===\n${last3}`;
  } else {
    boundaryPreview.textContent = "FATAL: Stream decompression halted. RFC 1952 container damaged.";
  }

  // 6. Column Profile Table
  const colTableBody = document.querySelector('#col-profile-table tbody');
  colTableBody.innerHTML = '';
  if (t2 && t2.column_profiles) {
    t2.column_profiles.forEach(col => {
      const tr = document.createElement('tr');
      const isHealthy = (col.status === 'HEALTHY');
      tr.innerHTML = `
        <td style="font-weight:700;">${col.column_name}</td>
        <td>${col.null_percentage}%</td>
        <td>${col.average_char_length} ch</td>
        <td>${col.sampled_distinct_values}</td>
        <td><strong style="color:${isHealthy ? 'var(--signal-safe)' : 'var(--signal-warn)'};">${col.status}</strong></td>
      `;
      colTableBody.appendChild(tr);
    });
  }

  // 7. Statistical Confidence Table
  const confTableBody = document.querySelector('#confidence-table tbody');
  confTableBody.innerHTML = '';
  if (t2 && t2.confidence_metrics && t2.confidence_metrics.detection_matrix) {
    t2.confidence_metrics.detection_matrix.forEach(row => {
      const tr = document.createElement('tr');
      const isHighConf = (row.detection_probability_pct > 95);
      tr.innerHTML = `
        <td>${row.label}</td>
        <td>${row.corruption_rate_pct}%</td>
        <td>${row.expected_corrupted_rows.toLocaleString()}</td>
        <td style="font-weight:700; color:${isHighConf ? 'var(--signal-safe)' : 'var(--signal-warn)'};">${row.detection_probability_pct}%</td>
      `;
      confTableBody.appendChild(tr);
    });
  }

  // 8. Populate Perforated Receipt Modal Data
  document.getElementById('receipt-filename').textContent = report.export_filename;
  document.getElementById('receipt-timestamp').textContent = `UTC: ${report.timestamp.slice(0, 19)}`;
  document.getElementById('receipt-rows').textContent = currRows.toLocaleString();
  document.getElementById('receipt-size').textContent = `${compSizeMB} MB`;
  document.getElementById('receipt-bpr').textContent = `${typeof bytesPerRow === 'number' ? bytesPerRow.toFixed(2) : bytesPerRow} B/row`;
  document.getElementById('receipt-crc').textContent = t1.gzip_container.stored_crc32 || '0x00000000';
  
  const recSentinel = document.getElementById('receipt-sentinel');
  recSentinel.textContent = t1.sentinel_check.passed ? 'VERIFIED INTACT' : 'MISSING / ABORTED';
  recSentinel.style.color = t1.sentinel_check.passed ? 'var(--signal-safe)' : 'var(--signal-warn)';
  
  document.getElementById('receipt-xor').textContent = t2 ? t2.calculated_xor_checksum : 'N/A';
  document.getElementById('receipt-entropy').textContent = t3 ? `${t3.entropy_analysis.average_entropy} bits/byte` : 'N/A';
  
  const recStamp = document.getElementById('receipt-verdict-stamp');
  recStamp.textContent = isIntact ? 'INTACT // CERTIFIED FOR RESTORE' : 'CORRUPTED // DO NOT RESTORE';
  recStamp.style.color = isIntact ? 'var(--signal-safe)' : 'var(--signal-warn)';
  recStamp.style.borderColor = isIntact ? 'var(--signal-safe)' : 'var(--signal-warn)';

  const viewFullReceipt = document.getElementById('receipt-view-full-link');
  if (viewFullReceipt) {
    const activeBtn = document.querySelector('.btn-scenario.active');
    const scn = activeBtn ? activeBtn.getAttribute('data-scenario') : 'high_compression';
    viewFullReceipt.href = `/receipt?scenario=${scn}`;
  }

  // 9. Fire GSAP Animations
  if (window.ExportGuardAnimations) {
    window.ExportGuardAnimations.animateVerdictStamp(report.verdict_severity);
    window.ExportGuardAnimations.animateMetrics();
    window.ExportGuardAnimations.animatePipelineBricks();
  }
}
