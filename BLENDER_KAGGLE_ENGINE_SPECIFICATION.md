# AI-Engine — Blender Production Engine & Kaggle Operations Specification

**Document ID:** AI-ENGINE-BLENDER-KAGGLE-SPEC  
**Version:** 1.0.1

**Decision status:** **BLENDER APPROVED AS THE SOLE PRIMARY PRODUCTION ENGINE**  
**Operational status:** **NOT YET VALIDATED ON THE PROJECT'S KAGGLE RUNTIME**  
**Decision date:** 2026-10-20  
**Applies to:** Visual Physics Experiments — Satisfying Systems, Physics in Action, The Experiment  
**Parent product specification:** [REVIEW_AND_UPDATED_PROJECT_FOUNDATION.md](./REVIEW_AND_UPDATED_PROJECT_FOUNDATION.md)  
**Production procedure:** [PRODUCTION_OPERATIONS_SPECIFICATION.md](./PRODUCTION_OPERATIONS_SPECIFICATION.md)

> **Decision boundary:** Blender is the approved primary production engine for this project. This is an architecture decision, not a claim that Kaggle compatibility, render speed, output quality, or production economics have already been measured. A small compatibility gate remains mandatory before bulk production. Do not investigate or benchmark alternative engines unless Blender fails a documented mandatory requirement and separate approval is obtained.

## 1. Purpose and scope

This document establishes the selected engine, its role, operating requirements, Kaggle execution model, local-computer control workflow, storage rules, and acceptance gates.

The production product combines three editorial modes in one channel:

1. **Satisfying Systems / Oddly Satisfying:** deliberate visual order, rhythm, motion, transformation, and payoff.
2. **Physics in Action:** visually legible physical interactions such as rigid-body motion, collisions, rebounds, stacking, balance, and chain reactions.
3. **The Experiment:** a clear visual question or constraint, a controlled setup, and an observable result.

The common promise is:

**“Beautiful visual experiments that test how a system behaves and reveal a satisfying, surprising, or counterintuitive result.”**

The intended initial output is vertical YouTube Shorts. Long-form production may be considered later after the Shorts pilot provides evidence.

## 2. Engine decision

### 2.1 Approved engine

**Blender is the sole approved primary 3D scene, animation, simulation, and rendering environment.**

- **Scene authoring and procedural control:** Blender Python API (bpy).
- **Initial renderer:** EEVEE, **PROVISIONAL** until it passes the Kaggle compatibility gate.
- **Initial simulation domain:** rigid bodies, collision-driven motion, gravity, rebound, stacking, and controlled chain reactions.
- **Execution mode on Kaggle:** background/headless command-line execution where supported.
- **Post-processing:** use command-line tools only where available and compatible; keep their versions and licenses recorded. Do not assume a particular encoder or binary exists in a fresh notebook.
- **Project source of truth:** versioned Blender scene files, source scripts, scene parameters, logs, and QA records stored durably.

### 2.2 Why Blender fits this project

The decision is based on architectural fit, not on a completed performance benchmark:

- It combines procedural geometry, animation, materials, cameras, lighting, simulation, and rendering in one environment.
- Python scripting makes repeatable scene generation and batch execution possible.
- It can be used with a graphical interface for development or a background process for automation.
- A single reusable scene system can support many distinct experiments without requiring recurring character animation.
- It can preserve editable scene files as well as rendered outputs.

These are capability-based reasons. They do **not** establish that every scene will be fast, stable, physically accurate, or commercially successful.

### 2.3 Explicitly not approved yet

- Bulk production or unattended publishing.
- A final renderer configuration or quality preset.
- A guaranteed render time per frame or video.
- A claim that GPU rendering is always available on Kaggle.
- Complex fluid, soft-body, fracture, or high-object-count workflows as launch requirements.
- Any specific YouTube performance or revenue forecast.

## 3. Requirements and compatibility

### 3.1 Local development computer

Current reported hardware:

- GPU: NVIDIA GeForce GTX 1050 Ti, 4 GB VRAM.
- CPU: Intel Core i5-9400F, 6 cores.
- RAM: 8 GB.
- Operating system: Windows (exact build and driver version must be recorded before validation).

Expected local role:

