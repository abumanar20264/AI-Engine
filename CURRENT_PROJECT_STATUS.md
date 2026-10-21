# AI-Engine — Current Project Status and Implementation Gaps

**Reviewed:** 2026-10-21 (after cleanup and commit preparation)
**Repository:** `abumanar20264/AI-Engine`
**Baseline commit:** `main` at `07f71bca201c1411841e8e160f96b4f85d29d89c` (implementation changes are currently uncommitted)
**Purpose:** Current implementation snapshot. This file supplements, but does not replace, the chronological [PROJECT_WORK_ARCHIVE.md](./PROJECT_WORK_ARCHIVE.md).

## Executive status

AI-Engine now has a **source-integrated, not yet remotely re-verified, saved-project video workflow**. The task runner snapshots the submitted project, builds and verifies its Blender scene on Kaggle, renders the project-configured MP4, checks H.264 metadata/full decode/visible motion, retrieves the `.blend`, MP4, and report, and verifies the downloaded MP4 SHA-256 before success. The control UI exposes the verified local MP4 for download. Local tests cover these contracts, recovery snapshots, and the download route.

This source change has **not** yet been exercised as a new Kaggle run; end-to-end production is therefore not yet proven. Existing v14/v16 runs verified scene creation and physics only, and the independent fixed-scene render does not prove this new integration. Audio-required projects are rejected before submission and audio is explicitly `NOT_AVAILABLE`; other experiment types, human release QA, and performance/cost qualification remain open. v16 artifact recovery previously hit Kaggle HTTP 429; the new output retrieval path still needs a successful remote validation run.

## Implemented and evidenced

| Component | Current evidence | Boundary |
|---|---|---|
| Blender runtime recovery | Archive and manifest verification, extraction into writable Kaggle storage, restored-tree checks | Tested path only; do not bypass integrity checks |
| Blender / EEVEE | Blender 4.0.2 CPU-only compatibility path passed in Kaggle Kernel v8, run `360689524` | Does not prove every runtime profile or production scale |
| Rigid-body smoke test | Small physics test passed in the recorded preflight/production runner | Not a general scenario-driven simulation service |
| Fixed-scene video render | Five-second 720×1280, 24 FPS, 120-frame H.264 MP4 passed checks in historical Kernel v8 | Independent test scene; does not prove the new saved-project render path |
| Project/scenario contract and local persistence | Version-1 rigid-body-chain project document, validation, JSON save/load/list, atomic replacement, and standard-library tests | Connected to the local UI and consumed by the actual v15 Kaggle test; one Windows symlink test is skipped because symlink creation is not permitted |
| Local project control UI | Loopback UI edits/saves projects, starts tasks, shows reports/checksums, and serves a verified local MP4 download | New remote render and retrieval path has not yet been exercised against Kaggle |
| Saved project to Blender scene | Kaggle Kernels v14, v15, and v16 reports verified Blender 4.0.2, `.blend` reopen, EEVEE, rigid bodies, and 0.663354 m target movement | One bounded rigid-body-chain case per run. Historical v16 `.blend` remains unrecovered after HTTP 429; the newly implemented render/retrieval path has not yet been remotely exercised. |
| Task lifecycle and Kaggle transfer | Success now requires matching task/project identity, verified MP4 metadata, hash/size/report, local artifact path, and explicit audio status; task recovery uses an immutable input snapshot | Local mocked retrieval/recovery tests pass. New Kaggle output filtering and real artifact download await a remote run; historical records remain unchanged |
| Performance measurement | Optional 8/4/2 EEVEE benchmark evidence from v10 run `360710783` and v12 run `360738597` | Reduced-sample quality is not approved; keep default at 8 |
| Technical QA | Per-task source gate checks project settings, H.264, full decode, motion, identity, and downloaded SHA-256; CI tests Windows/Linux on Python 3.10/3.12 | No remote run of the integrated gate and no human visual/audio/rights release gate |
| Operations documentation | Engine and production operations specifications, archive, QA rules and templates | Procedural documentation only; it does not provide the missing application |

### Benchmark evidence boundary

