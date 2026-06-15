// ============================================
// TREASURY × GTALK — INTERACTIVE WORKFLOW APP
// ============================================

(function () {
  "use strict";

  // === NAVIGATION ===
  const navBtns = document.querySelectorAll(".nav-btn");
  const sections = document.querySelectorAll(".section");
  const backBtns = document.querySelectorAll(".back-btn");
  const usecaseCards = document.querySelectorAll(".usecase-card");

  function showSection(targetId) {
    sections.forEach((s) => {
      s.classList.remove("active");
      s.classList.remove("section-entering");
    });
    navBtns.forEach((b) => b.classList.remove("active"));

    const target = document.getElementById("section-" + targetId);
    if (target) {
      target.classList.add("active");
      // Trigger entrance animation
      requestAnimationFrame(() => {
        target.classList.add("section-entering");
      });

      // Activate nav btn
      const navBtn = document.querySelector(
        `.nav-btn[data-section="${targetId}"]`
      );
      if (navBtn) navBtn.classList.add("active");

      // Scroll to top
      window.scrollTo({ top: 0, behavior: "smooth" });

      // Trigger step animations for flow sections
      if (targetId.startsWith("flow-")) {
        triggerFlowAnimations(target);
      }
    }
  }

  navBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      showSection(btn.dataset.section);
    });
  });

  backBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      showSection(btn.dataset.target);
    });
  });

  usecaseCards.forEach((card) => {
    card.addEventListener("click", () => {
      showSection(card.dataset.target);
    });
  });

  // === FLOW STEP ANIMATIONS ===
  function triggerFlowAnimations(section) {
    const steps = section.querySelectorAll(".flow-step");
    steps.forEach((step, i) => {
      step.classList.remove("step-visible");
      setTimeout(() => {
        step.classList.add("step-visible");
      }, 150 + i * 200);
    });
  }

  // Trigger initial section animations
  const overviewSection = document.getElementById("section-overview");
  if (overviewSection) {
    requestAnimationFrame(() => {
      overviewSection.classList.add("section-entering");
    });
  }

  // === USE CASE CARD ENTRANCE ANIMATION ===
  const ucCards = document.querySelectorAll(".usecase-card");
  ucCards.forEach((card, i) => {
    card.style.opacity = "0";
    card.style.transform = "translateY(30px)";
    setTimeout(() => {
      card.style.transition = "opacity 0.6s ease, transform 0.6s ease";
      card.style.opacity = "1";
      card.style.transform = "translateY(0)";
    }, 300 + i * 150);
  });

  // === STATS BAR COUNTER ANIMATION ===
  function animateCounter(el, target, duration) {
    const isInfinity = target === "∞";
    if (isInfinity) {
      el.textContent = "∞";
      return;
    }
    const numTarget = parseInt(target);
    const startTime = performance.now();

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(numTarget * eased);
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }

  const statValues = document.querySelectorAll(".stat-value");
  statValues.forEach((sv) => {
    const original = sv.textContent;
    setTimeout(() => {
      animateCounter(sv, original, 1500);
    }, 800);
  });

  // === HLD DIAGRAM — Draw Lines ===
  function drawHLDLines() {
    const canvas = document.getElementById("hld-canvas");
    const svg = document.getElementById("hld-lines");
    if (!canvas || !svg) return;

    const nodes = {
      treasury: document.getElementById("hld-treasury"),
      engine: document.getElementById("hld-engine"),
      gtalk: document.getElementById("hld-gtalk"),
      users: document.getElementById("hld-users"),
    };

    if (!nodes.treasury || !nodes.engine || !nodes.gtalk || !nodes.users)
      return;

    const canvasRect = canvas.getBoundingClientRect();

    function getCenter(el) {
      const r = el.getBoundingClientRect();
      return {
        x: r.left - canvasRect.left + r.width / 2,
        y: r.top - canvasRect.top + r.height / 2,
      };
    }

    const t = getCenter(nodes.treasury);
    const e = getCenter(nodes.engine);
    const g = getCenter(nodes.gtalk);
    const u = getCenter(nodes.users);

    // Update SVG viewBox to match actual canvas size
    svg.setAttribute(
      "viewBox",
      `0 0 ${canvasRect.width} ${canvasRect.height}`
    );

    // Draw curved lines
    svg.innerHTML = `
      <defs>
        <linearGradient id="lg1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#60a5fa" stop-opacity="0.8"/>
          <stop offset="100%" stop-color="#a78bfa" stop-opacity="0.8"/>
        </linearGradient>
        <linearGradient id="lg2" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#a78bfa" stop-opacity="0.8"/>
          <stop offset="100%" stop-color="#34d399" stop-opacity="0.8"/>
        </linearGradient>
        <linearGradient id="lg3" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#34d399" stop-opacity="0.8"/>
          <stop offset="100%" stop-color="#fb923c" stop-opacity="0.8"/>
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="blur"/>
          <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      <!-- Treasury → Engine -->
      <line x1="${t.x + 60}" y1="${t.y}" x2="${e.x - 60}" y2="${e.y}"
        stroke="url(#lg1)" stroke-width="2.5" stroke-dasharray="8 4" filter="url(#glow)">
        <animate attributeName="stroke-dashoffset" from="0" to="-24" dur="2s" repeatCount="indefinite"/>
      </line>

      <!-- Engine → GTalk -->
      <line x1="${e.x + 60}" y1="${e.y}" x2="${g.x - 60}" y2="${g.y}"
        stroke="url(#lg2)" stroke-width="2.5" stroke-dasharray="8 4" filter="url(#glow)">
        <animate attributeName="stroke-dashoffset" from="0" to="-24" dur="2s" repeatCount="indefinite"/>
      </line>

      <!-- GTalk → Users -->
      <line x1="${g.x + 60}" y1="${g.y}" x2="${u.x - 60}" y2="${u.y}"
        stroke="url(#lg3)" stroke-width="2.5" stroke-dasharray="8 4" filter="url(#glow)">
        <animate attributeName="stroke-dashoffset" from="0" to="-24" dur="2s" repeatCount="indefinite"/>
      </line>

      <!-- Arrow heads -->
      <polygon points="${e.x - 60},${e.y} ${e.x - 70},${e.y - 6} ${e.x - 70},${e.y + 6}" fill="#a78bfa" opacity="0.9"/>
      <polygon points="${g.x - 60},${g.y} ${g.x - 70},${g.y - 6} ${g.x - 70},${g.y + 6}" fill="#34d399" opacity="0.9"/>
      <polygon points="${u.x - 60},${u.y} ${u.x - 70},${u.y - 6} ${u.x - 70},${u.y + 6}" fill="#fb923c" opacity="0.9"/>
    `;

    // Position flow labels
    const label1 = document.getElementById("flow-label-1");
    const label2 = document.getElementById("flow-label-2");
    const label3 = document.getElementById("flow-label-3");

    if (label1) {
      label1.style.left = (t.x + e.x) / 2 + "px";
      label1.style.top = t.y - 35 + "px";
    }
    if (label2) {
      label2.style.left = (e.x + g.x) / 2 + "px";
      label2.style.top = e.y - 35 + "px";
    }
    if (label3) {
      label3.style.left = (g.x + u.x) / 2 + "px";
      label3.style.top = g.y - 35 + "px";
    }
  }

  // Draw lines after layout settles
  setTimeout(drawHLDLines, 500);
  window.addEventListener("resize", drawHLDLines);

  // === UPLOAD PIPELINE ANIMATION ===
  function animateUploadPipeline() {
    const stages = document.querySelectorAll(".upload-stage");
    const arrows = document.querySelectorAll(".upload-arrow");

    stages.forEach((s) => s.classList.remove("upload-active"));
    arrows.forEach((a) => a.classList.remove("upload-arrow-active"));

    let step = 0;
    function nextStep() {
      if (step < stages.length) {
        stages[step].classList.add("upload-active");
        if (step > 0 && arrows[step - 1]) {
          arrows[step - 1].classList.add("upload-arrow-active");
        }
        step++;
        setTimeout(nextStep, 800);
      } else {
        // Reset after a pause
        setTimeout(() => {
          stages.forEach((s) => s.classList.remove("upload-active"));
          arrows.forEach((a) => a.classList.remove("upload-arrow-active"));
          step = 0;
          setTimeout(nextStep, 500);
        }, 2000);
      }
    }

    // Only run when file section is visible
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            nextStep();
            observer.disconnect();
          }
        });
      },
      { threshold: 0.3 }
    );

    const pipeline = document.getElementById("upload-pipeline");
    if (pipeline) observer.observe(pipeline);
  }

  // Start upload animation when file flow is shown
  navBtns.forEach((btn) => {
    if (btn.dataset.section === "flow-file") {
      btn.addEventListener("click", () => {
        setTimeout(animateUploadPipeline, 500);
      });
    }
  });

  const fileCard = document.querySelector(
    '.usecase-card[data-target="flow-file"]'
  );
  if (fileCard) {
    fileCard.addEventListener("click", () => {
      setTimeout(animateUploadPipeline, 500);
    });
  }

  // === TRIGGER OPTIONS (File flow) ===
  const triggerOpts = document.querySelectorAll(".trigger-opt");
  triggerOpts.forEach((opt) => {
    opt.addEventListener("click", () => {
      triggerOpts.forEach((o) => o.classList.remove("active"));
      opt.classList.add("active");
    });
  });

  // === INTERSECTION OBSERVER for generic entrance animations ===
  const observeTargets = document.querySelectorAll(
    ".api-reference, .tech-stack, .env-config, .commands-panel, .stats-bar"
  );
  const entryObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("revealed");
        }
      });
    },
    { threshold: 0.15 }
  );

  observeTargets.forEach((t) => entryObserver.observe(t));

  // === API TABLE ROW HOVER EFFECTS ===
  const apiRows = document.querySelectorAll(".api-row");
  apiRows.forEach((row) => {
    row.addEventListener("mouseenter", () => {
      row.classList.add("api-row-hover");
    });
    row.addEventListener("mouseleave", () => {
      row.classList.remove("api-row-hover");
    });
  });

  // === TYPING INDICATOR ANIMATION (via CSS keyframes, but we ensure it starts) ===
  // Already handled by CSS, just need to ensure visibility

  // === SMOOTH SCROLL for hash links ===
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      const target = document.querySelector(a.getAttribute("href"));
      if (target) {
        target.scrollIntoView({ behavior: "smooth" });
      }
    });
  });

  // === KEYBOARD NAVIGATION ===
  document.addEventListener("keydown", (e) => {
    // Escape goes back to overview
    if (e.key === "Escape") {
      showSection("overview");
    }
    // Number keys 1-4 switch sections
    if (e.key === "1") showSection("overview");
    if (e.key === "2") showSection("flow-daily");
    if (e.key === "3") showSection("flow-chatbot");
    if (e.key === "4") showSection("flow-file");
    if (e.key === "5") showSection("architecture");
  });

  // === PARALLAX ON AMBIENT ORBS ===
  document.addEventListener("mousemove", (e) => {
    const orbs = document.querySelectorAll(".ambient-orb");
    const x = (e.clientX / window.innerWidth - 0.5) * 2;
    const y = (e.clientY / window.innerHeight - 0.5) * 2;

    orbs.forEach((orb, i) => {
      const factor = (i + 1) * 8;
      orb.style.transform = `translate(${x * factor}px, ${y * factor}px)`;
    });
  });

  // === HLD NODE HOVER TOOLTIPS ===
  const hldNodes = document.querySelectorAll(".hld-node");
  hldNodes.forEach((node) => {
    node.addEventListener("mouseenter", () => {
      node.classList.add("hld-node-hover");
    });
    node.addEventListener("mouseleave", () => {
      node.classList.remove("hld-node-hover");
    });
  });

  console.log(
    "%c Treasury × GTalk Workflow %c Loaded ",
    "background: linear-gradient(90deg, #60a5fa, #a78bfa); color: white; padding: 4px 8px; border-radius: 4px 0 0 4px; font-weight: bold;",
    "background: #141b2d; color: #34d399; padding: 4px 8px; border-radius: 0 4px 4px 0;"
  );
})();
