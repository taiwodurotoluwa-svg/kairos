/**
 * Kairos Pinned-Baseline Synthesis Matrix Controller (Milestone P3)
 * Owner: Peace (Oluwanifemi)
 *
 * Implements a sticky pinned-baseline comparison matrix across 6-8+ papers.
 * The reference paper remains anchored on the left while comparative studies
 * scroll horizontally. Each intersection renders multi-modal evidence badges
 * (Agree, Contradict, Delta, Gap) with hover/focus popovers containing verbatim
 * quotes, section tags, and page provenance.
 */
(function (global) {
  "use strict";

  var state = {
    payload: null,
    baselinePaperId: null,
    filterSignal: "ALL",
    searchQuery: ""
  };

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

  /**
   * Helper to create DOM element with class and textContent
   */
  function createEl(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined && text !== null) el.textContent = String(text);
    return el;
  }

  /**
   * Escape HTML for safe tooltip display
   */
  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  /**
   * Create an accessible multi-modal signal badge
   */
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

  /**
   * Populate the baseline paper dropdown in the toolbar
   */
  function updateBaselineSelect(papers) {
    var selectEl = document.getElementById("matrix-baseline-select");
    if (!selectEl) return;

    selectEl.innerHTML = "";
    papers.forEach(function (paper, index) {
      var opt = document.createElement("option");
      opt.value = paper.paper_id;
      var citation = paper.citation_label || (paper.authors && paper.authors[0] ? paper.authors[0] + " (" + paper.year + ")" : "Paper " + (index + 1));
      opt.textContent = "P" + (index + 1) + ": " + citation;
      if (paper.paper_id === state.baselinePaperId) {
        opt.selected = true;
      }
      selectEl.appendChild(opt);
    });
  }

  /**
   * Build the structured matrix model from raw API payload
   */
  function buildMatrixRows(payload, baselinePaperId) {
    var papers = payload.papers || [];
    var claims = payload.claims || [];
    var edges = payload.edges || [];
    var clusters = payload.clusters || [];
    var gaps = payload.gaps || [];

    // Map claims by paper_id and by claim_id
    var claimsByPaper = {};
    var claimsById = {};
    claims.forEach(function (c) {
      if (!claimsByPaper[c.paper_id]) {
        claimsByPaper[c.paper_id] = [];
      }
      claimsByPaper[c.paper_id].push(c);
      claimsById[c.claim_id] = c;
    });

    // Map edges between claims
    var edgesBetweenClaims = {};
    edges.forEach(function (e) {
      var k1 = e.source_claim_id + "::" + e.target_claim_id;
      var k2 = e.target_claim_id + "::" + e.source_claim_id;
      edgesBetweenClaims[k1] = e;
      edgesBetweenClaims[k2] = e;
    });

    // Map gaps by claim_id
    var gapsByClaimId = {};
    gaps.forEach(function (g) {
      gapsByClaimId[g.claim_id] = g;
    });

    var rows = [];

    // 1. First, build rows around topic clusters
    clusters.forEach(function (cluster) {
      var clusterClaimIds = cluster.claim_ids || [];
      var baselineClaim = null;

      // Find if baseline paper has a claim in this cluster
      for (var i = 0; i < clusterClaimIds.length; i++) {
        var c = claimsById[clusterClaimIds[i]];
        if (c && c.paper_id === baselinePaperId) {
          baselineClaim = c;
          break;
        }
      }

      // If no claim in baseline, pick the first claim from cluster as reference
      var referenceClaim = baselineClaim || (clusterClaimIds.length > 0 ? claimsById[clusterClaimIds[0]] : null);
      if (!referenceClaim) return;

      var row = {
        rowId: "cluster_" + cluster.cluster_id,
        topic: cluster.label,
        referenceClaim: referenceClaim,
        isBaselinePresent: !!baselineClaim,
        baselineClaim: baselineClaim,
        cells: {} // keyed by paper_id
      };

      // Populate cells for every paper
      papers.forEach(function (p) {
        if (p.paper_id === baselinePaperId) {
          row.cells[p.paper_id] = {
            isBaseline: true,
            claim: baselineClaim,
            hasData: !!baselineClaim
          };
          return;
        }

        // Find paper's claims in this cluster
        var paperClaimsInCluster = (claimsByPaper[p.paper_id] || []).filter(function (c) {
          return clusterClaimIds.indexOf(c.claim_id) !== -1;
        });

        if (paperClaimsInCluster.length > 0) {
          var targetClaim = paperClaimsInCluster[0];
          var edge = baselineClaim
            ? (edgesBetweenClaims[baselineClaim.claim_id + "::" + targetClaim.claim_id] || null)
            : null;
          var gap = gapsByClaimId[targetClaim.claim_id] || (targetClaim.is_research_gap ? targetClaim : null);

          var relation = edge ? edge.relation : (gap ? "RESEARCH_GAP" : null);

          row.cells[p.paper_id] = {
            isBaseline: false,
            claim: targetClaim,
            edge: edge,
            gap: gap,
            relation: relation,
            hasData: true
          };
        } else {
          row.cells[p.paper_id] = {
            isBaseline: false,
            claim: null,
            hasData: false
          };
        }
      });

      rows.push(row);
    });

    // 2. Add remaining baseline claims not covered by clusters
    var baselineAllClaims = claimsByPaper[baselinePaperId] || [];
    baselineAllClaims.forEach(function (bc, idx) {
      var alreadyAdded = rows.some(function (r) {
        return r.baselineClaim && r.baselineClaim.claim_id === bc.claim_id;
      });

      if (!alreadyAdded) {
        var row = {
          rowId: "baseline_claim_" + bc.claim_id,
          topic: bc.topic_hint || ("Claim " + (idx + 1)),
          referenceClaim: bc,
          isBaselinePresent: true,
          baselineClaim: bc,
          cells: {}
        };

        papers.forEach(function (p) {
          if (p.paper_id === baselinePaperId) {
            row.cells[p.paper_id] = {
              isBaseline: true,
              claim: bc,
              hasData: true
            };
            return;
          }

          // Check if any claim in this comparative paper has an edge to this baseline claim
          var matchingEdge = null;
          var matchingClaim = null;
          (claimsByPaper[p.paper_id] || []).forEach(function (compClaim) {
            var e = edgesBetweenClaims[bc.claim_id + "::" + compClaim.claim_id];
            if (e && !matchingEdge) {
              matchingEdge = e;
              matchingClaim = compClaim;
            }
          });

          if (matchingClaim) {
            row.cells[p.paper_id] = {
              isBaseline: false,
              claim: matchingClaim,
              edge: matchingEdge,
              relation: matchingEdge ? matchingEdge.relation : null,
              hasData: true
            };
          } else {
            row.cells[p.paper_id] = {
              isBaseline: false,
              claim: null,
              hasData: false
            };
          }
        });

        rows.push(row);
      }
    });

    return rows;
  }

  /**
   * Render the entire Matrix Table into #matrix-scroll-pane
   */
  function renderTable() {
    var container = document.getElementById("matrix-table-container");
    var activeFilterBadge = document.getElementById("matrix-active-filter-label");
    var rowCountBadge = document.getElementById("matrix-row-count-badge");

    if (!container || !state.payload) return;

    var payload = state.payload;
    var papers = payload.papers || [];
    var baselineId = state.baselinePaperId;
    var baselinePaper = papers.find(function (p) { return p.paper_id === baselineId; }) || papers[0];

    // Other comparative papers
    var comparativePapers = papers.filter(function (p) { return p.paper_id !== baselineId; });

    var allRows = buildMatrixRows(payload, baselineId);

    // Apply Filter & Search
    var filteredRows = allRows.filter(function (row) {
      // 1. Signal Filter
      if (state.filterSignal !== "ALL") {
        var hasMatchingSignal = Object.keys(row.cells).some(function (pid) {
          var cell = row.cells[pid];
          return cell && cell.relation === state.filterSignal;
        });
        if (!hasMatchingSignal) return false;
      }

      // 2. Search Query
      if (state.searchQuery.trim() !== "") {
        var q = state.searchQuery.toLowerCase();
        var topicMatch = row.topic && row.topic.toLowerCase().indexOf(q) !== -1;
        var claimMatch = row.referenceClaim && row.referenceClaim.statement && row.referenceClaim.statement.toLowerCase().indexOf(q) !== -1;
        if (!topicMatch && !claimMatch) return false;
      }

      return true;
    });

    if (rowCountBadge) {
      rowCountBadge.textContent = filteredRows.length + " rows";
    }

    if (activeFilterBadge) {
      activeFilterBadge.textContent = state.filterSignal === "ALL" ? "All Evidence Signals" : SIGNAL_META[state.filterSignal].label;
    }

    container.innerHTML = "";

    var scrollPane = createEl("div", "matrix-scroll-pane");
    var table = createEl("table", "matrix-table");
    table.setAttribute("role", "grid");
    table.setAttribute("aria-label", "Cross-paper synthesis comparison matrix");

    // Table Header
    var thead = createEl("thead");
    var headerRow = createEl("tr");

    // Col 0: Topic / Research Focus (Sticky Left: 0)
    var thTopic = createEl("th", "matrix-th th-sticky-topic");
    thTopic.textContent = "Synthesis Topic & Claim Focus";
    headerRow.appendChild(thTopic);

    // Col 1: Pinned Baseline Paper (Sticky Left: 260px)
    var thBaseline = createEl("th", "matrix-th th-sticky-baseline");
    var baselineBadge = createEl("span", "pinned-baseline-badge", "PINNED BASELINE");
    var baselineTitle = createEl("div", "th-paper-title", baselinePaper.title);
    var baselineCitation = createEl(
      "div",
      "th-paper-sub",
      (baselinePaper.citation_label || (baselinePaper.authors && baselinePaper.authors[0] ? baselinePaper.authors[0] : "Baseline")) + " · " + (baselinePaper.year || "2024")
    );
    thBaseline.appendChild(baselineBadge);
    thBaseline.appendChild(baselineTitle);
    thBaseline.appendChild(baselineCitation);
    headerRow.appendChild(thBaseline);

    // Cols 2..N: Comparative Papers
    comparativePapers.forEach(function (paper, idx) {
      var thComp = createEl("th", "matrix-th th-comp-paper");
      var compBadge = createEl("span", "comp-paper-badge", "PAPER 0" + (papers.indexOf(paper) + 1));
      var compTitle = createEl("div", "th-paper-title", paper.title);
      var compCitation = createEl(
        "div",
        "th-paper-sub",
        (paper.citation_label || (paper.authors && paper.authors[0] ? paper.authors[0] : "Study")) + " · " + (paper.year || "2024")
      );

      // Pin As Baseline Quick Switch Button
      var pinBtn = createEl("button", "btn-pin-baseline", "Pin as Baseline 📌");
      pinBtn.type = "button";
      pinBtn.title = "Make this paper the sticky baseline reference";
      pinBtn.addEventListener("click", function () {
        setBaseline(paper.paper_id);
      });

      thComp.appendChild(compBadge);
      thComp.appendChild(compTitle);
      thComp.appendChild(compCitation);
      thComp.appendChild(pinBtn);
      headerRow.appendChild(thComp);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Table Body
    var tbody = createEl("tbody");

    if (filteredRows.length === 0) {
      var emptyTr = createEl("tr");
      var emptyTd = createEl("td", "matrix-empty-cell");
      emptyTd.setAttribute("colspan", String(papers.length + 1));
      emptyTd.textContent = "No research claims match the active filter or search query.";
      emptyTr.appendChild(emptyTd);
      tbody.appendChild(emptyTr);
    } else {
      filteredRows.forEach(function (row) {
        var tr = createEl("tr", "matrix-row");

        // Col 0: Topic (Sticky 0)
        var tdTopic = createEl("td", "matrix-td td-sticky-topic");
        var topicHeading = createEl("div", "matrix-row-topic", row.topic);
        tdTopic.appendChild(topicHeading);
        if (row.referenceClaim && row.referenceClaim.statement) {
          var statementPreview = createEl("div", "matrix-statement-preview", row.referenceClaim.statement);
          tdTopic.appendChild(statementPreview);
        }
        tr.appendChild(tdTopic);

        // Col 1: Pinned Baseline Cell (Sticky 260px)
        var baselineCell = row.cells[baselineId];
        var tdBaseline = createEl("td", "matrix-td td-sticky-baseline");

        if (baselineCell && baselineCell.hasData && baselineCell.claim) {
          var bClaim = baselineCell.claim;
          var bInner = createEl("div", "cell-inner");

          var claimTypeTag = createEl("span", "cell-type-tag", (bClaim.claim_type || "FINDING").replace("_", " "));
          var claimStatement = createEl("div", "cell-statement", bClaim.statement);

          bInner.appendChild(claimTypeTag);
          bInner.appendChild(claimStatement);

          if (bClaim.provenance) {
            var prov = bClaim.provenance;
            var quoteBox = createEl(
              "blockquote",
              "cell-quote",
              "“" + prov.verbatim_quote + "”"
            );
            var citeFoot = createEl(
              "div",
              "cell-cite",
              "p. " + (prov.page_number || "—") + " · " + (prov.section || "Body")
            );
            bInner.appendChild(quoteBox);
            bInner.appendChild(citeFoot);
          }

          tdBaseline.appendChild(bInner);
        } else {
          var unaddressed = createEl("div", "cell-muted", "— Baseline does not report this topic —");
          tdBaseline.appendChild(unaddressed);
        }
        tr.appendChild(tdBaseline);

        // Cols 2..N: Comparative Cells
        comparativePapers.forEach(function (paper) {
          var tdComp = createEl("td", "matrix-td td-comp-cell");
          tdComp.setAttribute("tabindex", "0");
          tdComp.setAttribute("role", "gridcell");

          var cellData = row.cells[paper.paper_id];

          if (cellData && cellData.hasData && cellData.claim) {
            var compClaim = cellData.claim;
            var compInner = createEl("div", "cell-inner");

            // Evidence Badge
            if (cellData.relation) {
              var badge = createSignalBadge(cellData.relation);
              compInner.appendChild(badge);
            }

            var compStatement = createEl("div", "cell-statement", compClaim.statement);
            compInner.appendChild(compStatement);

            if (compClaim.provenance) {
              var p = compClaim.provenance;
              var citeFoot = createEl(
                "div",
                "cell-cite",
                "p. " + (p.page_number || "—") + " · " + (p.section || "Body")
              );
              compInner.appendChild(citeFoot);
            }

            // Interactive Popover with Verbatim Quote & Referee Rationale
            var popover = createEl("div", "cell-popover");
            var popTitle = createEl("div", "popover-title", paper.title);
            popover.appendChild(popTitle);

            if (cellData.relation) {
              var popRelation = createEl("div", "popover-relation");
              popRelation.appendChild(createSignalBadge(cellData.relation));
              if (cellData.edge && cellData.edge.confidence) {
                var conf = createEl("span", "popover-conf", (cellData.edge.confidence * 100).toFixed(0) + "% confidence");
                popRelation.appendChild(conf);
              }
              popover.appendChild(popRelation);
            }

            if (cellData.edge && cellData.edge.explanation) {
              var expHeading = createEl("div", "popover-section-label", "Referee Comparison");
              var exp = createEl("p", "popover-explanation", cellData.edge.explanation);
              popover.appendChild(expHeading);
              popover.appendChild(exp);
            }

            if (compClaim.provenance) {
              var qHeading = createEl("div", "popover-section-label", "Verbatim Evidence Quote");
              var qText = createEl("blockquote", "popover-quote", "“" + compClaim.provenance.verbatim_quote + "”");
              var qCite = createEl(
                "div",
                "popover-cite",
                "Page " + (compClaim.provenance.page_number || "—") + " · Section: " + (compClaim.provenance.section || "Body")
              );
              popover.appendChild(qHeading);
              popover.appendChild(qText);
              popover.appendChild(qCite);
            }

            tdComp.appendChild(compInner);
            tdComp.appendChild(popover);
            tdComp.setAttribute("aria-expanded", "false");

            // Popover event listeners with ARIA state tracking (P3-02)
            function showPopover() {
              popover.classList.add("visible");
              tdComp.setAttribute("aria-expanded", "true");
            }
            function hidePopover() {
              popover.classList.remove("visible");
              tdComp.setAttribute("aria-expanded", "false");
            }

            tdComp.addEventListener("mouseenter", showPopover);
            tdComp.addEventListener("mouseleave", hidePopover);
            tdComp.addEventListener("focus", showPopover);
            tdComp.addEventListener("blur", hidePopover);
            tdComp.addEventListener("click", function () {
              var isVis = popover.classList.contains("visible");
              if (isVis) {
                hidePopover();
              } else {
                showPopover();
              }
            });
          } else {
            // Unpaired Comparative Cell Fallback (P3-04)
            var emptyInner = createEl("div", "cell-inner");
            var noneBadge = createEl("span", "signal-pill signal-none");
            noneBadge.title = "No direct evidence edge identified between this paper and the baseline study for this claim.";
            var noneIcon = createEl("span", "signal-icon", "—");
            noneIcon.setAttribute("aria-hidden", "true");
            var noneName = createEl("span", "signal-name", "No direct edge");
            noneBadge.appendChild(noneIcon);
            noneBadge.appendChild(noneName);

            var unaddressed = createEl("div", "cell-muted", "Topic not addressed in this study");
            unaddressed.style.marginTop = "6px";
            unaddressed.style.fontSize = "0.78rem";

            emptyInner.appendChild(noneBadge);
            emptyInner.appendChild(unaddressed);
            tdComp.appendChild(emptyInner);
          }

          tr.appendChild(tdComp);
        });

        tbody.appendChild(tr);
      });
    }

    table.appendChild(tbody);
    scrollPane.appendChild(table);
    container.appendChild(scrollPane);
  }

  /**
   * Set Pinned Baseline Paper
   */
  function setBaseline(paperId) {
    if (!state.payload) return;
    var exists = (state.payload.papers || []).some(function (p) { return p.paper_id === paperId; });
    if (exists) {
      state.baselinePaperId = paperId;
      var selectEl = document.getElementById("matrix-baseline-select");
      if (selectEl) selectEl.value = paperId;
      renderTable();
    }
  }

  /**
   * Set Active Evidence Filter
   */
  function setFilter(signalKey) {
    state.filterSignal = signalKey;

    var pills = Array.prototype.slice.call(
      document.querySelectorAll(".matrix-filter-pill")
    );
    pills.forEach(function (pill) {
      var key = pill.getAttribute("data-signal");
      var isActive = key === signalKey;
      pill.classList.toggle("active", isActive);
      pill.setAttribute("aria-pressed", isActive ? "true" : "false");
    });

    renderTable();
  }

  /**
   * Set Search Query
   */
  function setSearch(query) {
    state.searchQuery = query || "";
    renderTable();
  }

  /**
   * Initialize Matrix Controls
   */
  function initControls() {
    var baselineSelect = document.getElementById("matrix-baseline-select");
    if (baselineSelect) {
      baselineSelect.addEventListener("change", function (e) {
        setBaseline(e.target.value);
      });
    }

    var filterPills = Array.prototype.slice.call(
      document.querySelectorAll(".matrix-filter-pill")
    );
    filterPills.forEach(function (pill) {
      pill.addEventListener("click", function () {
        var signal = pill.getAttribute("data-signal");
        setFilter(signal);
      });
    });

    var searchInput = document.getElementById("matrix-search");
    if (searchInput) {
      searchInput.addEventListener("input", function (e) {
        setSearch(e.target.value);
      });
    }

    // Dismiss active provenance popovers on Escape key (P3-02)
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" || e.keyCode === 27) {
        var visiblePopovers = Array.prototype.slice.call(
          document.querySelectorAll(".cell-popover.visible")
        );
        visiblePopovers.forEach(function (pop) {
          pop.classList.remove("visible");
          if (pop.parentElement) {
            pop.parentElement.setAttribute("aria-expanded", "false");
          }
        });
      }
    });
  }

  /**
   * Public Render Hook
   */
  function render(payload) {
    if (!payload) return;
    state.payload = payload;

    var papers = payload.papers || [];
    if (!state.baselinePaperId || !papers.some(function (p) { return p.paper_id === state.baselinePaperId; })) {
      state.baselinePaperId = papers.length > 0 ? papers[0].paper_id : null;
    }

    updateBaselineSelect(papers);
    renderTable();
  }

  global.KairosMatrix = {
    render: render,
    setBaseline: setBaseline,
    setFilter: setFilter,
    setSearch: setSearch,
    init: initControls,
    getState: function () {
      return Object.assign({}, state);
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initControls);
  } else {
    initControls();
  }
})(window);