- v10 log/report evidence: render plus MP4-write times of 511.823 / 268.390 / 146.320 seconds for 8/4/2 samples.
- v12 Kaggle Logs: 492.430 / 258.884 / 141.481 seconds for 8/4/2 samples.
- v12 report and comparison image were visible by filename in Kaggle Output, but targeted retrieval repeatedly returned HTTP 429. Original report contents, hashes and full-resolution image pixels were not independently validated locally.
- Therefore, 4/2 samples remain benchmark candidates only. The production default stays at 8 samples.

## Partially implemented and missing from the tracked product

The project/scenario contract, local persistence, and local control UI now provide a tested project-editing and task-submission workflow. The remaining gaps below describe capabilities not yet verified as integrated implementations in the current local worktree.

| Component | Current state / missing deliverable | Acceptance evidence |
|---|---|---|
| Project model and persistence | **Partial:** version-1 project IDs, scenario/settings, validation, JSON persistence, task/error/output references. No migration flow. | Store and UI integration tests pass; future schema migration tests when a new version is introduced |
| Scenario input | **Partial:** rigid-body-chain contract and supported object/camera/video settings can be edited in the local UI; no broader experiment types | Browser flow and valid/invalid contract tests pass |
| Control UI | **Partial:** create/open/edit/save, field validation, start a tracked task, and show persisted status/events/errors/results. | Browser create/save/start/status flow exercised; one actual task ended failed because Kaggle returned `CANCEL_ACKNOWLEDGED` |
| Scenario-to-scene adapter | **Implemented and runtime-tested for one bounded case:** v14, v15, and v16 reports record saved-project scene generation, `.blend` reopen, EEVEE settings, and measured post-contact target motion. | v16 report and task record verify the remote scene and Blender checks; the `.blend` was not recovered locally |
| Job orchestration | **Implemented in source; remote acceptance pending:** CPU-only submission, immutable project snapshot, scene/physics check, render, MP4 validation, output retrieval, local hash verification, and restart recovery | Local tests use mocked Kaggle output; do not claim end-to-end success until a new remote run passes |
| Audio pipeline | Unsupported; audio-required projects are rejected before submission and successful reports state `NOT_AVAILABLE` | Asset licensing, sync, mux, audio stream, and playback verification are not implemented |
| Final delivery | Verified MP4 and `.blend` are retrieved into task-scoped storage; UI exposes video download and reports | Versioned release manifest, preview, human QA, and publication-ready delivery remain open |
| Integrated release QA | Per-project visual/physics/audio/rights/export checklist with explicit PASS/FAIL/NOT APPLICABLE | Release blocked when a mandatory gate fails |

## Documentation conflicts resolved in this review

- The gap register previously said no Kaggle compatibility test or video render had occurred. That was true for the October 20 audit but is stale after Kernel v8 and later benchmark runs. Its active status now reflects the recorded test scope.
- The product foundation previously described Kaggle compatibility as unvalidated and EEVEE as provisional pending the first runtime test. Those active statements are now scoped to the passed v8 CPU-only path; broader production integration remains unvalidated.
- Historical change-log and archive entries are intentionally retained as records of what was known at their dates. They are not rewritten to imply that later evidence existed earlier.
- The README now distinguishes the technical spike from the missing user-facing product and links to this status file.

## Recommended build order

1. **Remote acceptance:** run one new UI-started Kaggle job and verify scene, physics, render, output retrieval, local SHA-256, UI download, and the 720×1280/24 FPS/120-frame/five-second acceptance profile.
2. **Visual/release QA:** review the downloaded video, add a versioned delivery manifest and explicit visual/rights outcomes, and retain 8 EEVEE samples until quality is approved.
3. **Audio:** implement licensed asset ingestion, synchronization, muxing, and playback verification before enabling audio-required projects.
4. **Scenario coverage:** add experiment types only with a versioned contract, scene builder, and tests; current support remains `rigid_body_chain`.
5. **Research/evidence policy:** keep competitor conclusions provisional until an auditable source ledger exists. Preserve historical runner outputs until an explicit evidence-retention policy is approved.

The task now has an end-to-end implementation path, but source and mocked tests do not replace remote acceptance evidence. The product remains limited to one rigid-body-chain scenario with no audio. Do not change the production default from 8 EEVEE samples until full-resolution visual review is completed.

## Generate a scene locally from a saved project (Blender required)

After saving a project in the UI, copy its displayed project UUID and run from PowerShell:

