/**
 * Kairos Consensus Summary, Research Gaps & Literature Review Exporter (Milestone P5)
 * Owner: Peace (Oluwanifemi)
 *
 * Renders the circular SVG Consensus Score gauge, high-level executive synthesis,
 * categorized key agreements, top contradiction callouts, research gaps, and actionable
 * next steps. Generates formatted Markdown synthesis reports and raw JSON exports.
 */
(function (global) {
  "use strict";

  var currentPayload = null;

  function createEl(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined && text !== null) el.textContent = String(text);
    return el;
  }

  function getVerdictPill(score) {
    var pill = createEl("span", "gauge-verdict-pill");
    if (score >= 70) {
      pill.textContent = "High Consensus (Corroborated)";
      pill.style.background = "#F0FDF4";
      pill.style.color = "#064E3B";
      pill.style.borderColor = "#BBF7D0";
    } else if (score >= 45) {
      pill.textContent = "Moderate Consensus (Nuanced)";
      pill.style.background = "#FFFBEB";
      pill.style.color = "#B45309";
      pill.style.borderColor = "#FDE68A";
    } else {
      pill.textContent = "Active Debate (High Friction)";
      pill.style.background = "#FFF1F2";
      pill.style.color = "#881337";
      pill.style.borderColor = "#FECDD3";
    }
    return pill;
  }

  /**
   * Export comprehensive literature review report as clean Markdown
   */
  function exportMarkdown() {
    if (!currentPayload) return;
    var p = currentPayload;
    var c = p.consensus || {};
    var stats = p.stats || {};
    var latency = stats.stage_latency_ms || {};

    var md = [];
    md.push("# Kairos Literature Synthesis Report");
    md.push("");
    md.push("> Generated automatically by **Kairos** — Open-Source Multi-Paper Literature Synthesis & Contradiction Engine.");
    md.push("> Theme: *\"AI belongs to everyone. Build for a world you understand. Make it open.\"*");
    md.push("");
    md.push("---");
    md.push("");
    md.push("## 1. Corpus Metadata & Pipeline Telemetry");
    md.push("");
    md.push("- **Research Domain:** " + (p.preset_id || "scientific_corpus").toUpperCase());
    if (global.KAIROS_RESEARCH_OBJECTIVE) {
      md.push("- **Systematic Review Focus / Objective:** `" + global.KAIROS_RESEARCH_OBJECTIVE + "`");
    }
    md.push("- **Schema Version:** v" + (p.schema_version || "1.0.0"));
    md.push("- **Fixture Provenance:** `" + (p.fixture_provenance || "NOT_APPLICABLE") + "`");
    md.push("- **Papers Analysed:** " + (stats.paper_count || (p.papers ? p.papers.length : 0)));
    md.push("- **Verified Extracted Claims:** " + (stats.claim_count || (p.claims ? p.claims.length : 0)));
    md.push("- **Candidate Pair BGE Reduction:** " + (stats.cross_paper_pairs_total || 0) + " pairs → " + (stats.candidate_pairs || 0) + " pairs (" + (stats.pair_reduction_pct !== undefined ? Number(stats.pair_reduction_pct).toFixed(1) + "%" : "—") + " reduction)");
    md.push("- **NLI Referee Calls:** " + (stats.referee_calls || 0));
    md.push("- **Total Pipeline Latency:** " + (latency.total_ms || 0) + " ms");
    md.push("");
    md.push("---");
    md.push("");
    md.push("## 2. Executive Literature Consensus");
    md.push("");
    md.push("### Overall Consensus Score: **" + (c.consensus_score !== undefined ? c.consensus_score + "%" : "—") + "**");
    md.push("");
    md.push("> " + (c.executive_summary || "No executive summary provided."));
    md.push("");
    md.push("---");
    md.push("");
    md.push("## 3. Key Scientific Agreements");
    md.push("");
    if (c.agreed_findings && c.agreed_findings.length > 0) {
      c.agreed_findings.forEach(function (finding, idx) {
        md.push(String(idx + 1) + ". " + finding);
      });
    } else {
      md.push("_No direct consensus claims met the agreement threshold._");
    }
    md.push("");
    md.push("---");
    md.push("");
    md.push("## 4. Top Scientific Contradictions & Disputed Findings");
    md.push("");
    if (c.top_contradictions && c.top_contradictions.length > 0) {
      c.top_contradictions.forEach(function (contra, idx) {
        md.push("### Contradiction " + String(idx + 1) + ": " + contra.headline);
        var edge = (p.edges || []).find(function (e) { return e.edge_id === contra.edge_id; });
        if (edge) {
          md.push("- **Edge Identifier:** `" + edge.edge_id + "`");
          md.push("- **NLI Referee Model:** " + (edge.referee_model || "Qwen2.5-7B"));
          md.push("- **Confidence:** " + (edge.confidence !== undefined ? Math.round(edge.confidence * 100) + "%" : "—"));
          md.push("- **Referee Rationale:** " + (edge.explanation || "—"));
          if (edge.source) {
            md.push("  - **Study A (" + edge.source.paper_id + "):** *" + edge.source.paper_title + "*");
            md.push("    - Quote: *“" + edge.source.verbatim_quote + "”* (Section: " + edge.source.section + ", Page " + edge.source.page_number + ")");
          }
          if (edge.target) {
            md.push("  - **Study B (" + edge.target.paper_id + "):** *" + edge.target.paper_title + "*");
            md.push("    - Quote: *“" + edge.target.verbatim_quote + "”* (Section: " + edge.target.section + ", Page " + edge.target.page_number + ")");
          }
        }
        md.push("");
      });
    } else {
      md.push("_No prominent contradictions identified in this research collection._");
    }
    md.push("");
    md.push("---");
    md.push("");
    md.push("## 5. Identified Research Gaps & Uncorroborated Questions");
    md.push("");
    if (p.gaps && p.gaps.length > 0) {
      p.gaps.forEach(function (gap, idx) {
        md.push("### Gap " + String(idx + 1) + ": " + gap.statement);
        md.push("- **Unaddressed In:** " + (gap.provenance ? gap.provenance.paper_title : gap.paper_id));
        if (gap.provenance && gap.provenance.verbatim_quote) {
          md.push("- **Author Limitation Quote:** *“" + gap.provenance.verbatim_quote + "”* (p. " + gap.provenance.page_number + " · " + gap.provenance.section + ")");
        }
        md.push("- **Reason:** " + gap.reason);
        md.push("");
      });
    } else {
      md.push("_No uncorroborated research gaps reported._");
    }
    md.push("");
    md.push("---");
    md.push("");
    md.push("## 6. Recommended Next Experimental Steps");
    md.push("");
    if (c.recommended_next_steps && c.recommended_next_steps.length > 0) {
      c.recommended_next_steps.forEach(function (step, idx) {
        md.push(String(idx + 1) + ". " + step);
      });
    } else {
      md.push("_Continue literature monitoring and broader multi-center replication._");
    }
    md.push("");
    md.push("---");
    md.push("");
    md.push("## 7. Open-Weight Model Registry & Licences");
    md.push("");
    md.push("| Pipeline Role | Model Identifier | Runtime Provider | Parameters | Licence |");
    md.push("| :--- | :--- | :--- | :--- | :--- |");
    (p.models || []).forEach(function (m) {
      md.push(
        "| " +
          m.role +
          " | `" +
          (m.model_id || m.model_name || "—") +
          "` | " +
          (m.provider || "—") +
          " | " +
          (m.parameter_count || m.parameters || "—") +
          " | " +
          (m.license || "—") +
          " |"
      );
    });
    md.push("");
    md.push("---");
    md.push("");
    md.push("### Research & Clinical Limitation Disclaimer");
    md.push("Kairos is an academic literature synthesis and reading aid. It is not a clinical decision support system. Always verify scientific claims and methodological parameters against original peer-reviewed source publications.");

    triggerFileDownload(
      md.join("\n"),
      "kairos-synthesis-report-" + (p.preset_id || "corpus") + ".md",
      "text/markdown;charset=utf-8"
    );
  }

  /**
   * Memory-safe file download with filename sanitization (P5-02 & P5-04)
   */
  function triggerFileDownload(content, filename, mimeType) {
    var safeFilename = String(filename || "export")
      .toLowerCase()
      .replace(/[^a-z0-9._-]/g, "_");
    var blob = new Blob([content], { type: mimeType || "text/plain;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = safeFilename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);

    // Defer URL revocation to prevent premature abort and avoid memory leaks
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 1000);
  }

  /**
   * Export raw AnalysisResult JSON payload
   */
  function exportJson() {
    if (!currentPayload) return;
    var jsonStr = JSON.stringify(currentPayload, null, 2);
    triggerFileDownload(
      jsonStr,
      "kairos-analysis-result-" + (currentPayload.preset_id || "corpus") + ".json",
      "application/json;charset=utf-8"
    );
  }

  /**
   * Render the entire Consensus & Gaps View
   */
  function render(payload) {
    if (!payload) return;
    currentPayload = payload;

    var container = document.getElementById("consensus-shell-content");
    if (!container) return;

    var c = payload.consensus || {};
    var rawScore = c.consensus_score !== undefined ? Number(c.consensus_score) : 50;
    var clampedScore = Math.min(100, Math.max(0, Math.round(rawScore || 0)));

    container.innerHTML = "";

    var wrapper = createEl("div", "consensus-wrapper");

    // 1. Top Hero: Consensus Score SVG Ring Gauge + Executive Narrative
    var hero = createEl("div", "consensus-hero");

    // Gauge Box
    var gaugeBox = createEl("div", "gauge-box");
    var svgContainer = createEl("div", "gauge-svg-container");
    svgContainer.id = "consensus-gauge";

    // P5-01: Accessible progressbar/meter attributes
    svgContainer.setAttribute("role", "meter");
    svgContainer.setAttribute("aria-label", "Literature Consensus Score");
    svgContainer.setAttribute("aria-valuenow", String(clampedScore));
    svgContainer.setAttribute("aria-valuemin", "0");
    svgContainer.setAttribute("aria-valuemax", "100");

    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 100 100");
    svg.setAttribute("class", "gauge-svg");
    svg.setAttribute("aria-hidden", "true");

    var bgCircle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    bgCircle.setAttribute("cx", "50");
    bgCircle.setAttribute("cy", "50");
    bgCircle.setAttribute("r", "45");
    bgCircle.setAttribute("class", "gauge-bg-circle");

    var fillCircle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    fillCircle.setAttribute("cx", "50");
    fillCircle.setAttribute("cy", "50");
    fillCircle.setAttribute("r", "45");
    fillCircle.setAttribute("class", "gauge-fill-circle");

    // Color stroke according to score
    var strokeColor = clampedScore >= 70 ? "#059669" : (clampedScore >= 45 ? "#D97706" : "#FF3366");
    fillCircle.style.stroke = strokeColor;

    svg.appendChild(bgCircle);
    svg.appendChild(fillCircle);
    svgContainer.appendChild(svg);

    var centerText = createEl("div", "gauge-center-text");
    var pctEl = createEl("div", "gauge-pct", clampedScore + "%");
    var capEl = createEl("div", "gauge-caption", "Consensus");
    centerText.appendChild(pctEl);
    centerText.appendChild(capEl);
    svgContainer.appendChild(centerText);

    // P5-01: Visually hidden description for screen readers
    var srOnly = createEl("span", "sr-only", "Scientific consensus score: " + clampedScore + " out of 100.");
    svgContainer.appendChild(srOnly);

    gaugeBox.appendChild(svgContainer);
    gaugeBox.appendChild(getVerdictPill(clampedScore));
    hero.appendChild(gaugeBox);

    // Executive Narrative Column
    var summaryCol = createEl("div", "consensus-summary-col");
    var title = createEl("h3", "consensus-summary-title", "Executive Literature Synthesis");
    var execQuote = createEl(
      "blockquote",
      "consensus-executive-quote",
      "“" + (c.executive_summary || "Evaluating cross-paper scientific evidence...") + "”"
    );

    var exportBar = createEl("div", "consensus-export-bar");

    var btnExportMd = createEl("button", "btn-export btn-export-primary", "📥 Export Synthesis Report (.md)");
    btnExportMd.type = "button";
    btnExportMd.id = "btn-export-markdown";
    btnExportMd.setAttribute("aria-label", "Download full literature synthesis report in Markdown format");
    btnExportMd.addEventListener("click", exportMarkdown);

    var btnExportJson = createEl("button", "btn-export", "💾 Export Raw JSON");
    btnExportJson.type = "button";
    btnExportJson.id = "btn-export-json";
    btnExportJson.setAttribute("aria-label", "Download raw AnalysisResult contract JSON payload");
    btnExportJson.addEventListener("click", exportJson);

    var stage4Model = (payload.models || []).find(function (m) {
      return m.role === "CONSENSUS_WRITER" || m.role === "REFEREE";
    });
    var pillText = stage4Model
      ? (stage4Model.model_id.replace(/^meta-llama\//i, "") + " (" + (stage4Model.role === "CONSENSUS_WRITER" ? "Stage 4" : "Referee") + ")")
      : "Llama-3.1-8B (Stage 4)";
    var modelPill = createEl("span", "llama-pill", pillText);

    exportBar.appendChild(btnExportMd);
    exportBar.appendChild(btnExportJson);
    exportBar.appendChild(modelPill);

    summaryCol.appendChild(title);
    summaryCol.appendChild(execQuote);
    summaryCol.appendChild(exportBar);
    hero.appendChild(summaryCol);

    wrapper.appendChild(hero);

    // 2. Breakdown Grid: Key Agreements & Top Contradictions
    var grid = createEl("div", "consensus-grid");

    // Agreements Card
    var agreeCard = createEl("div", "consensus-card");
    var agreeHeader = createEl("div", "consensus-card-header");
    var agreeTitle = createEl("h4", "consensus-card-heading", "Key Scientific Agreements");
    var agreeCount = createEl(
      "span",
      "queue-badge",
      (c.agreed_findings ? c.agreed_findings.length : 0) + " corroborated"
    );
    agreeHeader.appendChild(agreeTitle);
    agreeHeader.appendChild(agreeCount);
    agreeCard.appendChild(agreeHeader);

    var agreeList = createEl("div", "agreements-list");
    if (c.agreed_findings && c.agreed_findings.length > 0) {
      c.agreed_findings.forEach(function (finding) {
        var item = createEl("div", "agreement-item");
        var icon = createEl("span", "signal-icon", "✓");
        icon.style.color = "#059669";
        icon.style.fontWeight = "800";
        var text = createEl("div", "agreement-item-text", finding);
        item.appendChild(icon);
        item.appendChild(text);
        agreeList.appendChild(item);
      });
    } else {
      var emptyAgree = createEl("div", "cell-muted", "No high-confidence agreement claims detected.");
      agreeList.appendChild(emptyAgree);
    }
    agreeCard.appendChild(agreeList);
    grid.appendChild(agreeCard);

    // Contradictions Card
    var contraCard = createEl("div", "consensus-card");
    var contraHeader = createEl("div", "consensus-card-header");
    var contraTitle = createEl("h4", "consensus-card-heading", "Top Scientific Contradictions");
    var contraCount = createEl(
      "span",
      "queue-badge",
      (c.top_contradictions ? c.top_contradictions.length : 0) + " debates"
    );
    contraHeader.appendChild(contraTitle);
    contraHeader.appendChild(contraCount);
    contraCard.appendChild(contraHeader);

    var contraList = createEl("div", "contradictions-list");
    if (c.top_contradictions && c.top_contradictions.length > 0) {
      c.top_contradictions.forEach(function (contra) {
        var item = createEl("div", "contradiction-item");
        var head = createEl("div", "contradiction-headline", "⚠ " + contra.headline);
        item.appendChild(head);

        var actions = createEl("div", "contradiction-actions");
        var inspectBtn = createEl("button", "btn-inspect-edge", "Inspect in Dispute Drawer ↗");
        inspectBtn.type = "button";
        inspectBtn.setAttribute("aria-label", "Inspect contradiction dispute details for " + contra.edge_id);
        inspectBtn.addEventListener("click", function () {
          var edge = (payload.edges || []).find(function (e) { return e.edge_id === contra.edge_id; });
          if (edge && global.KairosDrawer && global.KairosDrawer.open) {
            global.KairosDrawer.open(edge, inspectBtn);
          }
        });
        actions.appendChild(inspectBtn);
        item.appendChild(actions);

        contraList.appendChild(item);
      });
    } else {
      var emptyContra = createEl("div", "cell-muted", "No direct contradictions found in this collection.");
      contraList.appendChild(emptyContra);
    }
    contraCard.appendChild(contraList);
    grid.appendChild(contraCard);

    wrapper.appendChild(grid);

    // 3. Research Gaps Section
    var gapsCard = createEl("div", "consensus-card");
    var gapsHeader = createEl("div", "consensus-card-header");
    var gapsTitle = createEl("h4", "consensus-card-heading", "Identified Research Gaps");
    var gapsBadge = createEl(
      "span",
      "queue-badge",
      (payload.gaps ? payload.gaps.length : 0) + " unaddressed"
    );
    gapsHeader.appendChild(gapsTitle);
    gapsHeader.appendChild(gapsBadge);
    gapsCard.appendChild(gapsHeader);

    var gapsContainer = createEl("div", "gaps-container");
    if (payload.gaps && payload.gaps.length > 0) {
      payload.gaps.forEach(function (gap) {
        var card = createEl("div", "gap-card");

        var cardHead = createEl("div", "gap-card-header");
        var gapTag = createEl("span", "signal-pill signal-gap");
        gapTag.appendChild(createEl("span", "signal-icon", "◌"));
        gapTag.appendChild(createEl("span", "signal-name", "Research Gap"));
        var idTag = createEl("span", "mono-tag", gap.gap_id);
        cardHead.appendChild(gapTag);
        cardHead.appendChild(idTag);
        card.appendChild(cardHead);

        var stmt = createEl("div", "gap-statement", gap.statement);
        card.appendChild(stmt);

        var reason = createEl("div", "gap-reason", gap.reason);
        card.appendChild(reason);

        if (gap.provenance && gap.provenance.verbatim_quote) {
          var prov = gap.provenance;
          var q = createEl("blockquote", "gap-quote", "“" + prov.verbatim_quote + "”");
          var cite = createEl("div", "cell-cite", "p. " + (prov.page_number || "—") + " · " + (prov.section || "Body"));
          card.appendChild(q);
          card.appendChild(cite);
        }

        gapsContainer.appendChild(card);
      });
    } else {
      gapsContainer.appendChild(createEl("div", "cell-muted", "No unaddressed research gaps identified."));
    }
    gapsCard.appendChild(gapsContainer);
    wrapper.appendChild(gapsCard);

    // 4. Actionable Next Steps
    var stepsCard = createEl("div", "consensus-card");
    var stepsHeader = createEl("div", "consensus-card-header");
    var stepsTitle = createEl("h4", "consensus-card-heading", "Recommended Next Research Steps");
    stepsHeader.appendChild(stepsTitle);
    stepsCard.appendChild(stepsHeader);

    var stepsList = createEl("div", "next-steps-list");
    if (c.recommended_next_steps && c.recommended_next_steps.length > 0) {
      c.recommended_next_steps.forEach(function (step, idx) {
        var item = createEl("div", "next-step-item");
        var num = createEl("span", "next-step-num", String(idx + 1));
        var text = createEl("div", "next-step-text", step);
        item.appendChild(num);
        item.appendChild(text);
        stepsList.appendChild(item);
      });
    } else {
      stepsList.appendChild(createEl("div", "cell-muted", "No specific follow-up experiments proposed."));
    }
    stepsCard.appendChild(stepsList);
    wrapper.appendChild(stepsCard);

    container.appendChild(wrapper);

    // Animate circular gauge fill from empty (283) to score offset (P5-05 clamped)
    requestAnimationFrame(function () {
      var circumference = 283;
      var offset = circumference - (circumference * (clampedScore / 100));
      fillCircle.style.strokeDashoffset = String(offset);
    });
  }

  global.KairosConsensus = {
    render: render,
    exportMarkdown: exportMarkdown,
    exportJson: exportJson,
    triggerFileDownload: triggerFileDownload
  };
})(window);
