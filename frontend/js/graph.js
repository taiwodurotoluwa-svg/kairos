/**
 * Kairos Cytoscape.js Contradiction Graph & Edge Inspector (Milestone P4)
 * Owner: Peace (Oluwanifemi)
 *
 * Renders an interactive, physics-driven force-directed network of cross-paper
 * scientific claims and contradictions using Cytoscape.js (`cose` layout).
 * Distinguishes relations via multi-modal visual cues (Ruby dashed, Emerald solid,
 * Amber dotted), and provides a fully accessible edge relation table for screen-readers.
 */
(function (global) {
  "use strict";

  var cyInstance = null;
  var currentPayload = null;
  var activeFilters = {
    CONTRADICT: true,
    AGREE: true,
    METHODOLOGY_DELTA: true
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

  function getShortCitation(paper, index) {
    if (paper.citation_label) return paper.citation_label;
    if (paper.authors && paper.authors.length > 0) {
      var first = paper.authors[0].split(",")[0].trim();
      return first + " (" + (paper.year || "2024") + ")";
    }
    return "Paper " + (index + 1);
  }

  /**
   * Build Cytoscape element definitions from payload
   */
  function buildElements(payload) {
    var papers = payload.papers || [];
    var claims = payload.claims || [];
    var edges = payload.edges || [];

    // Count claims per paper for node sizing
    var claimsPerPaper = {};
    claims.forEach(function (c) {
      claimsPerPaper[c.paper_id] = (claimsPerPaper[c.paper_id] || 0) + 1;
    });

    var elements = [];

    // 1. Paper Nodes
    papers.forEach(function (paper, idx) {
      var count = claimsPerPaper[paper.paper_id] || 1;
      var size = Math.min(88, Math.max(54, 50 + count * 4));
      var shortCit = getShortCitation(paper, idx);

      elements.push({
        group: "nodes",
        data: {
          id: paper.paper_id,
          label: shortCit,
          fullTitle: paper.title,
          claimCount: count,
          nodeSize: size,
          paperIndex: idx + 1
        }
      });
    });

    // 2. Relation Edges
    edges.forEach(function (edge) {
      var sourcePid = (edge.source && edge.source.paper_id) || (edge.source_claim_id ? edge.source_claim_id.split("-")[0] : null);
      var targetPid = (edge.target && edge.target.paper_id) || (edge.target_claim_id ? edge.target_claim_id.split("-")[0] : null);

      if (sourcePid && targetPid) {
        elements.push({
          group: "edges",
          data: {
            id: edge.edge_id,
            source: sourcePid,
            target: targetPid,
            relation: edge.relation,
            confidence: edge.confidence,
            explanation: edge.explanation,
            fullEdge: edge
          }
        });
      }
    });

    return elements;
  }

  /**
   * Render Accessible Edge Table below Canvas
   */
  function renderAccessibleTable(payload) {
    var tbody = document.getElementById("graph-edge-table-body");
    var countBadge = document.getElementById("graph-edge-count-badge");
    if (!tbody) return;

    var edges = (payload.edges || []).filter(function (e) {
      return activeFilters[e.relation] !== false;
    });

    if (countBadge) {
      countBadge.textContent = edges.length + " relations";
    }

    tbody.innerHTML = "";

    if (edges.length === 0) {
      var tr = createEl("tr");
      var td = createEl("td", null, "No evidence edges match the active filters.");
      td.colSpan = 5;
      td.style.textAlign = "center";
      td.style.padding = "24px";
      td.style.color = "var(--site-ink-muted)";
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }

    edges.forEach(function (edge) {
      var tr = createEl("tr");

      // Col 1: Source
      var tdSource = createEl("td");
      var srcTitle = createEl("strong", null, (edge.source && edge.source.paper_title) || "Source");
      var srcCite = createEl(
        "div",
        "cell-cite",
        "Section: " + ((edge.source && edge.source.section) || "Body") + " · p. " + ((edge.source && edge.source.page_number) || "—")
      );
      tdSource.appendChild(srcTitle);
      tdSource.appendChild(srcCite);
      tr.appendChild(tdSource);

      // Col 2: Target
      var tdTarget = createEl("td");
      var tgtTitle = createEl("strong", null, (edge.target && edge.target.paper_title) || "Target");
      var tgtCite = createEl(
        "div",
        "cell-cite",
        "Section: " + ((edge.target && edge.target.section) || "Body") + " · p. " + ((edge.target && edge.target.page_number) || "—")
      );
      tdTarget.appendChild(tgtTitle);
      tdTarget.appendChild(tgtCite);
      tr.appendChild(tdTarget);

      // Col 3: Relation Badge
      var tdRel = createEl("td");
      tdRel.appendChild(createSignalBadge(edge.relation));
      tr.appendChild(tdRel);

      // Col 4: Confidence & Model
      var tdConf = createEl("td");
      var confPct = (edge.confidence !== undefined && edge.confidence !== null)
        ? Math.round(edge.confidence * 100) + "%"
        : "—";
      tdConf.appendChild(createEl("div", null, confPct + " confidence"));
      tdConf.appendChild(createEl("div", "cell-cite", edge.referee_model || "Qwen2.5-7B"));
      tr.appendChild(tdConf);

      // Col 5: Action Button
      var tdAction = createEl("td");
      var btn = createEl("button", "btn-inspect-edge", "Inspect Evidence ↗");
      btn.type = "button";
      btn.setAttribute("aria-label", "Inspect evidence and verbatim quotes for " + edge.edge_id);
      btn.addEventListener("click", function () {
        if (global.KairosDrawer && global.KairosDrawer.open) {
          global.KairosDrawer.open(edge, btn);
        }
      });
      tdAction.appendChild(btn);
      tr.appendChild(tdAction);

      tbody.appendChild(tr);
    });
  }

  /**
   * Apply Relation Visibility Filters to Cytoscape
   */
  function applyFilters() {
    if (!cyInstance) return;

    cyInstance.batch(function () {
      cyInstance.edges().forEach(function (edge) {
        var rel = edge.data("relation");
        if (activeFilters[rel] === false) {
          edge.style("display", "none");
        } else {
          edge.style("display", "element");
        }
      });
    });

    if (currentPayload) {
      renderAccessibleTable(currentPayload);
    }
  }

  /**
   * Initialize or Update Cytoscape Graph
   */
  function render(payload) {
    if (!payload) return;
    currentPayload = payload;

    var container = document.getElementById("cy-network");
    if (!container) return;

    // Verify Cytoscape is available on window
    if (typeof global.cytoscape !== "function") {
      console.warn("Cytoscape library not loaded yet.");
      renderAccessibleTable(payload);
      return;
    }

    var elements = buildElements(payload);

    // Destroy existing instance if any
    if (cyInstance && typeof cyInstance.destroy === "function") {
      cyInstance.destroy();
      cyInstance = null;
    }

    cyInstance = global.cytoscape({
      container: container,
      elements: elements,
      boxSelectionEnabled: false,
      autounselectify: false,
      userZoomingEnabled: false, // Prevents page scroll hijacking; zoom delegated to [+] / [-] buttons (P4-03)
      userPanningEnabled: true,
      style: [
        // Node styling
        {
          selector: "node",
          style: {
            "shape": "ellipse",
            "width": "data(nodeSize)",
            "height": "data(nodeSize)",
            "background-color": "#FFFFFF",
            "border-width": 2.5,
            "border-color": "#0A0F1D",
            "border-style": "solid",
            "label": "data(label)",
            "text-valign": "bottom",
            "text-halign": "center",
            "text-margin-y": 8,
            "font-family": "Space Mono, monospace",
            "font-size": "10.5px",
            "font-weight": 700,
            "color": "#0A0F1D",
            "text-background-opacity": 0.85,
            "text-background-color": "#FFFFFF",
            "text-background-padding": "3px",
            "text-background-shape": "roundrectangle"
          }
        },
        // Active / Highlighted Node
        {
          selector: "node:selected, node.highlighted",
          style: {
            "border-width": 4,
            "border-color": "#4F46E5",
            "background-color": "#EEF2FF"
          }
        },
        // Edge base styling
        {
          selector: "edge",
          style: {
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
            "arrow-scale": 1.2,
            "opacity": 0.9,
            "transition-property": "opacity, width, line-color",
            "transition-duration": "0.15s"
          }
        },
        // Contradiction Edge (Ruby Dashed)
        {
          selector: 'edge[relation = "CONTRADICT"]',
          style: {
            "line-color": "#FF3366",
            "target-arrow-color": "#FF3366",
            "line-style": "dashed",
            "line-dash-pattern": [6, 4],
            "width": 3.8
          }
        },
        // Agreement Edge (Emerald/Lagoon Solid)
        {
          selector: 'edge[relation = "AGREE"]',
          style: {
            "line-color": "#00D2C4",
            "target-arrow-color": "#00D2C4",
            "line-style": "solid",
            "width": 2.6
          }
        },
        // Methodology Delta Edge (Amber Dotted - WCAG AA Contrast P4-05)
        {
          selector: 'edge[relation = "METHODOLOGY_DELTA"]',
          style: {
            "line-color": "#D97706",
            "target-arrow-color": "#D97706",
            "line-style": "dotted",
            "line-dash-pattern": [2, 3],
            "width": 2.8
          }
        },
        // Highlighted / Hovered Edge
        {
          selector: "edge.hovered",
          style: {
            "width": 6,
            "opacity": 1.0,
            "z-index": 999
          }
        },
        // Dimmed Non-adjacent Elements
        {
          selector: ".dimmed",
          style: {
            "opacity": 0.18
          }
        }
      ],
      layout: {
        name: "cose",
        animate: false,
        randomize: false,
        componentSpacing: 80,
        nodeRepulsion: 12000,
        idealEdgeLength: 140,
        edgeElasticity: 100,
        gravity: 60,
        numIter: 400,
        padding: 40
      }
    });

    // Node Interaction: Highlight connected neighbors
    cyInstance.on("tap", "node", function (evt) {
      var node = evt.target;
      var neighborhood = node.neighborhood().add(node);

      cyInstance.elements().addClass("dimmed");
      neighborhood.removeClass("dimmed").addClass("highlighted");
    });

    // Canvas Background Click: Reset highlights
    cyInstance.on("tap", function (evt) {
      if (evt.target === cyInstance) {
        cyInstance.elements().removeClass("dimmed").removeClass("highlighted").removeClass("hovered");
      }
    });

    // Edge Click: Open Slide-Over Dispute Inspection Drawer (P4)
    cyInstance.on("tap", "edge", function (evt) {
      var edge = evt.target;
      var edgeData = edge.data("fullEdge");

      if (edgeData && global.KairosDrawer && global.KairosDrawer.open) {
        global.KairosDrawer.open(edgeData);
      }
    });

    // Edge Hover Effect
    cyInstance.on("mouseover", "edge", function (evt) {
      evt.target.addClass("hovered");
    });
    cyInstance.on("mouseout", "edge", function (evt) {
      evt.target.removeClass("hovered");
    });

    // Initial Filter pass & Accessible table render
    applyFilters();
    renderAccessibleTable(payload);

    // Initial fit
    setTimeout(function () {
      if (cyInstance) {
        cyInstance.resize();
        cyInstance.fit(null, 35);
      }
    }, 120);
  }

  var resizeObserver = null;

  function initResizeObserver() {
    var container = document.getElementById("cy-network");
    if (!container || typeof global.ResizeObserver !== "function") return;

    if (resizeObserver) {
      resizeObserver.disconnect();
    }

    resizeObserver = new ResizeObserver(function (entries) {
      for (var i = 0; i < entries.length; i++) {
        var entry = entries[i];
        if (entry.contentRect && entry.contentRect.width > 0 && entry.contentRect.height > 0) {
          if (cyInstance) {
            cyInstance.resize();
            cyInstance.fit(null, 35);
          }
        }
      }
    });

    resizeObserver.observe(container);
  }

  function resize() {
    if (cyInstance) {
      cyInstance.resize();
      cyInstance.fit(null, 35);
    }
  }

  function initControls() {
    initResizeObserver();
    // Zoom In Button
    var btnZoomIn = document.getElementById("btn-graph-zoom-in");
    if (btnZoomIn) {
      btnZoomIn.addEventListener("click", function () {
        if (cyInstance) cyInstance.zoom(cyInstance.zoom() * 1.25);
      });
    }

    // Zoom Out Button
    var btnZoomOut = document.getElementById("btn-graph-zoom-out");
    if (btnZoomOut) {
      btnZoomOut.addEventListener("click", function () {
        if (cyInstance) cyInstance.zoom(cyInstance.zoom() * 0.8);
      });
    }

    // Reset Fit Button
    var btnFit = document.getElementById("btn-graph-fit");
    if (btnFit) {
      btnFit.addEventListener("click", function () {
        if (cyInstance) cyInstance.fit(null, 35);
      });
    }

    // Filter Checkboxes
    var chkContradict = document.getElementById("filter-graph-contradict");
    if (chkContradict) {
      chkContradict.addEventListener("change", function (e) {
        activeFilters.CONTRADICT = e.target.checked;
        applyFilters();
      });
    }

    var chkAgree = document.getElementById("filter-graph-agree");
    if (chkAgree) {
      chkAgree.addEventListener("change", function (e) {
        activeFilters.AGREE = e.target.checked;
        applyFilters();
      });
    }

    var chkDelta = document.getElementById("filter-graph-delta");
    if (chkDelta) {
      chkDelta.addEventListener("change", function (e) {
        activeFilters.METHODOLOGY_DELTA = e.target.checked;
        applyFilters();
      });
    }
  }

  global.KairosGraph = {
    render: render,
    resize: resize,
    applyFilters: applyFilters,
    init: initControls,
    getCy: function () {
      return cyInstance;
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initControls);
  } else {
    initControls();
  }
})(window);