```powershell
.\.venv\Scripts\python.exe .\generate_project_scene.py "PASTE_PROJECT_UUID_HERE" --blender "C:\Tools\Blender 4.0\blender.exe"
```

Replace `PASTE_PROJECT_UUID_HERE` with the ID shown in the selected project's editor metadata and replace the example Blender path with the installed Blender 4.0.2 executable. This local CLI builds only a `.blend` file and JSON scene report; it does not evaluate physics or render. The UI task path is intended to perform verification and rendering on Kaggle, but has not yet been remotely run after implementation. Blender and `bpy` are unavailable in this local environment.

## Run the local project UI

1. From PowerShell, switch to `C:\AI-Engine`.
2. Start the UI with `.\.venv\Scripts\python.exe .\run_control_ui.py`.
3. Open `http://127.0.0.1:8765/` in a browser.
4. Choose **New project**, edit supported fields, and select **Save project**. Saved JSON projects are kept under `C:\AI-Engine\projects\`; that local-data directory is excluded from Git.
5. Select a project in **Saved projects** to reopen it. Start a CPU-only task to submit the saved project to Kaggle, verify its scene and physics, render and validate an MP4, retrieve artifacts, and show task reports. Audio-required projects are rejected until audio production is implemented. The task database is stored separately under `.ai-engine-task-state/`. Stop the local server with `Ctrl+C`.

The server binds only to loopback. It creates the project directory only when the first project is saved.

## Source-of-truth hierarchy

- **Current implementation status and gaps:** this file.
- **Editorial/product direction:** [REVIEW_AND_UPDATED_PROJECT_FOUNDATION.md](./REVIEW_AND_UPDATED_PROJECT_FOUNDATION.md).
- **Operational production requirements:** [PRODUCTION_OPERATIONS_SPECIFICATION.md](./PRODUCTION_OPERATIONS_SPECIFICATION.md).
- **Blender/Kaggle engine decision and runtime evidence:** [BLENDER_KAGGLE_ENGINE_SPECIFICATION.md](./BLENDER_KAGGLE_ENGINE_SPECIFICATION.md).
- **Section-by-section documentation audit:** [DOCUMENT_AUDIT_AND_GAP_REGISTER.md](./DOCUMENT_AUDIT_AND_GAP_REGISTER.md).
- **Source/evidence/output retention rules:** [ARTIFACT_RETENTION_POLICY.md](./ARTIFACT_RETENTION_POLICY.md).
- **Immutable-in-practice chronological work record (append-only):** [PROJECT_WORK_ARCHIVE.md](./PROJECT_WORK_ARCHIVE.md).

## Change log

### 1.0.5 — 2026-10-21
- Added saved-project Kaggle MP4 render/validation, task-bound output retrieval, SHA-256 checks, local UI downloads, immutable task snapshots, and success-state video requirements; local tests pass, remote acceptance is pending.
- Added cross-platform CI and refreshed the README/current-status boundary to keep historical evidence distinct from unverified integration.

### 1.0.4 — 2026-10-21
- Recorded the stable, source-controlled CPU-only Kaggle notebook template and the bounded v16 task lifecycle result.
- Clarified that remote scene verification is implemented for one test case, while local artifact recovery and end-to-end video/audio production remain incomplete.

### 1.0.2 — 2026-10-21
- Recorded the tested local control UI and its boundary: project editing and persistence only, with no rendering or Kaggle job integration.
- Updated the product gaps and next implementation step to the scenario-to-Blender adapter.

### 1.0.3 — 2026-10-21
- Recorded the SQLite-backed task lifecycle and UI-to-Kaggle submission path, including actual v15 Blender report evidence and the unresolved `CANCEL_ACKNOWLEDGED` terminal status.
- Kept the task marked failed, documented that the report was validated separately from captured logs, and clarified that no local `.blend`, video, or audio artifact was produced.

### 1.0.1 — 2026-10-21
- Recorded the tested version-1 project/scenario contract and local JSON persistence as a partial product foundation.
- Updated the remaining gaps and next implementation step without implying UI, Blender integration, or Kaggle orchestration exists.

### 1.0.0 — 2026-10-21
- Created a concise, current implementation snapshot grounded in the tracked repository and recorded Kaggle evidence.
- Separated implemented technical proof from missing product components and unresolved visual-quality evidence.
