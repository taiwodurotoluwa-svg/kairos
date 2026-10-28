/**
 * Kairos Core Application Controller (Milestone P1)
 * Owner: Peace (Oluwanifemi)
 *
 * Manages Academic Editorial theme switching (Light/Dark), preset loading,
 * provenance banner visibility, workspace view navigation, and the custom
 * "state:loaded" event bus.
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
    theme: "light",
    payload: null,
    isLoading: false
  };

  /**
   * Helper to set textContent safely on an element by ID.
   */
  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) {
      el.textContent = String(value);
    }
  }

  /**
   * Helper to create a DOM element with className and textContent.
   */
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

  /* ------------------------------------------------------------------------
     Workspace View Tabs (Matrix, Graph, Consensus)
     ------------------------------------------------------------------------ */
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

  /* ------------------------------------------------------------------------
     DOM Renderers for P1 Shell Verification
     ------------------------------------------------------------------------ */
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

  function createQuoteBlock(provenance) {
    var block = createEl("blockquote", "quote-block");
    var quoteText = createEl(
      "p",
      "quote-text",
      "“" + (provenance.verbatim_quote || "") + "”"
    );
    var cite = createEl(
      "footer",
      "quote-provenance",
      "p. " +
        provenance.page_number +
        " · " +
        provenance.section +
        " · " +
        provenance.paper_title
    );
    block.appendChild(quoteText);
    block.appendChild(cite);
    return block;
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

    (payload.papers || []).forEach(function (paper) {
      var card = createEl("article", "paper-shell-card");

      var top = createEl("div", "paper-card-top");
      var chip = createEl("span", "paper-short-chip", paper.short_label);
      var citation = createEl("span", "paper-citation", paper.citation_label);
      top.appendChild(chip);
      top.appendChild(citation);

      var title = createEl("h3", "paper-title", paper.title);

      var dl = createEl("dl", "paper-meta-list");
      var fields = [
        ["Dataset", paper.dataset],
        ["Sample size", paper.sample_size || "Not reported"],
        ["Methodology", paper.methodology],
        ["Primary metric", paper.primary_metric],
        ["Conclusion", paper.core_conclusion]
      ];
      fields.forEach(function (pair) {
        var row = createEl("div", "paper-meta-row");
        row.appendChild(createEl("dt", "paper-meta-term", pair[0]));
        row.appendChild(createEl("dd", "paper-meta-detail", pair[1]));
        dl.appendChild(row);
      });

      card.appendChild(top);
      card.appendChild(title);
      card.appendChild(dl);

      var paperClaims = claimsByPaper[paper.paper_id] || [];
      if (paperClaims.length > 0 && paperClaims[0].provenance) {
        card.appendChild(createQuoteBlock(paperClaims[0].provenance));
      }

      container.appendChild(card);
    });
  }

  function renderGraphShell(payload) {
    var container = document.getElementById("graph-shell-content");
    if (!container) return;
    container.textContent = "";

    (payload.edges || []).forEach(function (edge) {
      var card = createEl("article", "edge-shell-card");

      var header = createEl("div", "edge-header-row");
      header.appendChild(createSignalBadge(edge.relation));
      var metaText =
        "Confidence " +
        Number(edge.confidence).toFixed(2) +
        " · Cosine sim " +
        Number(edge.cosine_similarity).toFixed(2) +
        " · " +
        edge.edge_id;
      header.appendChild(createEl("span", "mono-tag", metaText));

      var explanation = createEl("p", "edge-explanation", edge.explanation);

      var quotesGrid = createEl("div", "edge-quotes-grid");
      if (edge.source) {
        quotesGrid.appendChild(createQuoteBlock(edge.source));
      }
      if (edge.target) {
        quotesGrid.appendChild(createQuoteBlock(edge.target));
      }

      card.appendChild(header);
      card.appendChild(explanation);
      card.appendChild(quotesGrid);
      container.appendChild(card);
    });
  }

  function renderConsensusShell(payload) {
    var container = document.getElementById("consensus-shell-content");
    if (!container) return;
    container.textContent = "";

    var consensus = payload.consensus || {};
    var summaryCard = createEl("article", "consensus-shell-card");
    var heading = createEl(
      "h3",
      "paper-title",
      "Field Consensus Score: " +
        (consensus.consensus_score !== undefined ? consensus.consensus_score : 0) +
        "%"
    );
    var summaryText = createEl(
      "p",
      "edge-explanation",
      consensus.executive_summary || ""
    );
    summaryCard.appendChild(heading);
    summaryCard.appendChild(summaryText);
    container.appendChild(summaryCard);

    (payload.gaps || []).forEach(function (gap) {
      var gapCard = createEl("article", "consensus-shell-card");
      var top = createEl("div", "edge-header-row");
      top.appendChild(createSignalBadge("RESEARCH_GAP"));
      top.appendChild(
        createEl(
          "span",
          "mono-tag",
          "Best cross-paper similarity: " + Number(gap.best_match_similarity).toFixed(2)
        )
      );

      var statement = createEl("h4", "paper-title", gap.statement);
      var reason = createEl("p", "edge-explanation", gap.reason);

      gapCard.appendChild(top);
      gapCard.appendChild(statement);
      gapCard.appendChild(reason);
      if (gap.provenance) {
        gapCard.appendChild(createQuoteBlock(gap.provenance));
      }
      container.appendChild(gapCard);
    });
  }

  function renderModelTable(models) {
    var tbody = document.getElementById("model-table-body");
    if (!tbody) return;
    tbody.textContent = "";

    if (!Array.isArray(models) || models.length === 0) {
      var emptyRow = createEl("tr");
      var cell = createEl("td", "table-empty-cell", "No model disclosures reported.");
      cell.setAttribute("colspan", "5");
      emptyRow.appendChild(cell);
      tbody.appendChild(emptyRow);
      return;
    }

    models.forEach(function (m) {
      var tr = createEl("tr");
      tr.appendChild(createEl("td", "mono-cell", m.role));
      tr.appendChild(createEl("td", "mono-cell", m.model_id));
      tr.appendChild(createEl("td", "mono-cell", m.provider));
      tr.appendChild(createEl("td", "mono-cell", m.parameter_count));

      var licenseTd = createEl("td");
      if (m.license_url) {
        var link = createEl("a", "footer-link", m.license);
        link.href = m.license_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
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
    setText("stat-papers", stats.paper_count !== undefined ? stats.paper_count : payload.papers.length);
    setText("stat-claims", stats.claim_count !== undefined ? stats.claim_count : payload.claims.length);
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

    setText("tab-badge-matrix", payload.papers.length + " papers");
    setText("tab-badge-graph", payload.edges.length + " relations");
    var consensusScore =
      payload.consensus && payload.consensus.consensus_score !== undefined
        ? payload.consensus.consensus_score + "%"
        : "—";
    setText("tab-badge-consensus", consensusScore);

    renderMatrixShell(payload);
    renderGraphShell(payload);
    renderConsensusShell(payload);
    renderModelTable(payload.models);
  }

  /* ------------------------------------------------------------------------
     Preset Coordinator & Event Bus
     ------------------------------------------------------------------------ */
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

  function initControls() {
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
        loadPreset("demo_radiology_8papers");
      });
    }
  }

  function boot() {
    initTabs();
    initControls();
    /* Load default preset (demo_radiology_8papers) on boot per P1 specification */
    loadPreset("demo_radiology_8papers");
  }

  global.KairosApp = {
    state: state,
    loadPreset: loadPreset,
    switchView: switchView
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})(window);
