/**
 * Kairos Paper Ingestion Hub & Queue Controller (Milestone P2)
 * Owner: Peace (Oluwanifemi)
 *
 * Implements drag-and-drop PDF ingestion, arXiv ID/URL validation, client-side
 * queue limits (2-10 papers, <=20MB per file), and an animated 4-stage open-weight
 * pipeline progress simulator.
 */
(function (global) {
  "use strict";

  var MAX_FILES = 10;
  var MIN_FILES = 2;
  var MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024; // 20 MB

  var stagedQueue = [
    {
      id: "sample_paper_1",
      name: "rajpurkar2017_chexnet.pdf",
      size: 2450000,
      type: "pdf",
      status: "ready"
    },
    {
      id: "sample_paper_2",
      name: "dosovitskiy2020_vit_radiology.pdf",
      size: 3120000,
      type: "pdf",
      status: "ready"
    },
    {
      id: "sample_paper_3",
      name: "cohen2020_covid_cxr_dataset.pdf",
      size: 1890000,
      type: "pdf",
      status: "ready"
    }
  ];

  var isSimulating = false;

  /**
   * Format bytes to human readable string (KB or MB)
   */
  function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    var k = 1024;
    var sizes = ["Bytes", "KB", "MB", "GB"];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  /**
   * Validate arXiv identifier or URL
   */
  function parseArXivId(input) {
    if (!input) return null;
    var trimmed = input.trim();
    var urlMatch = trimmed.match(/arxiv\.org\/(?:abs|pdf)\/(\d{4}\.\d{4,5}(?:v\d+)?)(?:\.pdf)?/i);
    if (urlMatch && urlMatch[1]) {
      return urlMatch[1];
    }
    var idMatch = trimmed.match(/^(\d{4}\.\d{4,5}(?:v\d+)?)$/);
    if (idMatch && idMatch[1]) {
      return idMatch[1];
    }
    return null;
  }

  /**
   * Update Staged Papers UI List
   */
  function renderQueue() {
    var listEl = document.getElementById("queue-list");
    var countBadge = document.getElementById("queue-count-badge");
    var synthesizeBtn = document.getElementById("btn-synthesize");

    if (!listEl) return;

    if (countBadge) {
      countBadge.textContent = stagedQueue.length + " / " + MAX_FILES;
    }

    if (synthesizeBtn) {
      if (stagedQueue.length < MIN_FILES || isSimulating) {
        synthesizeBtn.disabled = true;
        synthesizeBtn.title = "At least " + MIN_FILES + " papers required for synthesis";
      } else {
        synthesizeBtn.disabled = false;
        synthesizeBtn.title = "Synthesize " + stagedQueue.length + " papers";
      }
    }

    listEl.innerHTML = "";

    if (stagedQueue.length === 0) {
      var emptyEl = document.createElement("li");
      emptyEl.className = "queue-empty";
      emptyEl.textContent = "No papers staged. Drag and drop PDFs or add an arXiv ID above.";
      listEl.appendChild(emptyEl);
      return;
    }

    stagedQueue.forEach(function (paper, index) {
      var item = document.createElement("li");
      item.className = "queue-item";

      var left = document.createElement("div");
      left.className = "queue-item-left";

      var chip = document.createElement("div");
      chip.className = "paper-chip";
      chip.textContent = "P" + (index + 1);

      var meta = document.createElement("div");
      meta.className = "queue-item-meta";

      var name = document.createElement("div");
      name.className = "queue-item-name";
      name.textContent = paper.name;

      var size = document.createElement("div");
      size.className = "queue-item-size";
      size.textContent = formatBytes(paper.size) + " · " + paper.status.toUpperCase();

      meta.appendChild(name);
      meta.appendChild(size);

      left.appendChild(chip);
      left.appendChild(meta);

      var removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "btn-remove";
      removeBtn.innerHTML = "&times;";
      removeBtn.disabled = isSimulating;
      removeBtn.title = "Remove paper from queue";
      removeBtn.setAttribute("aria-label", "Remove " + paper.name);
      removeBtn.addEventListener("click", function () {
        removePaper(index);
      });

      item.appendChild(left);
      item.appendChild(removeBtn);
      listEl.appendChild(item);
    });
  }

  /**
   * Add a file to staged queue with validation
   */
  function addFile(file) {
    var feedbackEl = document.getElementById("ingest-feedback");
    if (isSimulating) return false;

    if (stagedQueue.length >= MAX_FILES) {
      if (feedbackEl) {
        feedbackEl.textContent = "Maximum of " + MAX_FILES + " papers allowed in this session.";
      }
      return false;
    }

    var isPdf = file.name.toLowerCase().endsWith(".pdf") || file.type === "application/pdf";
    if (!isPdf) {
      if (feedbackEl) {
        feedbackEl.textContent = "Only PDF documents (.pdf) are supported.";
      }
      return false;
    }

    if (file.size <= 0 || file.size > MAX_FILE_SIZE_BYTES) {
      if (feedbackEl) {
        feedbackEl.textContent = file.size <= 0
          ? "File \"" + file.name + "\" is empty (0 bytes)."
          : "File \"" + file.name + "\" exceeds the 20MB limit.";
      }
      return false;
    }

    var isDuplicate = stagedQueue.some(function (p) {
      return p.name.toLowerCase() === file.name.toLowerCase();
    });
    if (isDuplicate) {
      if (feedbackEl) {
        feedbackEl.textContent = "File \"" + file.name + "\" is already staged in the queue.";
      }
      return false;
    }

    stagedQueue.push({
      id: "paper_" + Date.now() + "_" + Math.random().toString(36).substr(2, 4),
      name: file.name,
      size: file.size,
      type: "pdf",
      file: file,
      status: "ready"
    });

    renderQueue();
    return true;
  }

  /**
   * Remove paper from staged queue
   */
  function removePaper(index) {
    if (isSimulating) return;
    if (index >= 0 && index < stagedQueue.length) {
      stagedQueue.splice(index, 1);
      var feedbackEl = document.getElementById("ingest-feedback");
      if (feedbackEl) feedbackEl.textContent = "";
      renderQueue();
    }
  }

  /**
   * Add arXiv paper
   */
  function addArXivPaper(inputStr) {
    if (isSimulating) return false;
    var feedbackEl = document.getElementById("ingest-feedback");
    var arxivId = parseArXivId(inputStr);

    if (!arxivId) {
      if (feedbackEl) {
        feedbackEl.textContent = "Invalid arXiv ID. Please use format YYMM.NNNNN (e.g. 2309.12345).";
      }
      return false;
    }

    if (stagedQueue.length >= MAX_FILES) {
      if (feedbackEl) {
        feedbackEl.textContent = "Maximum of " + MAX_FILES + " papers reached.";
      }
      return false;
    }

    var candidateName = "arXiv:" + arxivId + ".pdf";
    var isDuplicate = stagedQueue.some(function (p) {
      return p.name.toLowerCase() === candidateName.toLowerCase();
    });
    if (isDuplicate) {
      if (feedbackEl) {
        feedbackEl.textContent = candidateName + " is already in the staged queue.";
      }
      return false;
    }

    if (feedbackEl) feedbackEl.textContent = "";

    stagedQueue.push({
      id: "arxiv_" + arxivId.replace(".", "_"),
      name: candidateName,
      size: 1420000,
      type: "arxiv",
      arxivId: arxivId,
      status: "ready"
    });

    renderQueue();
    return true;
  }

  /**
   * Multi-stage Open-Weight Pipeline Progress Simulator
   */
  function simulatePipeline() {
    if (isSimulating) return;
    var feedbackEl = document.getElementById("ingest-feedback");
    if (stagedQueue.length < MIN_FILES) {
      if (feedbackEl) {
        feedbackEl.textContent = "Please stage at least 2 papers to perform cross-paper synthesis.";
      }
      return;
    }

    if (feedbackEl) feedbackEl.textContent = "";
    isSimulating = true;
    renderQueue();

    var card = document.getElementById("pipeline-card");
    var fill = document.getElementById("pipeline-progress-fill");
    var statusText = document.getElementById("pipeline-status-text");
    var btn = document.getElementById("btn-synthesize");

    if (card) card.hidden = false;
    if (btn) btn.disabled = true;

    var stages = [
      {
        num: 1,
        stepId: "pstep-1",
        label: "Stage 1/4: Ingesting & Chunking " + stagedQueue.length + " PDFs (pdftotext)...",
        progress: 25,
        duration: 900
      },
      {
        num: 2,
        stepId: "pstep-2",
        label: "Stage 2/4: Extracting structured claims via Llama-3.1-8B-Instruct...",
        progress: 55,
        duration: 1100
      },
      {
        num: 3,
        stepId: "pstep-3",
        label: "Stage 3/4: Pre-filtering candidate pairs with BAAI/bge-small-en-v1.5...",
        progress: 80,
        duration: 900
      },
      {
        num: 4,
        stepId: "pstep-4",
        label: "Stage 4/4: NLI Contradiction Refereeing & Consensus scoring...",
        progress: 100,
        duration: 1000
      }
    ];

    function runStage(idx) {
      if (idx >= stages.length) {
        if (statusText) statusText.textContent = "Synthesis complete! Cross-paper evidence matrix ready.";
        isSimulating = false;
        renderQueue();

        setTimeout(function () {
          if (global.KairosApp && global.KairosApp.navigateToPage) {
            global.KairosApp.navigateToPage("matrix", true);
          } else if (global.KairosApp && global.KairosApp.switchView) {
            global.KairosApp.switchView("matrix", true);
            var workspaceSection = document.getElementById("workspace");
            if (workspaceSection) {
              workspaceSection.scrollIntoView({ behavior: "smooth" });
            }
          }
          if (global.KairosMatrix && global.KairosMatrix.applyResearchObjective) {
            global.KairosMatrix.applyResearchObjective(global.KAIROS_RESEARCH_OBJECTIVE);
          }
        }, 600);
        return;
      }

      var current = stages[idx];
      if (fill) fill.style.width = current.progress + "%";
      if (statusText) statusText.textContent = current.label;

      stages.forEach(function (s, sIdx) {
        var el = document.getElementById(s.stepId);
        if (el) {
          if (sIdx < idx) {
            el.className = "pipeline-step complete";
          } else if (sIdx === idx) {
            el.className = "pipeline-step active";
          } else {
            el.className = "pipeline-step";
          }
        }
      });

      setTimeout(function () {
        runStage(idx + 1);
      }, current.duration);
    }

    runStage(0);
  }

  function updateStageSteps(stage) {
    var stageMap = {
      INGESTION: 1,
      EXTRACTION: 2,
      EMBEDDING: 3,
      CLUSTERING: 3,
      REFEREE: 4,
      CONSENSUS: 4
    };
    var activeNum = stageMap[stage] || 1;
    [1, 2, 3, 4].forEach(function (num) {
      var el = document.getElementById("pstep-" + num);
      if (el) {
        if (num < activeNum) el.className = "pipeline-step complete";
        else if (num === activeNum) el.className = "pipeline-step active";
        else el.className = "pipeline-step";
      }
    });
  }

  /**
   * Dispatches live synthesis job to FastAPI / Render backend and streams SSE progress
   */
  async function runLivePipeline(baseUrl) {
    isSimulating = true;
    renderQueue();

    var card = document.getElementById("pipeline-card");
    var fill = document.getElementById("pipeline-progress-fill");
    var statusText = document.getElementById("pipeline-status-text");
    var btn = document.getElementById("btn-synthesize");

    if (card) card.hidden = false;
    if (btn) btn.disabled = true;
    if (statusText) statusText.textContent = "Dispatching analysis job to open-weight pipeline...";

    var formData = new FormData();
    var arxivIds = [];
    stagedQueue.forEach(function (p) {
      if (p.file) {
        formData.append("files", p.file, p.name);
      } else if (p.arxivId) {
        arxivIds.push(p.arxivId);
      }
    });

    if (arxivIds.length > 0) {
      formData.append("arxiv_ids", JSON.stringify(arxivIds));
    }

    var submitUrl = baseUrl.replace(/\/$/, "") + "/api/v1/analyze";
    var res = await fetch(submitUrl, {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      throw new Error("Analysis job rejected with HTTP " + res.status);
    }

    var jobData = await res.json();
    var analysisId = jobData.analysis_id;

    return new Promise(function (resolve, reject) {
      var eventsUrl = baseUrl.replace(/\/$/, "") + "/api/v1/analyze/" + encodeURIComponent(analysisId) + "/events";
      var eventSource = new EventSource(eventsUrl);

      eventSource.addEventListener("progress", function (e) {
        try {
          var data = JSON.parse(e.data);
          if (fill && data.progress_pct !== undefined) {
            fill.style.width = data.progress_pct + "%";
          }
          if (statusText && data.message) {
            statusText.textContent = data.message;
          }
          if (data.stage) {
            updateStageSteps(data.stage);
          }
        } catch (_err) {}
      });

      eventSource.addEventListener("complete", async function (e) {
        eventSource.close();
        try {
          var eventPayload = JSON.parse(e.data);
          var payload = eventPayload;
          if (!payload || !Array.isArray(payload.papers)) {
            var resUrl = baseUrl.replace(/\/$/, "") + "/api/v1/analyze/" + encodeURIComponent(analysisId) + "?raw=true";
            var finalRes = await fetch(resUrl, { headers: { Accept: "application/json" } });
            if (!finalRes.ok) throw new Error("Failed to fetch completed analysis result");
            payload = await finalRes.json();
            if (payload && payload.result && Array.isArray(payload.result.papers)) {
              payload = payload.result;
            }
          }
          if (fill) fill.style.width = "100%";
          if (statusText) statusText.textContent = "Live synthesis complete! Rendering evidence matrix...";
          isSimulating = false;
          renderQueue();

          if (global.KairosApp && global.KairosApp.loadPayload) {
            global.KairosApp.loadPayload(payload, {
              preset_id: payload.preset_id || "live_analysis",
              title: "Live Analysis (" + payload.papers.length + " papers)"
            });
          }
          if (global.KairosApp && global.KairosApp.navigateToPage) {
            global.KairosApp.navigateToPage("matrix", true);
          }
          if (global.KairosMatrix && global.KairosMatrix.applyResearchObjective) {
            global.KairosMatrix.applyResearchObjective(global.KAIROS_RESEARCH_OBJECTIVE);
          }
          resolve(payload);
        } catch (err) {
          reject(err);
        }
      });

      eventSource.addEventListener("error", function () {
        eventSource.close();
        reject(new Error("SSE connection error"));
      });
    });
  }

  /**
   * Orchestrates live synthesis or falls back to simulation
   */
  async function synthesizePapers() {
    if (isSimulating) return;
    var feedbackEl = document.getElementById("ingest-feedback");
    if (stagedQueue.length < MIN_FILES) {
      if (feedbackEl) {
        feedbackEl.textContent = "Please stage at least 2 papers to perform cross-paper synthesis.";
      }
      return;
    }

    var realInputsCount = stagedQueue.filter(function (p) { return p.file || p.arxivId; }).length;
    var baseUrl = global.KairosApi && global.KairosApi.getBaseUrl ? global.KairosApi.getBaseUrl() : "https://kairos-yo50.onrender.com";

    if (realInputsCount >= MIN_FILES) {
      try {
        await runLivePipeline(baseUrl);
        return;
      } catch (err) {
        console.warn("Live synthesis unreachable or failed, falling back to simulator:", err);
      }
    }

    simulatePipeline();
  }

  /**
   * Bind DOM Events
   */
  function init() {
    var dropzone = document.getElementById("dropzone");
    var fileInput = document.getElementById("file-input");
    var arxivInput = document.getElementById("arxiv-input");
    var arxivBtn = document.getElementById("btn-add-arxiv");
    var synthesizeBtn = document.getElementById("btn-synthesize");
    var feedbackEl = document.getElementById("ingest-feedback");

    if (dropzone && fileInput) {
      dropzone.addEventListener("click", function () {
        if (!isSimulating) fileInput.click();
      });

      dropzone.addEventListener("keydown", function (e) {
        if ((e.key === "Enter" || e.key === " ") && !isSimulating) {
          e.preventDefault();
          fileInput.click();
        }
      });

      fileInput.addEventListener("change", function () {
        if (fileInput.files && fileInput.files.length > 0) {
          if (feedbackEl) feedbackEl.textContent = "";
          for (var i = 0; i < fileInput.files.length; i++) {
            addFile(fileInput.files[i]);
          }
          fileInput.value = "";
        }
      });

      dropzone.addEventListener("dragover", function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (!isSimulating) dropzone.classList.add("dragover");
      });

      dropzone.addEventListener("dragleave", function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("dragover");
      });

      dropzone.addEventListener("drop", function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("dragover");

        if (!isSimulating && e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          if (feedbackEl) feedbackEl.textContent = "";
          for (var i = 0; i < e.dataTransfer.files.length; i++) {
            addFile(e.dataTransfer.files[i]);
          }
        }
      });
    }

    if (arxivBtn && arxivInput) {
      arxivBtn.addEventListener("click", function () {
        if (arxivInput.value) {
          if (addArXivPaper(arxivInput.value)) {
            arxivInput.value = "";
          }
        }
      });

      arxivInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          if (arxivInput.value) {
            if (addArXivPaper(arxivInput.value)) {
              arxivInput.value = "";
            }
          }
        }
      });
    }

    if (synthesizeBtn) {
      synthesizeBtn.addEventListener("click", function () {
        synthesizePapers();
      });
    }

    // Bind Systematic Review Objective input and chips
    var objectiveInput = document.getElementById("research-objective-input");
    var objectiveChips = Array.prototype.slice.call(
      document.querySelectorAll(".objective-chip")
    );

    if (objectiveInput) {
      objectiveInput.addEventListener("input", function (e) {
        global.KAIROS_RESEARCH_OBJECTIVE = e.target.value.trim();
      });
    }

    objectiveChips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        objectiveChips.forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        var focus = chip.getAttribute("data-focus");
        var chipText = chip.textContent;
        if (objectiveInput) {
          objectiveInput.value = chipText;
        }
        global.KAIROS_RESEARCH_OBJECTIVE = focus;
      });
    });

    renderQueue();
  }

  global.KairosIngest = {
    init: init,
    addFile: addFile,
    addArXivPaper: addArXivPaper,
    removePaper: removePaper,
    simulatePipeline: simulatePipeline,
    synthesizePapers: synthesizePapers,
    getQueue: function () {
      return stagedQueue.slice();
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window);
