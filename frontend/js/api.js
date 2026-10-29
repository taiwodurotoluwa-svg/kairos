/**
 * Kairos Frontend API & Fixture Client (Milestone P1)
 * Owner: Peace (Oluwanifemi)
 *
 * Loads pre-analysed research corpus fixtures from ./fixtures/*.json in P1-P4
 * with zero failed network requests, and supports live FastAPI backend resolution
 * for Milestone P5. Validates required AnalysisResult contract keys.
 */
(function (global) {
  "use strict";

  var PRESET_REGISTRY = {
    radiology: {
      preset_id: "radiology",
      file: "./fixtures/demo_radiology_8papers.json",
      title: "Chest X-Ray Pneumonia Detection (CNN vs ViT vs Hybrid)"
    },
    demo_radiology_8papers: {
      preset_id: "radiology",
      file: "./fixtures/demo_radiology_8papers.json",
      title: "Chest X-Ray Pneumonia Detection (CNN vs ViT vs Hybrid)"
    },
    llm_quantization: {
      preset_id: "llm_quantization",
      file: "./fixtures/demo_llm_quantization_6papers.json",
      title: "LLM 4-Bit Quantization Trade-offs (GPTQ, AWQ, SmoothQuant, QLoRA)"
    },
    demo_llm_quantization_6papers: {
      preset_id: "llm_quantization",
      file: "./fixtures/demo_llm_quantization_6papers.json",
      title: "LLM 4-Bit Quantization Trade-offs (GPTQ, AWQ, SmoothQuant, QLoRA)"
    },
    microgrids: {
      preset_id: "microgrids",
      file: "./fixtures/demo_microgrids_6papers.json",
      title: "Decentralized Energy Scheduling for Islanded Microgrids (RL vs MPC)"
    },
    demo_microgrids_6papers: {
      preset_id: "microgrids",
      file: "./fixtures/demo_microgrids_6papers.json",
      title: "Decentralized Energy Scheduling for Islanded Microgrids (RL vs MPC)"
    },
    contract_sample: {
      preset_id: "contract_sample",
      file: "./fixtures/contract_sample.json",
      title: "Contract Baseline Verification Sample (4-Bit Quantization)"
    }
  };

  var REQUIRED_TOP_KEYS = [
    "schema_version",
    "preset_id",
    "fixture_provenance",
    "papers",
    "claims",
    "clusters",
    "edges",
    "gaps",
    "consensus",
    "stats",
    "models"
  ];

  /**
   * Validates that a loaded payload conforms to the AnalysisResult contract shape.
   * @param {Object} payload
   */
  function validateAnalysisResult(payload) {
    if (!payload || typeof payload !== "object") {
      throw new Error("Invalid AnalysisResult payload: expected JSON object.");
    }
    for (var i = 0; i < REQUIRED_TOP_KEYS.length; i++) {
      var key = REQUIRED_TOP_KEYS[i];
      if (!(key in payload)) {
        throw new Error("Contract validation failed: missing required field '" + key + "'.");
      }
    }
    if (!Array.isArray(payload.papers) || !Array.isArray(payload.claims) || !Array.isArray(payload.edges)) {
      throw new Error("Contract validation failed: papers, claims, and edges must be arrays.");
    }
    return payload;
  }

  var activeApiMode = "local";

  /**
   * Returns current API mode ("local" or "live").
   */
  function getApiMode() {
    return activeApiMode;
  }

  /**
   * Sets current API mode.
   * @param {string} mode - "local" or "live"
   */
  function setApiMode(mode) {
    activeApiMode = mode === "live" ? "live" : "local";
    global.KAIROS_API_MODE = activeApiMode;
    return activeApiMode;
  }

  var healthCheckController = null;

  /**
   * Checks whether the live FastAPI backend is reachable and healthy on /api/v1/health.
   * Cancels any pending in-flight probe to prevent race conditions (P5-03).
   * Times out after 2000ms and fails cleanly without uncaught console errors.
   * @param {string} [baseUrl]
   * @returns {Promise<{online: boolean, data?: Object, aborted?: boolean, error?: any}>}
   */
  async function checkLiveBackendHealth(baseUrl) {
    if (healthCheckController) {
      try {
        healthCheckController.abort();
      } catch (_e) {}
    }
    healthCheckController = typeof AbortController !== "undefined" ? new AbortController() : null;
    var currentCtrl = healthCheckController;

    var url = (baseUrl || global.KAIROS_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "") + "/api/v1/health";
    var timer = currentCtrl ? setTimeout(function () { currentCtrl.abort(); }, 2000) : null;
    try {
      var res = await fetch(url, {
        headers: { Accept: "application/json" },
        signal: currentCtrl ? currentCtrl.signal : undefined
      });
      if (timer) clearTimeout(timer);
      if (res.ok) {
        var data = await res.json();
        return { online: true, data: data };
      }
      return { online: false, status: res.status };
    } catch (err) {
      if (timer) clearTimeout(timer);
      if (err && err.name === "AbortError") {
        return { online: false, aborted: true };
      }
      return { online: false, error: err };
    } finally {
      if (healthCheckController === currentCtrl) {
        healthCheckController = null;
      }
    }
  }

  /**
   * Resolves preset metadata from either a preset_id or a fixture filename stem.
   * @param {string} key
   */
  function resolvePresetMeta(key) {
    var normalized = String(key || "radiology").trim();
    return PRESET_REGISTRY[normalized] || null;
  }

  /**
   * Fetches and validates a preset AnalysisResult payload.
   * Defaults to local ./fixtures/*.json in P1-P4 so the browser console remains
   * completely free of connection-refused errors when the backend is not running.
   *
   * @param {string} presetKey - e.g. "radiology" or "demo_radiology_8papers"
   * @param {Object} [options]
   * @returns {Promise<{payload: Object, meta: Object, source: string}>}
   */
  async function fetchPreset(presetKey, options) {
    var opts = options || {};
    var meta = resolvePresetMeta(presetKey);
    if (!meta) {
      throw new Error("Unknown preset identifier: '" + String(presetKey) + "'.");
    }

    var apiMode = opts.mode || activeApiMode || global.KAIROS_API_MODE || "local";
    var baseUrl = opts.baseUrl || global.KAIROS_API_BASE_URL || "http://localhost:8000";

    if (apiMode === "live") {
      try {
        var liveResponse = await fetch(
          baseUrl.replace(/\/$/, "") + "/api/v1/demo/" + encodeURIComponent(meta.preset_id),
          { headers: { Accept: "application/json" } }
        );
        if (liveResponse.ok) {
          var liveData = validateAnalysisResult(await liveResponse.json());
          return { payload: liveData, meta: meta, source: "live" };
        }
      } catch (_err) {
        /* Fall back cleanly to bundled local fixture when live server is unreachable */
      }
    }

    var response = await fetch(meta.file, {
      headers: { Accept: "application/json" },
      cache: "no-cache"
    });

    if (!response.ok) {
      throw new Error(
        "Failed to load local fixture '" + meta.file + "' (HTTP " + response.status + ")."
      );
    }

    var data = validateAnalysisResult(await response.json());
    return { payload: data, meta: meta, source: "fixture" };
  }

  global.KairosApi = {
    PRESET_REGISTRY: PRESET_REGISTRY,
    resolvePresetMeta: resolvePresetMeta,
    validateAnalysisResult: validateAnalysisResult,
    fetchPreset: fetchPreset,
    getApiMode: getApiMode,
    setApiMode: setApiMode,
    checkLiveBackendHealth: checkLiveBackendHealth
  };
})(window);
