/**
 * Kairos Slide-Over Evidence & Dispute Inspection Drawer (Milestone P4)
 * Owner: Peace (Oluwanifemi)
 *
 * Provides a slide-over modal dialog displaying full side-by-side verbatim
 * quote evidence and open-weight NLI referee explanations whenever any
 * relation edge on the graph or comparison cell in the matrix is clicked.
 */
(function (global) {
  "use strict";

  var SIGNAL_META = {
    AGREE: {
      label: "Agree",
      icon: "✓",
      cssClass: "signal-agree",
      lineClass: "line-solid-agree"
    },
    CONTRADICT: {
      label: "Contradiction",
      icon: "⚠",
      cssClass: "signal-contradict",
      lineClass: "line-solid-contradict"
    },
    METHODOLOGY_DELTA: {
      label: "Methodology difference",
      icon: "≈",
      cssClass: "signal-delta",
      lineClass: "line-dashed-delta"
    },
    RESEARCH_GAP: {
      label: "Research gap",
      icon: "◌",
      cssClass: "signal-gap",
      lineClass: "line-dotted-gap"
    }
  };

  var lastFocusedEl = null;

  function createEl(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined && text !== null) el.textContent = String(text);
    return el;
  }

  function createSignalBadge(signalKey) {
    var meta = SIGNAL_META[signalKey] || SIGNAL_META.AGREE;
    var pill = createEl("span", "signal-pill " + meta.cssClass);
    var icon = createEl("span", "signal-icon", meta.icon);
    icon.setAttribute("aria-hidden", "true");
    var name = createEl("span", "signal-name", meta.label);
    var line = createEl("span", "signal-line-sample " + meta.lineClass);
    line.setAttribute("aria-hidden", "true");

    pill.appendChild(icon);
    pill.appendChild(name);
    pill.appendChild(line);
    return pill;
  }

  function getDrawerElements() {
    return {
      drawer: document.getElementById("drawer-evidence"),
      backdrop: document.getElementById("drawer-backdrop"),
      title: document.getElementById("drawer-title"),
      body: document.getElementById("drawer-body"),
      closeBtn: document.getElementById("drawer-close-btn")
    };
  }

  function open(edge, triggerEl) {
    if (!edge) return;
    lastFocusedEl = triggerEl || document.activeElement;

    var els = getDrawerElements();
    if (!els.drawer || !els.body) return;

    // Set Header
    if (els.title) {
      els.title.textContent = "Dispute & Evidence Inspection";
    }

    // Clear and build Body
    els.body.innerHTML = "";

    // 1. Relation & Confidence Bar
    var relBar = createEl("div", "drawer-relation-bar");
    var badge = createSignalBadge(edge.relation || "CONTRADICT");
    relBar.appendChild(badge);

    var confVal = (edge.confidence !== undefined && edge.confidence !== null)
      ? Math.round(edge.confidence * 100) + "% confidence"
      : "Verified relation";
    var confBadge = createEl("span", "queue-badge", confVal);
    relBar.appendChild(confBadge);

    els.body.appendChild(relBar);

    // 2. Side-by-Side Study Cards
    var comparisonWrapper = createEl("div", "drawer-cards-comparison");

    // Study A (Source)
    var cardA = createEl("article", "drawer-study-card coral");
    var headA = createEl("div", "drawer-study-header");
    headA.appendChild(createEl("span", null, "STUDY A · SOURCE CLAIM"));
    if (edge.source_claim_id) {
      headA.appendChild(createEl("span", "mono-tag", edge.source_claim_id));
    }
    cardA.appendChild(headA);

    var titleA = createEl(
      "h3",
      "drawer-study-title",
      (edge.source && edge.source.paper_title) || "Source Study"
    );
    cardA.appendChild(titleA);

    if (edge.source && edge.source.verbatim_quote) {
      var quoteA = createEl("blockquote", "drawer-study-quote", "“" + edge.source.verbatim_quote + "”");
      var citeA = createEl(
        "div",
        "drawer-study-cite",
        "Section: " + (edge.source.section || "Body") + " · Page: " + (edge.source.page_number || "—")
      );
      cardA.appendChild(quoteA);
      cardA.appendChild(citeA);
    }
    comparisonWrapper.appendChild(cardA);

    // Study B (Target)
    var cardB = createEl("article", "drawer-study-card teal");
    var headB = createEl("div", "drawer-study-header");
    headB.appendChild(createEl("span", null, "STUDY B · TARGET CLAIM"));
    if (edge.target_claim_id) {
      headB.appendChild(createEl("span", "mono-tag", edge.target_claim_id));
    }
    cardB.appendChild(headB);

    var titleB = createEl(
      "h3",
      "drawer-study-title",
      (edge.target && edge.target.paper_title) || "Comparative Study"
    );
    cardB.appendChild(titleB);

    if (edge.target && edge.target.verbatim_quote) {
      var quoteB = createEl("blockquote", "drawer-study-quote", "“" + edge.target.verbatim_quote + "”");
      var citeB = createEl(
        "div",
        "drawer-study-cite",
        "Section: " + (edge.target.section || "Body") + " · Page: " + (edge.target.page_number || "—")
      );
      cardB.appendChild(quoteB);
      cardB.appendChild(citeB);
    }
    comparisonWrapper.appendChild(cardB);

    els.body.appendChild(comparisonWrapper);

    // 3. Open-Weight Referee Analysis Panel
    var refPanel = createEl("div", "drawer-referee-panel");
    var refHead = createEl("div", "drawer-referee-head");
    var refTitle = createEl("h4", null, "Open-Weight NLI Referee Verdict");
    refTitle.style.margin = "0";
    refTitle.style.fontSize = "1rem";
    refTitle.style.fontWeight = "800";
    var refModel = createEl(
      "span",
      "llama-pill",
      edge.referee_model || "Qwen2.5-7B-Instruct (NLI Referee)"
    );
    refHead.appendChild(refTitle);
    refHead.appendChild(refModel);
    refPanel.appendChild(refHead);

    var refCopy = createEl(
      "p",
      "drawer-referee-copy",
      edge.explanation ||
        "The automated natural language inference referee evaluated both passages in context. Differences in population baseline, dosage, or measurement window may explain the observed divergence."
    );
    refPanel.appendChild(refCopy);

    var metrics = createEl("div", "drawer-referee-metrics");
    if (edge.cosine_similarity !== undefined && edge.cosine_similarity !== null) {
      metrics.appendChild(createEl("span", null, "BGE Embedding Similarity: " + Number(edge.cosine_similarity).toFixed(3)));
    }
    if (edge.edge_id) {
      metrics.appendChild(createEl("span", null, "Edge ID: " + edge.edge_id));
    }
    refPanel.appendChild(metrics);

    els.body.appendChild(refPanel);

    // Reveal Drawer & Backdrop
    els.drawer.hidden = false;
    els.drawer.setAttribute("aria-hidden", "false");
    if (els.backdrop) els.backdrop.hidden = false;

    // Trigger slide-in CSS transition on next tick
    setTimeout(function () {
      els.drawer.classList.add("open");
      if (els.closeBtn) {
        els.closeBtn.focus();
      }
    }, 20);
  }

  function close() {
    var els = getDrawerElements();
    if (!els.drawer) return;

    els.drawer.classList.remove("open");
    els.drawer.setAttribute("aria-hidden", "true");

    setTimeout(function () {
      els.drawer.hidden = true;
      if (els.backdrop) els.backdrop.hidden = true;
      if (lastFocusedEl && typeof lastFocusedEl.focus === "function") {
        try {
          lastFocusedEl.focus();
        } catch (e) {
          // Ignore focus failure if trigger no longer exists
        }
      }
    }, 280);
  }

  function isOpen() {
    var els = getDrawerElements();
    return els.drawer ? els.drawer.classList.contains("open") : false;
  }

  function handleDrawerKeydown(e) {
    if (!isOpen()) return;

    if (e.key === "Escape" || e.keyCode === 27) {
      close();
      return;
    }

    // Modal Focus Trap for Tab and Shift+Tab (P4-02)
    if (e.key === "Tab") {
      var els = getDrawerElements();
      if (!els.drawer) return;
      var focusable = Array.prototype.slice.call(
        els.drawer.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
      );
      if (!focusable.length) return;

      var first = focusable[0];
      var last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first || !els.drawer.contains(document.activeElement)) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last || !els.drawer.contains(document.activeElement)) {
          e.preventDefault();
          first.focus();
        }
      }
    }
  }

  function init() {
    var els = getDrawerElements();

    if (els.closeBtn) {
      els.closeBtn.addEventListener("click", close);
    }

    if (els.backdrop) {
      els.backdrop.addEventListener("click", close);
    }

    document.addEventListener("keydown", handleDrawerKeydown);
  }

  global.KairosDrawer = {
    open: open,
    close: close,
    isOpen: isOpen,
    init: init
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window);
