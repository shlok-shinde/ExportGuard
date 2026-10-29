/**
 * Landing Page Controller for ExportGuard
 */

document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const skipGate = params.get('skip_gate') === 'true';
  const openReceipt = params.get('receipt') === 'open';

  // Gate Curtain
  const gate = document.getElementById('gate-curtain');
  if (skipGate && gate) {
    gate.style.display = 'none';
  } else if (window.ExportGuardAnimations) {
    window.ExportGuardAnimations.initGateSequence();
  }

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

  if (openReceipt && window.ExportGuardAnimations) {
    window.ExportGuardAnimations.openReceiptModal();
  }
});
