/**
 * Kairos Paper Ingestion Hub & Queue Controller (Milestone P2 — Argon 4 Patched)
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
          if (global.KairosApp && global.KairosApp.switchView) {
            global.KairosApp.switchView("matrix", true);
            var workspaceSection = document.getElementById("workspace");
            if (workspaceSection) {
              workspaceSection.scrollIntoView({ behavior: "smooth" });
            }
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
        simulatePipeline();
      });
    }

    renderQueue();
  }

  global.KairosIngest = {
    init: init,
    addFile: addFile,
    addArXivPaper: addArXivPaper,
    removePaper: removePaper,
    simulatePipeline: simulatePipeline,
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