- Write and maintain Python scripts and scene specifications.
- Create simple scenes and low-cost previews.
- Inspect scene files and debug geometry, timing, materials, and camera framing.
- Review outputs, perform lightweight editing, and manage archives.
- Prepare jobs and monitor Kaggle sessions through a browser.

This computer is near the practical memory floor for a multi-tool workflow. Keep browser tabs and background applications controlled when Blender is open. Do not assume that a complex simulation or high-resolution final render will be efficient locally.

### 3.2 Kaggle runtime

Kaggle is the planned primary compute environment for heavier simulation and rendering. Its actual runtime is variable and must be checked at the start of a job.

**Required checks for every new runtime or after a material environment change:**

1. Record the runtime OS and available CPU/RAM.
2. Determine whether a GPU was actually allocated; do not assume a T4 or any other accelerator.
3. Record GPU model, VRAM, driver/runtime information when a GPU is available.
4. Verify the Blender executable and exact version.
5. Run Blender in background mode and capture its exit code and log.
6. Confirm the chosen renderer initializes successfully in that runtime.
7. Verify that the intended output path is writable and that a test file can be read back.
8. Confirm that sufficient disk space remains for the scene, caches, frames, and exports.

If a GPU is not available, do not automatically fail the whole workflow: determine whether the scene can run acceptably on CPU. If the chosen renderer fails to initialize, capture the error and use the approved compatibility decision process rather than silently switching settings.

### 3.3 Blender system requirements

Consult the official requirements page before selecting or upgrading a version:

