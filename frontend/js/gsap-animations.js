/**
 * GSAP Kinetic Animation Controller for ExportGuard (Mechay-Inspired)
 */

window.ExportGuardAnimations = {
  // 1. Gate Opening Sequence & Counter
  initGateSequence: function() {
    if (typeof gsap === 'undefined') return;
    const counterEl = document.getElementById('gate-counter');
    const gateEl = document.getElementById('gate-curtain');
    const enterBtn = document.getElementById('btn-gate-enter');
    
    if (!counterEl || !gateEl) return;

    // Fast numeric counter 000 -> 100
    const counterObj = { val: 0 };
    gsap.to(counterObj, {
      val: 100,
      duration: 1.0,
      ease: 'power2.out',
      onUpdate: function() {
        const intVal = Math.round(counterObj.val);
        counterEl.textContent = intVal < 10 ? `00${intVal}` : intVal < 100 ? `0${intVal}` : '100';
      }
    });

    // Enter trigger
    const unlockGate = () => {
      gsap.to(gateEl, {
        yPercent: -100,
        duration: 0.7,
        ease: 'power4.inOut',
        onComplete: () => {
          gateEl.classList.add('gate-unlocked');
        }
      });
    };

    if (enterBtn) {
      enterBtn.addEventListener('click', unlockGate);
    }
  },

  // 2. Elastic Verdict Certificate Stamp
  animateVerdictStamp: function(severity) {
    if (typeof gsap === 'undefined') return;
    const banner = document.getElementById('verdict-banner');
    if (!banner) return;
    
    gsap.fromTo(banner, 
      { scale: 0.94, opacity: 0, y: -10 },
      { 
        scale: 1, 
        opacity: 1, 
        y: 0, 
        duration: 0.45, 
        ease: 'elastic.out(1, 0.75)' 
      }
    );
  },

  // 3. Brutalist Metric Brick Numbers
  animateMetrics: function() {
    if (typeof gsap === 'undefined') return;
    const elements = document.querySelectorAll('.animate-number');
    
    elements.forEach((el, index) => {
      const targetVal = parseFloat(el.getAttribute('data-value') || '0');
      const isDecimal = targetVal % 1 !== 0;
      
      const counter = { val: Math.round(targetVal * 0.9) };
      gsap.to(counter, {
        val: targetVal,
        duration: 0.2,
        ease: 'power2.out',
        onUpdate: function() {
          if (isDecimal) {
            el.textContent = counter.val.toFixed(2);
          } else {
            el.textContent = Math.round(counter.val).toLocaleString();
          }
        },
        onComplete: function() {
          if (isDecimal) {
            el.textContent = targetVal.toFixed(2);
          } else {
            el.textContent = Math.round(targetVal).toLocaleString();
          }
        }
      });
    });
  },

  // 4. Staggered Pipeline Bricks
  animatePipelineBricks: function() {
    if (typeof gsap === 'undefined') return;
    gsap.fromTo('.tier-brick',
      { opacity: 0.4, y: 8 },
      { opacity: 1, y: 0, stagger: 0.05, duration: 0.3, ease: 'power2.out' }
    );
  },

  // 5. SVG Line Draw for Entropy Chart
  animateEntropyLine: function(pathElement) {
    if (typeof gsap === 'undefined' || !pathElement) return;
    const length = pathElement.getTotalLength();
    if (!length) return;
    
    gsap.fromTo(pathElement,
      { strokeDasharray: length, strokeDashoffset: length },
      { strokeDashoffset: 0, duration: 0.6, ease: 'power2.out' }
    );
  },

  // 6. Pull-Ticket Receipt Unfold Animation
  openReceiptModal: function() {
    const modal = document.getElementById('receipt-modal');
    const paper = document.querySelector('.receipt-paper');
    if (!modal || !paper) return;
    
    modal.classList.add('open');
    if (typeof gsap !== 'undefined') {
      gsap.fromTo(paper,
        { y: -20, scale: 0.98, opacity: 1 },
        { y: 0, scale: 1, opacity: 1, duration: 0.2, ease: 'power2.out' }
      );
    }
  },

  closeReceiptModal: function() {
    const modal = document.getElementById('receipt-modal');
    const paper = document.querySelector('.receipt-paper');
    if (!modal || !paper) return;
    
    if (typeof gsap !== 'undefined') {
      gsap.to(paper, {
        y: -30,
        opacity: 0,
        duration: 0.15,
        ease: 'power2.in',
        onComplete: () => {
          modal.classList.remove('open');
        }
      });
    } else {
      modal.classList.remove('open');
    }
  }
};
