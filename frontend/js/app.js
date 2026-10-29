/**
 * Kairos Core Application Controller (Milestones P1 & P2 — Argon 4 Patched)
 * Owner: Peace (Oluwanifemi)
 *
 * Manages Editorial Kinetic Science workspace views, preset loading,
 * dynamic Dispute Lab claim population, synthetic data provenance banners,
 * and the custom "state:loaded" event bus.
 */
(function (global) {
  "use strict";

  var SYNTHETIC_WARNING_TEXT =
    "Demo Data: Synthetically generated for interface testing. Not peer-reviewed scientific claims.";

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

  var state = {
    activePreset: "radiology",
    activeView: "matrix",
    payload: null,
    isLoading: false
  };

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) {
      el.textContent = String(value);
    }
  }

  function createEl(tag, className, text) {
    var el = document.createElement(tag);
    if (className) {
      el.className = className;
    }
    if (text !== undefined && text !== null) {
      el.textContent = String(text);
    }
    return el;
  }

  function switchView(viewName, focusTab) {
    var validViews = ["matrix", "graph", "consensus"];
    if (validViews.indexOf(viewName) === -1) {
      return;
    }
    state.activeView = viewName;

    validViews.forEach(function (v) {
      var tab = document.getElementById("tab-" + v);
      var panel = document.getElementById("view-" + v);
      var isActive = v === viewName;

      if (tab) {
        tab.classList.toggle("active", isActive);
        tab.setAttribute("aria-selected", isActive ? "true" : "false");
        tab.setAttribute("tabindex", isActive ? "0" : "-1");
        if (isActive && focusTab) {
          tab.focus();
        }
      }
      if (panel) {
        panel.hidden = !isActive;
      }
    });

    if (viewName === "graph" && global.KairosGraph) {
      setTimeout(function () {
        if (state.payload) {
          global.KairosGraph.render(state.payload);
        }
        if (typeof global.KairosGraph.resize === "function") {
          global.KairosGraph.resize();
        }
      }, 50);
    }

    if (viewName === "consensus" && global.KairosConsensus && global.KairosConsensus.render) {
      if (state.payload) {
        global.KairosConsensus.render(state.payload);
      }
    }
  }

  function initTabs() {
    var tabs = Array.prototype.slice.call(
      document.querySelectorAll('.tab-button[role="tab"]')
    );
    tabs.forEach(function (tab, index) {
      tab.addEventListener("click", function () {
        var targetView = tab.getAttribute("data-view");
        switchView(targetView, false);
      });

      tab.addEventListener("keydown", function (event) {
        var nextIndex = null;
        if (event.key === "ArrowRight") {
          nextIndex = (index + 1) % tabs.length;
        } else if (event.key === "ArrowLeft") {
          nextIndex = (index - 1 + tabs.length) % tabs.length;
        } else if (event.key === "Home") {
          nextIndex = 0;
        } else if (event.key === "End") {
          nextIndex = tabs.length - 1;
        }

        if (nextIndex !== null) {
          event.preventDefault();
          var targetView = tabs[nextIndex].getAttribute("data-view");
          switchView(targetView, true);
        }
      });
    });
  }

  var disputeEdges = [];
  var currentDisputeIndex = 0;

  var refereeFallbackNotes = [
    'These claims may not be direct opposites. The studies could differ in follow-up duration, participant profile, or how “improvement” was measured. A contradiction is a signal to inspect the methods—not a verdict.',
    'Try checking the outcome measures first. One study may measure immediate recall while the other tests retention weeks later. Similar words can hide different definitions.',
    'Next, compare the participants and conditions. A result can hold for one population or setting without generalising to another. The source methods matter as much as the headline.'
  ];

  function renderDisputeLab(payload) {
    var edges = payload.edges || [];
    disputeEdges = edges.filter(function (e) {
      return e.relation === "CONTRADICT" || e.relation === "METHODOLOGY_DELTA";
    });
    if (disputeEdges.length === 0) {
      disputeEdges = edges.slice();
    }
    currentDisputeIndex = 0;
    updateDisputeView();
  }

  function updateDisputeView() {
    if (disputeEdges.length === 0) return;
    var edge = disputeEdges[currentDisputeIndex % disputeEdges.length];

    if (edge.source) {
      var titleA = edge.source.paper_title || "Study A / claim";
      setText("dispute-a-label", titleA.length > 38 ? titleA.substring(0, 35) + "…" : titleA);
      setText("dispute-a-tag", edge.source.paper_id || "01—A");
      setText("dispute-a-quote", "“" + (edge.source.verbatim_quote || "") + "”");
      setText("dispute-a-foot", (edge.source.section || "Findings") + " · p. " + (edge.source.page_number || "08"));
      setText("dispute-a-year", "Source A ↗");
    }

    if (edge.target) {
      var titleB = edge.target.paper_title || "Study B / claim";
      setText("dispute-b-label", titleB.length > 38 ? titleB.substring(0, 35) + "…" : titleB);
      setText("dispute-b-tag", edge.target.paper_id || "02—B");
      setText("dispute-b-quote", "“" + (edge.target.verbatim_quote || "") + "”");
      setText("dispute-b-foot", (edge.target.section || "Results") + " · p. " + (edge.target.page_number || "11"));
      setText("dispute-b-year", "Source B ↗");
    }

    // Patched P2-06: Safe DOM node creation instead of raw innerHTML
    var refereeCopy = document.getElementById("referee-copy");
    if (refereeCopy) {
      var confidencePct = edge.confidence ? Math.round(edge.confidence * 100) : 92;
      var note = edge.explanation || refereeFallbackNotes[currentDisputeIndex % refereeFallbackNotes.length];
      refereeCopy.textContent = note;
      refereeCopy.appendChild(createEl("br"));
      refereeCopy.appendChild(createEl("br"));
      refereeCopy.appendChild(
        createEl(
          "strong",
          null,
          "Referee Verdict: " + edge.relation.replace(/_/g, " ") + " (" + confidencePct + "% NLI Confidence)"
        )
      );
    }

    var inspectBtn = document.getElementById("inspect-btn");
    if (inspectBtn) {
      inspectBtn.textContent = disputeEdges.length > 1
        ? "Inspect edge " + ((currentDisputeIndex % disputeEdges.length) + 1) + " of " + disputeEdges.length + " ↗"
        : "Inspect another angle ↗";
    }
  }

  function initDisputeControls() {
    var inspectBtn = document.getElementById("inspect-btn");
    if (inspectBtn) {
      inspectBtn.addEventListener("click", function () {
        if (disputeEdges.length > 0) {
          currentDisputeIndex = (currentDisputeIndex + 1) % disputeEdges.length;
          updateDisputeView();
        }
      });
    }
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

  function renderMatrixShell(payload) {
    var container = document.getElementById("matrix-shell-content");
    if (!container) return;
    container.textContent = "";

    var claimsByPaper = {};
    (payload.claims || []).forEach(function (c) {
      if (!claimsByPaper[c.paper_id]) {
        claimsByPaper[c.paper_id] = [];
      }
      claimsByPaper[c.paper_id].push(c);
    });

    (payload.papers || []).forEach(function (paper, index) {
      var card = createEl("article", "paper-card");

      var header = createEl("div", "paper-card-header");
      header.appendChild(createEl("span", null, "PAPER " + String(index + 1).padStart(2, "0")));
      header.appendChild(createEl("span", null, paper.year ? String(paper.year) : "2024"));

      var title = createEl("h4", "paper-card-title", paper.title);
      var meta = createEl(
        "div",
        "paper-card-meta",
        (paper.authors && paper.authors.length ? paper.authors.join(", ") : "Lead Author et al.") +
        " · " + (paper.methodology || "Comparative Study")
      );

      card.appendChild(header);
      card.appendChild(title);
      card.appendChild(meta);

      // Patched P2-02: Include verbatim provenance page_number & section
      var paperClaims = claimsByPaper[paper.paper_id] || [];
      if (paperClaims.length > 0 && paperClaims[0].provenance) {
        var prov = paperClaims[0].provenance;
        var claimQuote = createEl(
          "div",
          "paper-card-claim",
          "“" + prov.verbatim_quote + "” — p. " + (prov.page_number || "—") + " · " + (prov.section || "Body")
        );
        card.appendChild(claimQuote);
      }

      container.appendChild(card);
    });
  }

  function renderGraphShell(payload) {
    if (global.KairosGraph && global.KairosGraph.render) {
      global.KairosGraph.render(payload);
    }
  }

  function renderConsensusShell(payload) {
    if (global.KairosConsensus && global.KairosConsensus.render) {
      global.KairosConsensus.render(payload);
      return;
    }

    var container = document.getElementById("consensus-shell-content");
    if (!container) return;
    container.textContent = "";

    var consensus = payload.consensus || {};
    var summaryCard = createEl("article", "paper-card");
    summaryCard.style.gridColumn = "1 / -1";
    var heading = createEl(
      "h3",
      "paper-card-title",
      "Field Consensus Score: " +
        (consensus.consensus_score !== undefined ? consensus.consensus_score : 0) +
        "%"
    );
    var summaryText = createEl(
      "p",
      "view-description",
      consensus.executive_summary || "Synthesis complete across staged corpus."
    );
    summaryCard.appendChild(heading);
    summaryCard.appendChild(summaryText);
    container.appendChild(summaryCard);

    (payload.gaps || []).forEach(function (gap) {
      var gapCard = createEl("article", "paper-card");
      var top = createEl("div", "paper-card-header");
      top.appendChild(createSignalBadge("RESEARCH_GAP"));
      top.appendChild(
        createEl(
          "span",
          null,
          "Similarity: " + Number(gap.best_match_similarity || 0.45).toFixed(2)
        )
      );

      var statement = createEl("h4", "paper-card-title", gap.statement);
      var reason = createEl("p", "paper-card-meta", gap.reason);

      gapCard.appendChild(top);
      gapCard.appendChild(statement);
      gapCard.appendChild(reason);
      container.appendChild(gapCard);
    });
  }

  function renderModelTable(models) {
    var tbody = document.getElementById("model-table-body");
    if (!tbody) return;
    tbody.textContent = "";

    if (!Array.isArray(models) || models.length === 0) {
      var emptyRow = createEl("tr");
      var cell = createEl("td", null, "No model disclosures reported.");
      cell.setAttribute("colspan", "5");
      emptyRow.appendChild(cell);
      tbody.appendChild(emptyRow);
      return;
    }

    models.forEach(function (m) {
      var tr = createEl("tr");
      tr.appendChild(createEl("td", null, m.role));
      tr.appendChild(createEl("td", null, m.model_id));
      tr.appendChild(createEl("td", null, m.provider));
      tr.appendChild(createEl("td", null, m.parameter_count));

      var licenseTd = createEl("td");
      if (m.license_url) {
        var link = createEl("a", null, m.license);
        link.href = m.license_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.style.textDecoration = "underline";
        licenseTd.appendChild(link);
      } else {
        licenseTd.textContent = m.license || "";
      }
      tr.appendChild(licenseTd);
      tbody.appendChild(tr);
    });
  }

  function renderPayload(payload, meta) {
    var banner = document.getElementById("synthetic-banner");
    var bannerText = document.getElementById("synthetic-banner-text");
    var isSynthetic = payload.fixture_provenance === "SYNTHETIC_PLACEHOLDER";

    if (banner) {
      banner.hidden = !isSynthetic;
    }
    if (bannerText) {
      bannerText.textContent = SYNTHETIC_WARNING_TEXT;
    }

    setText(
      "corpus-preset-tag",
      "PRESET: " + String(payload.preset_id || meta.preset_id).toUpperCase()
    );
    setText("corpus-provenance-tag", payload.fixture_provenance);
    setText("corpus-schema-tag", "SCHEMA v" + payload.schema_version);
    setText("corpus-title", meta.title || payload.preset_id);

    var stats = payload.stats || {};
    var latency = stats.stage_latency_ms || {};
    setText("stat-papers", stats.paper_count !== undefined ? stats.paper_count : (payload.papers ? payload.papers.length : 0));
    setText("stat-claims", stats.claim_count !== undefined ? stats.claim_count : (payload.claims ? payload.claims.length : 0));
    setText(
      "stat-pairs",
      (stats.cross_paper_pairs_total || 0) + " → " + (stats.candidate_pairs || 0)
    );
    setText(
      "stat-reduction",
      stats.pair_reduction_pct !== undefined
        ? Number(stats.pair_reduction_pct).toFixed(1) + "%"
        : "—"
    );
    setText(
      "stat-referee-calls",
      stats.referee_calls !== undefined ? stats.referee_calls : "—"
    );
    setText(
      "stat-latency",
      latency.total_ms !== undefined ? latency.total_ms + " ms" : "—"
    );

    var counts = { AGREE: 0, CONTRADICT: 0, METHODOLOGY_DELTA: 0 };
    (payload.edges || []).forEach(function (edge) {
      if (counts[edge.relation] !== undefined) {
        counts[edge.relation] += 1;
      }
    });
    var gapCount = Array.isArray(payload.gaps) ? payload.gaps.length : 0;

    setText("count-agree", counts.AGREE);
    setText("count-contradict", counts.CONTRADICT);
    setText("count-delta", counts.METHODOLOGY_DELTA);
    setText("count-gap", gapCount);

    setText("tab-badge-matrix", (payload.papers ? payload.papers.length : 0) + " papers");
    setText("tab-badge-graph", (payload.edges ? payload.edges.length : 0) + " relations");
    var consensusScore =
      payload.consensus && payload.consensus.consensus_score !== undefined
        ? payload.consensus.consensus_score + "%"
        : "—";
    setText("tab-badge-consensus", consensusScore);

    renderDisputeLab(payload);
    if (global.KairosMatrix && global.KairosMatrix.render) {
      global.KairosMatrix.render(payload);
    }
    renderMatrixShell(payload);
    renderGraphShell(payload);
    renderConsensusShell(payload);
    renderModelTable(payload.models);
  }

  async function loadPreset(presetKey) {
    var loadingEl = document.getElementById("loading-state");
    var errorEl = document.getElementById("error-state");
    var errorMsgEl = document.getElementById("error-message");

    state.isLoading = true;
    if (loadingEl) loadingEl.hidden = false;
    if (errorEl) errorEl.hidden = true;

    try {
      var result = await global.KairosApi.fetchPreset(presetKey);
      state.activePreset = result.meta.preset_id;
      state.payload = result.payload;

      var selectEl = document.getElementById("preset-select");
      if (selectEl && selectEl.value !== result.meta.preset_id) {
        selectEl.value = result.meta.preset_id;
      }

      renderPayload(result.payload, result.meta);

      var eventDetail = {
        presetId: result.meta.preset_id,
        payload: result.payload,
        source: result.source,
        activeView: state.activeView
      };
      global.dispatchEvent(new CustomEvent("state:loaded", { detail: eventDetail }));
      document.dispatchEvent(new CustomEvent("state:loaded", { detail: eventDetail }));
    } catch (err) {
      if (errorEl) errorEl.hidden = false;
      if (errorMsgEl) {
        errorMsgEl.textContent = err && err.message ? err.message : "Failed to load preset.";
      }
    } finally {
      state.isLoading = false;
      if (loadingEl) loadingEl.hidden = true;
    }
  }

  function initModeToggle() {
    var btnOffline = document.getElementById("btn-mode-offline");
    var btnLive = document.getElementById("btn-mode-live");
    var statusText = document.getElementById("status-text");
    var connStatus = document.getElementById("connection-status");

    function setOfflineUI() {
      if (btnOffline) {
        btnOffline.classList.add("active");
        btnOffline.setAttribute("aria-checked", "true");
      }
      if (btnLive) {
        btnLive.classList.remove("active");
        btnLive.setAttribute("aria-checked", "false");
      }
      if (statusText) statusText.textContent = "Presets (Offline)";
      if (connStatus) {
        connStatus.classList.remove("status-live", "status-error");
        connStatus.classList.add("status-presets");
      }
      if (global.KairosApi && global.KairosApi.setApiMode) {
        global.KairosApi.setApiMode("local");
      }
    }

    async function tryLiveUI() {
      if (statusText) statusText.textContent = "Probing :8000...";
      var check = global.KairosApi && global.KairosApi.checkLiveBackendHealth
        ? await global.KairosApi.checkLiveBackendHealth()
        : { online: false };

      if (check.online) {
        if (btnOffline) {
          btnOffline.classList.remove("active");
          btnOffline.setAttribute("aria-checked", "false");
        }
        if (btnLive) {
          btnLive.classList.add("active");
          btnLive.setAttribute("aria-checked", "true");
        }
        if (statusText) statusText.textContent = "Live (FastAPI :8000)";
        if (connStatus) {
          connStatus.classList.remove("status-presets", "status-error");
          connStatus.classList.add("status-live");
        }
        if (global.KairosApi && global.KairosApi.setApiMode) {
          global.KairosApi.setApiMode("live");
        }
        loadPreset(state.activePreset);
      } else {
        if (statusText) statusText.textContent = "Backend offline (Presets active)";
        setTimeout(setOfflineUI, 2000);
      }
    }

    if (btnOffline) {
      btnOffline.addEventListener("click", function () {
        setOfflineUI();
        loadPreset(state.activePreset);
      });
    }

    if (btnLive) {
      btnLive.addEventListener("click", function () {
        tryLiveUI();
      });
    }
  }

  function initControls() {
    initModeToggle();

    var selectEl = document.getElementById("preset-select");
    if (selectEl) {
      selectEl.addEventListener("change", function (event) {
        loadPreset(event.target.value);
      });
    }

    var retryBtn = document.getElementById("retry-button");
    if (retryBtn) {
      retryBtn.addEventListener("click", function () {
        loadPreset(state.activePreset);
      });
    }

    var fallbackBtn = document.getElementById("fallback-button");
    if (fallbackBtn) {
      fallbackBtn.addEventListener("click", function () {
        loadPreset("radiology");
      });
    }
  }

  var VALID_PAGES = ["overview", "ingest", "dispute", "matrix"];
  var activePage = "overview";

  function navigateToPage(pageId, updateHash) {
    if (VALID_PAGES.indexOf(pageId) === -1) {
      pageId = "overview";
    }
    activePage = pageId;

    VALID_PAGES.forEach(function (pid) {
      var pageEl = document.getElementById("page-" + pid);
      if (pageEl) {
        pageEl.hidden = pid !== pageId;
      }
    });

    var navLinks = Array.prototype.slice.call(
      document.querySelectorAll(".nav-page-link")
    );
    navLinks.forEach(function (link) {
      var target = link.getAttribute("data-page");
      var isActive = target === pageId;
      link.classList.toggle("active", isActive);
      link.setAttribute("aria-selected", isActive ? "true" : "false");
      link.setAttribute("tabindex", isActive ? "0" : "-1");
    });

    if (updateHash !== false) {
      if (window.location.hash !== "#" + pageId) {
        try {
          window.history.pushState(null, "", "#" + pageId);
        } catch (e) {
          window.location.hash = "#" + pageId;
        }
      }
    }

    try {
      window.scrollTo({ top: 0, left: 0, behavior: "instant" });
    } catch (e) {
      window.scrollTo(0, 0);
    }

    // When navigating to the matrix page, re-render matrix if payload is already loaded
    if (pageId === "matrix" && state.payload && global.KairosMatrix && global.KairosMatrix.render) {
      global.KairosMatrix.render(state.payload);
    }
  }

  function initPageRouter() {
    // 1. Navigation clicks for both topbar nav links and in-page CTAs
    document.addEventListener("click", function (evt) {
      var target = evt.target && evt.target.closest
        ? evt.target.closest("a[data-navigate-page], .nav-page-link")
        : null;
      if (target) {
        var page = target.getAttribute("data-page") || target.getAttribute("data-navigate-page");
        if (page && VALID_PAGES.indexOf(page) !== -1) {
          evt.preventDefault();
          navigateToPage(page, true);
        }
      }
    });

    // 2. Browser Back/Forward history navigation
    window.addEventListener("hashchange", function () {
      var hash = window.location.hash.replace(/^#/, "");
      if (VALID_PAGES.indexOf(hash) !== -1 && hash !== activePage) {
        navigateToPage(hash, false);
      }
    });

    // 3. Initial page determination from URL hash
    var initialHash = window.location.hash.replace(/^#/, "");
    if (VALID_PAGES.indexOf(initialHash) !== -1) {
      navigateToPage(initialHash, false);
    } else {
      navigateToPage("overview", false);
    }
  }

  function boot() {
    initTabs();
    initControls();
    initDisputeControls();
    initPageRouter();
    loadPreset("radiology");
  }

  global.KairosApp = {
    state: state,
    loadPreset: loadPreset,
    switchView: switchView,
    navigateToPage: navigateToPage
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})(window);