- [Blender — System Requirements](https://www.blender.org/download/requirements/)
- [Blender — Downloads](https://www.blender.org/download/)

General published requirements can change by Blender release and platform. The local machine's 8 GB RAM and 4 GB VRAM should be treated as constrained resources, not as a guarantee of smooth operation. Kaggle's compatibility depends on its own OS, graphics stack, drivers, allocated hardware, and notebook policies.

### 3.4 Version pinning

Before building reusable production scripts:

- Select one Blender version that runs successfully in the chosen Kaggle runtime and on the local computer to the extent needed for editing/review.
- Record the exact version and runtime details in the project environment record.
- Use that version consistently for production jobs.
- Do not upgrade Blender, change renderer, or change a major simulation setting in the middle of a production batch without recording the change and revalidating representative scenes.
- If local and Kaggle versions cannot be identical, record the mismatch and verify scene-file compatibility and output consistency explicitly.

The specific version is **NOT YET LOCKED**. Choose it after the compatibility check, not by assuming that the newest release is automatically the best choice.

## 4. Kaggle operating model

### 4.1 Core principle

Kaggle is a remote execution environment, not a permanent workstation or archive. The local computer controls the workflow through the Kaggle website and transfers source files and outputs. The heavy computation occurs in the cloud runtime.

The workflow must tolerate runtime interruption, quota limits, unavailable accelerators, and temporary storage.

### 4.2 Recommended job stages

1. **Prepare locally:** update the scene script, scene parameters, and job manifest.
2. **Transfer source:** upload the required files to a Kaggle notebook/session or retrieve a pinned project revision. Avoid uploading unnecessary archives and large assets.
3. **Preflight:** verify runtime, Blender version, dependencies, paths, storage, and available accelerator.
4. **Build scene:** generate or update the scene file from the versioned script and parameters.
5. **Save checkpoint:** save the scene file and scene parameters before expensive simulation/rendering.
6. **Run a short preview:** render a small frame range or low-quality preview before committing to a full job.
7. **Validate:** inspect logs, frame count, output dimensions, simulation behavior, and representative frames.
8. **Render final:** run only after the preview passes the required checks.
9. **Export and verify:** create the final video or intermediate frames, then verify that the file exists, has non-zero size, and can be opened/decoded.
10. **Archive:** copy required source files, logs, settings, and outputs to durable storage before the session expires.
11. **Record:** log elapsed time, failures, resource use where available, output paths, and QA status.

### 4.3 Headless execution

Blender supports command-line/background workflows. A representative command pattern is shown below. It is a **template**, not a ready-to-run command until the files, arguments, Blender path, and runtime environment exist.

    blender --background --python build_scene.py -- --config scene_config.json

For rendering a saved project, a pattern may look like this:

    blender --background scene.blend --render-output /path/to/frames/frame_#### --render-format PNG

Confirm the exact command-line options for the pinned Blender version. In a Kaggle notebook, the command will usually be invoked from a notebook cell using the actual executable path discovered in that session.

Capture stdout/stderr and the process exit code. Do not treat the presence of a partially written output file as a successful render.

### 4.4 GPU and renderer policy

- Do not assume that a Kaggle session always has a GPU.
- Do not assume that EEVEE will initialize successfully in every headless/cloud environment; test it in the actual runtime.
- Do not assume that Cycles GPU rendering is configured simply because a GPU is visible.
- First prove that the chosen renderer completes a minimal scene in the allocated runtime.
- Prefer the simplest renderer/settings that meet the project's visual requirements and pass repeatability checks.
- If the initial EEVEE path fails, diagnose the environment and compare a documented CPU or alternate supported configuration within Blender. Do not investigate other engines unless Blender fails a documented mandatory requirement and separate approval is obtained.

## 5. Local-computer control and file transfer

### 5.1 What “control from the local computer” means

The local computer is the operator's control station. Through a web browser, the operator can edit and run Kaggle notebook cells, monitor logs, stop or restart jobs, and download outputs. The simulation and render are executed by the remote runtime, not by the local GPU.

The workflow does **not** imply a permanent direct remote shell, continuous connection, or that a Kaggle session remains active after the browser is closed. Actual session persistence and controls depend on Kaggle's current interface and policies.

### 5.2 Source-of-truth layout

Use a structure like this in the repository:

    AI-Engine/
      README.md
      BLENDER_KAGGLE_ENGINE_SPECIFICATION.md
      PRODUCTION_OPERATIONS_SPECIFICATION.md
      production/
        engine/
          environment-manifest.md
          scripts/
            build_scene.py
            render_scene.py
            validate_output.py
          configs/
            scene_config.json
          templates/
          benchmarks/
        concepts/
          <concept_id>/
            scene_spec.yaml
            source/
            previews/
            renders/
            exports/
            logs/
            qa/

This is a proposed logical structure. Create files only when they are needed; do not commit large render outputs or caches to Git by default. Keep the source, small configs, manifests, and checksums in Git. Store large binary outputs in durable storage and record their location.

### 5.3 Transfer methods

Use the least complicated method suitable for the job:

- **Small source scripts/configs:** upload them to the notebook or retrieve a specific, known repository revision.
- **Reusable project code:** use the Git repository as the source of truth and pin the commit/revision used by each job.
- **Large assets or caches:** transfer only when needed and use a storage location appropriate for large files.
- **Final exports and logs:** download or copy them to durable storage before the Kaggle session ends.

Never place personal access tokens, Kaggle credentials, or other secrets in committed scripts, notebook output, or public logs. Use Kaggle's supported secret/credential mechanism when authentication is required. Grant the minimum required access.

### 5.4 Job manifest

Each job must record at least:

- Job ID and concept ID/version.
- Git commit or source revision.
- Blender version.
- Runtime OS and execution date.
- GPU model/availability, CPU/RAM/disk observations when available.
- Renderer and all non-default render settings.
- Scene config and random seed, where applicable.
- Input asset list and license/status.
- Output paths and filenames.
- Start/end time, exit code, and error summary.
- Validation and QA status.

## 6. Checkpoints, interruption, and recovery

Kaggle notebook runtimes and their working storage are not guaranteed to persist. Design every expensive task so it can be restarted without rebuilding everything from scratch.

**Required safeguards:**

- Save the scene source and its config before simulation or rendering.
- Write numbered frames or other resumable intermediates when practical.
- Separate scene generation, simulation/cache generation, rendering, and video assembly into distinct stages.
- Write logs to a file as well as notebook output.
- Use unique job directories so a new attempt does not overwrite the last known-good output.
- Verify every copied/downloaded artifact after transfer.
- Archive final sources, configs, caches that are required to reproduce the result, logs, and output checksums.
- Stop a job before its resource/session limit where possible; do not depend on last-minute saving.
- Never treat a temporary notebook working directory as the only copy of a deliverable.

A checkpoint is valid only if the file can be reopened or its contents can be verified, not merely because a save command was issued.

## 7. First compatibility gate — minimal test only

The goal is to establish feasibility without consuming significant GPU quota or committing to a large render.

### Gate A — Environment inspection

- [ ] Record runtime OS, CPU/RAM/disk, GPU availability/model/VRAM, and Blender version.
- [ ] Confirm the executable runs and reports the expected version.
- [ ] Confirm background mode works and produces a readable log.
- [ ] Confirm the intended output directory is writable.

### Gate B — Minimal scene

Create one simple scene containing a floor and a small number of rigid objects. The scene should include a fall or roll, one collision/rebound, a fixed camera, basic lighting, and a short timeline. Keep geometry and frame count low.

- [ ] Generate and save a scene file through Python.
- [ ] Run the intended renderer for a short, low-quality preview.
- [ ] Confirm expected frames are produced.
- [ ] Inspect several frames for missing objects, black frames, obvious simulation failures, or camera errors.
- [ ] Record wall-clock time, logs, and observed resource usage.
- [ ] Re-run once with the same inputs to check whether the result is acceptably repeatable.

### Gate C — Export and archive

- [ ] Export a short MP4 if a compatible encoder is available; otherwise preserve a verified frame sequence and record the missing dependency.
- [ ] Confirm the video/frame sequence can be opened and has the intended orientation and dimensions.
- [ ] Copy the scene file, scripts, config, logs, and output to durable storage.
- [ ] Confirm the archived copies are readable.

**Pass condition:** the complete minimal path succeeds, the output is inspectable, the source and parameters are recoverable, and runtime/version details are recorded.

**Fail condition:** Blender cannot start, the renderer cannot initialize, the scene cannot be saved/reopened, output is corrupt, or the job cannot be recovered. On failure, document the exact error and correct that specific issue before scaling up.

This gate is a small technical validation, not a multi-engine benchmark and not a full production test.

## 8. Quality and production limits

- Begin with rigid bodies, collisions, gravity, rebound, and small chain reactions.
- Use procedural motion when deterministic geometry or timing can produce a better and more repeatable result than a costly simulation.
- Increase object count, resolution, samples, and timeline length gradually.
- Keep simulation validation separate from visual polish.
- Do not label a stylized or unvalidated simulation as scientific evidence.
- For comparison videos, vary one intended independent variable at a time and record the controlled variables.
- Human review remains mandatory for originality, physical/causal coherence, framing, visual payoff, audio, and final export.
- A completed render is not equivalent to a publishable episode.

## 9. Operational acceptance criteria

A production setup is not ready for batch production until all of the following are true:

1. The pinned Blender version starts successfully in the chosen Kaggle runtime.
2. The chosen renderer completes the minimal scene without critical errors.
3. The scene can be generated from versioned scripts/configuration.
4. The output can be verified and reproduced within documented tolerances.
5. A failed/interrupted job can be resumed or safely restarted.
6. Source files, settings, logs, and outputs can be archived outside temporary runtime storage.
7. Actual processing time and resource use have been recorded for at least one representative scene.
8. The production team can explain which steps run locally and which run on Kaggle.
9. The production SOP quality gates and editorial originality gate remain in force.

Passing this gate establishes technical readiness for a **small controlled pilot only**. It does not establish market demand, virality, monetization, or the economics of scaled production.

## 10. References and evidence policy

Official Blender references:

- [Blender system requirements](https://www.blender.org/download/requirements/)
- [Blender downloads and releases](https://www.blender.org/download/)
- [Blender manual](https://docs.blender.org/manual/en/latest/)
- [Blender command-line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html)
- [Blender Python API](https://docs.blender.org/api/current/)

Kaggle runtime capabilities and limits are service policies and can change. Verify current documentation and the actual notebook runtime before relying on specific accelerator types, quotas, persistence, or session duration. Record the verification date and observed facts in the environment manifest.

**Evidence labels:** APPROVED = project decision; PROVISIONAL = initial choice requiring validation; MEASURED = supported by a recorded test; UNKNOWN = not established. Do not relabel a capability-based expectation as a measured result.

## 11. Change log

### 1.0.1 — 2026-10-20
- Clarified that alternative-engine investigation requires a documented Blender mandatory-requirement failure and separate approval.
