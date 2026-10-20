# AI-Engine — Production Operations Specification
**Document ID:** AI-ENGINE-PRODUCTION-SOP  
**Version:** 1.0.0  
**Status:** Operational production standard; implementation and hardware benchmarks pending  
**Applies to:** Visual Physics Experiments — Satisfying Systems, Physics in Action, The Experiment  
**Parent specification:** [REVIEW_AND_UPDATED_PROJECT_FOUNDATION.md](./REVIEW_AND_UPDATED_PROJECT_FOUNDATION.md)  
**Last updated:** 2026-10-20

> **Purpose and limits.** This document removes avoidable ambiguity from the production workflow. It defines required inputs, outputs, acceptance tests, failure handling, records, and provisional delivery settings. It does not pretend to know the best engine, actual render speed, achievable quality on the available machine, audience performance, or monetization. Those items must be measured. Any value marked **PROVISIONAL** is a controlled starting point, not a proven optimum.

## 0. Governing rules

1. The approved editorial product is one channel with three pillars: Satisfying Systems, Physics in Action, and The Experiment.
2. No production code, asset purchase, model download, bulk generation, or publishing automation is authorized by this document alone.
3. Every episode must have an approved concept record before scene construction.
4. Every scene must declare its fidelity mode: **stylized procedural**, **plausible simulation**, or **evidence-oriented experiment**.
5. Never present a stylized or unvalidated simulation as measured real-world evidence.
6. A technically completed render is not a finished episode. Human review and all mandatory quality gates are required.
7. Store all decisions, settings, source assets, versions, failures, and outputs in durable project storage. Temporary compute sessions are not an archive.
8. Unknowns must be labeled **UNKNOWN** and assigned a test or decision owner. Never silently fill a gap with a guess.
9. If requirements conflict, follow this order: factual integrity and rights → physical/causal coherence → readability → originality → visual polish → speed.
10. The parent foundation document governs product strategy. This SOP governs production execution. If they conflict, record the conflict and update both documents rather than silently choosing one.

## 1. Status vocabulary and decision control

Use these exact labels in production records:

- **APPROVED:** Explicitly adopted project decision.
- **REQUIRED:** Mandatory for a deliverable to pass.
- **PROVISIONAL:** Initial setting to benchmark and revise.
- **HYPOTHESIS:** Expected benefit not yet established.
- **MEASURED:** Observed in a recorded test, with environment and method documented.
- **UNKNOWN:** Not yet established.
- **BLOCKED:** Work must not proceed until the named dependency is resolved.
- **WAIVED:** A specific requirement has been consciously waived by the project owner, with reason and risk recorded. Safety, rights, factual integrity, and critical defect checks cannot be waived.

Every major production decision must record: decision, status, rationale, evidence or test, date, owner, and review trigger.

## 2. End-to-end production lifecycle

No stage may be skipped without recording a justified exception. A stage is complete only when its required artifacts exist and its acceptance test passes.

| Stage | Name | Required output | Exit condition |
|---|---|---|---|
| P0 | Idea intake | Candidate record | Complete enough to evaluate |
| P1 | Editorial approval | Approved concept card and originality review | Premise and payoff are distinct and legible |
| P2 | Experiment design | Scene/experiment specification | Variables, initial conditions, and claim limits defined |
| P3 | Feasibility prototype | Blockout scene and preview | Core action is achievable and readable |
| P4 | Simulation validation | Validation notes and repeatability test | No critical causal or simulation defects |
| P5 | Art direction | Approved look frame / style sheet | Visual identity and framing approved |
| P6 | Production scene | Versioned scene source and parameters | Approved action reproduced at target timeline |
| P7 | Picture lock | Final shot/timing edit | Story/action is complete before final polish |
| P8 | Final render | Image sequence or high-quality intermediate | Render passes technical integrity checks |
| P9 | Sound and finishing | Mixed audio, captions, final edit | Sound, text, pacing, and claims reviewed |
| P10 | Quality assurance | Completed release checklist | All mandatory gates pass |
| P11 | Delivery and archive | Final export plus source package | Export verified and all source records archived |
| P12 | Publication and measurement | URL, date, metrics snapshots | Publication records and review dates saved |

### Stage transition rules

- A failed stage returns to the earliest stage capable of correcting the cause. Example: an unclear payoff returns to P1/P2, not merely to color grading.
- Do not polish an unproven blockout. Do not final-render a scene with unresolved simulation defects.
- If the concept changes after P1, increment the concept version and re-run originality and experiment-design review.
- If a physical parameter changes after validation, rerun the affected simulation and validation checks.
- If framing, timing, captions, or audio changes after final QA, rerun the affected checks; any change that can hide or alter the event requires full review.
- Keep rejected candidates and failure notes. They prevent repeated work and reveal recurring production problems.

## 3. P0 — Idea intake and P1 — Editorial approval

### 3.1 Required concept card

Every proposed Short must contain the following fields before scene construction:

| Field | Required content |
|---|---|
| Concept ID | Unique stable identifier, e.g. `VPE-SS-001`, `VPE-PA-001`, `VPE-EX-001` |
| Working title | Short internal name, not necessarily the final public title |
| Pillar | Exactly one primary pillar; a secondary pillar may be noted |
| One-sentence premise | What the viewer will see |
| Viewer question | The question or uncertainty that creates interest |
| First-second image | Specific visible state/action in the opening |
| Rule or constraint | What governs success, failure, or motion |
| Payoff | The exact visible outcome |
| Novelty delta | How the mechanism, rule, comparison, or payoff differs from prior work |
| Closest references | URLs or “not yet researched”; no invented references |
| Fidelity mode | Stylized procedural / plausible simulation / evidence-oriented experiment |
| Claim boundary | What can and cannot be concluded from this scene |
| Main risk | Most likely reason the idea may fail |
| Complexity class | C0–C3 using Section 5 |
| Asset needs | Geometry, textures, audio, fonts, models, and rights status |
| Acceptance test | Observable condition that proves the scene works |
| Decision | APPROVE / REVISE / REJECT / BLOCKED |
| Decision record | Date, reviewer, rationale |

### 3.2 Originality gate

Score the concept using the parent document’s 10-point originality scorecard. Minimum 8/10 is an internal project rule, not a market-performance predictor. Original premise and episode-specific value must each score above zero.

In addition, answer all of these:
- What is the closest known example?
- What changes structurally, not cosmetically?
- What unique result does this episode deliver?
- Would the episode still be meaningfully different if colors and camera angle were removed?
- Is the source of the idea and any reference material recorded?

If these cannot be answered, status is **BLOCKED** until research is completed. If the only novelty is a recolor, increased object count, or minor camera change, **REJECT** or redesign.

### 3.3 Pillar-specific approval tests

**Satisfying Systems**
- The system has a deliberate pattern, rhythm, transformation, completion, or loop.
- The viewer can see what “resolved” means.
- The motion is not just random objects moving.
- If a loop is used, both the loop transition and the meaningful visual idea pass review.

**Physics in Action**
- The physical interaction is the main event.
- The causal sequence and relevant contact points are visible.
- The fidelity mode is honest about approximations.
- Any material comparison identifies which properties were changed.

**The Experiment**
- A concise question or challenge exists before production.
- The independent variable and relevant controlled variables are recorded.
- The result can be compared to the setup.
- The conclusion does not exceed what the test actually demonstrates.

## 4. P2 — Scene and experiment specification

Before constructing a scene, create a scene spec. This is the production source of truth for the expected behavior.

### 4.1 Scene spec fields

- Concept ID and version.
- Scene ID and shot list.
- Timeline: frame rate, start/end frame, event frames, and intended duration.
- World units and scale convention.
- Objects: unique ID, geometry, dimensions, mass if relevant, collision shape, material, initial transform, and role.
- Simulation parameters: gravity vector, friction, restitution, damping, solver/substep settings, constraints, and any non-default values relevant to the result.
- Initial conditions: positions, rotations, velocities, trigger timing, and random seed where applicable.
- Declared independent variable and all controlled variables for comparisons.
- Camera: projection type, position, focal length or orthographic scale, framing, focus, and motion.
- Lighting and material intent.
- Fidelity mode and claim boundary.
- Expected outcome and acceptable variation.
- Failure conditions and planned debug steps.
- Preview render settings.
- Final render settings, once benchmarked.
- Audio and caption cues.
- Acceptance tests.
- Software versions, dependencies, and asset references.

Do not record irrelevant parameters merely to create paperwork. Record every parameter that can materially affect reproducibility, comparison validity, or interpretation.

### 4.2 Controlled comparison protocol

For an episode comparing conditions:
1. Define the question and the outcome metric before running the comparison.
2. Set a baseline configuration.
3. Change only the declared independent variable wherever practical.
4. Keep initial positions, camera, timing, object geometry, solver settings, and other relevant conditions identical.
5. If more than one variable must change, list them and narrow the conclusion accordingly.
6. Save every run’s parameter file and output.
7. Repeat the run when stochastic behavior or numerical instability could materially change the result.
8. If results vary, report the variation or redesign the test; do not cherry-pick the most dramatic run and imply it is universal.
9. Label deliberately exaggerated parameters as stylized entertainment.
10. For evidence-oriented experiments, document validation requirements and source the physical assumptions. A render by itself is not empirical proof.

## 5. Complexity classification and production risk

Classify every concept before choosing a tool. The classification is a planning aid, not a promise of runtime.

| Class | Scene characteristics | Production posture | Gate |
|---|---|---|---|
| C0 — Procedural/simple | Mathematical pattern, deterministic transform, simple single-object motion, minimal collision dependency | Preferred for first blockout and baseline tests | Must still pass visual and originality checks |
| C1 — Basic rigid body | Small number of rigid objects, simple collision chain, stable geometry | Candidate for first physics prototype | Validate contacts, scale, and repeatability |
| C2 — Dense/compound | Many interacting objects, complex constraints, dense stacks, breakage, branching chain reactions | Defer until C0/C1 pipeline is stable | Benchmark a reduced scene first |
| C3 — Expensive/fragile | Advanced fluids, complex soft bodies, coupled fluid/solid systems, high-detail destruction, heavy particle counts | Do not use for the first proof of workflow unless essential to the product promise | Requires isolated feasibility test and documented cost ceiling |

Do not classify solely by object count. Collision topology, stiffness, geometry quality, solver choice, output resolution, and desired fidelity can dominate cost.

### 5.1 Simplification ladder

When a scene fails or is too expensive, simplify in this order and record the change:
1. Replace final assets with primitives.
2. Remove secondary objects and effects.
3. Reduce collision complexity.
4. Shorten the simulated interval to the critical event.
5. Use a deterministic procedural path when the goal is visual design rather than physical inference.
6. Reduce preview samples/resolution and render only critical frames.
7. Change solver or engine only after preserving a minimal reproducible failure case.
8. Revisit the premise if the essential event cannot be produced reliably.

Do not hide an impossible or unstable setup with post-production edits if those edits would misrepresent the claimed result.

## 6. P3 — Feasibility prototype

Build the smallest scene that can test the central visual premise. Use simple geometry and one fixed camera. Do not add final materials, complex lighting, particles, or sound until the action is proven.

### Prototype checklist
- [ ] The action can be triggered consistently.
- [ ] The action fits the intended timeline.
- [ ] The camera shows the cause and effect.
- [ ] The result is visible at phone size.
- [ ] The scene can be reset and rerun.
- [ ] The critical event is reproducible or the variability is documented.
- [ ] The simulation can be exported and inspected frame by frame.
- [ ] The scene has a defined pass/fail test.
- [ ] Measured build time, run time, preview time, and failure count are logged.

### Prototype report template
- Concept/scene ID and revision:
- Hardware and operating environment:
- Software/engine/version:
- Scene complexity class:
- Test settings:
- Active build time:
- Simulation/run time:
- Preview render time:
- Peak memory/VRAM if measurable:
- Number and type of failures:
- Manual fixes required:
- Visual result:
- Pass/fail against acceptance test:
- Next action:
- Evidence location:

The prototype passes only if the central event is repeatable enough for its declared fidelity mode, visually readable, and achievable within a budget explicitly chosen by the project owner. No assumed time limit is silently imposed.

## 7. P4 — Simulation validation and reproducibility

### 7.1 Defect taxonomy

Record defects by type and severity:

- **S0 — Critical:** Changes the meaning or claimed result; e.g. object passes through a solid barrier, comparison conditions are inconsistent, a key event is hidden, or motion violates the stated rule.
- **S1 — Major:** Clearly visible and damaging to credibility or viewing; e.g. persistent jitter, obvious teleportation, unstable resting objects, broken constraints, severe clipping.
- **S2 — Minor:** Visible but does not alter interpretation; e.g. small noncritical shadow flicker or a brief secondary-object wobble.
- **S3 — Cosmetic:** Very subtle defect unlikely to be noticed at final viewing size.

Release policy: no unresolved S0 or S1 defects. S2 defects must be corrected when practical; any retained S2 requires reviewer approval and a written reason. S3 defects are tracked if they recur.

### 7.2 Required validation tests

- **Reset test:** Restart from the saved initial state and confirm the scene does not depend on hidden previous state.
- **Repeat-run test:** Run the same scene at least three times for the first prototype. Compare outcomes and record variation. If the engine is deterministic, confirm settings and environment; do not assume determinism without checking.
- **Collision test:** Inspect critical contacts, thin geometry, fast motion, and known tunneling risks.
- **Rest-state test:** Check for drift, jitter, energy appearing without a cause, or objects settling through surfaces.
- **Constraint test:** Check joints, hinges, fixed points, and stacked objects for unintended separation or instability.
- **Comparison test:** Confirm only intended parameters differ.
- **Camera test:** Confirm no key action is clipped or occluded.
- **Timeline test:** Confirm trigger, escalation, and payoff occur in the intended frame range.
- **Export test:** Confirm the rendered sequence matches the approved simulation and contains no missing or duplicated frames.

Three repeats are a minimum diagnostic check for the first prototype, not proof of scientific validity. Increase repeats when stochastic variation affects the claim.

### 7.3 Failure handling

When a test fails:
1. Save the failed scene and logs before editing.
2. Reduce to the smallest scene that still reproduces the failure.
3. Change one diagnostic parameter at a time.
4. Record each change and its effect.
5. Do not modify comparison conditions invisibly.
6. If the failure cannot be resolved, simplify the scene, change the declared fidelity mode, or reject the concept.
7. Re-run all affected tests after any relevant change.

## 8. P5–P7 — Art direction, production, and picture lock

### 8.1 Visual system

Maintain a versioned visual style sheet with:
- Background and palette rules.
- Material families and roughness/reflectivity intent.
- Lighting setup and shadow behavior.
- Camera/projection defaults and approved exceptions.
- Object scale and proportion rules.
- Typography, label placement, and safe area.
- Motion language and transition rules.
- Sound signature.
- Examples of accepted and rejected frames.

Do not lock a palette, material, or render technique based on generic advice alone. Approve it by comparing test frames at actual mobile size and checking whether it supports the action.

### 8.2 Composition rules

- Establish spatial relationships before cutting to close-ups.
- Keep the primary action in a mobile-safe region and inspect the final 9:16 export.
- Avoid depth of field, motion blur, particles, reflections, or camera movement that conceal causal events.
- Keep comparison cameras and scales matched unless the difference is explicitly part of the test.
- Use cuts only when they improve comprehension; do not cut away from the decisive event.
- Verify the first frame, first meaningful action, decisive event, and final payoff separately.
- A beautiful still frame is not sufficient if the motion is unclear.

### 8.3 Picture lock

Before final rendering, approve a low-resolution timing edit that includes:
- Opening frame and first action.
- All required causal steps.
- Timing of labels and audio cues.
- Result/payoff.
- End frame and optional loop.
- Final duration.

After picture lock, changes to event order, simulation, or timing require revalidation. Color/material polish should not be used to conceal a weak premise.

## 9. P8 — Rendering and delivery settings

The first render benchmark must establish what the actual machine can sustain. Until then, use the following only as **PROVISIONAL DELIVERY BASELINE**.

### 9.1 Provisional export baseline for a standard vertical Short

| Setting | Provisional baseline | Rule |
|---|---|---|
| Frame shape | 9:16 vertical | Required for this project’s initial format |
| Resolution | 1080 × 1920 | Baseline; confirm the renderer and machine can produce it reliably |
| Frame rate | 30 fps | Use only if motion and simulation are designed for it; native project rate may differ |
| Container | MP4 | Preferred delivery container |
| Video codec | H.264/AVC | Baseline compatibility choice |
| Color | SDR, Rec.709 where supported | Do not mix color spaces silently |
| Audio codec | AAC, 48 kHz stereo where audio is present | Verify final encode and sync |
| Bitrate | Encoder-controlled high-quality setting; record actual output | Do not invent a universal bitrate; validate visible artifacts and file size |
| Duration | Concept-driven; initial 20–45 second target is a hypothesis | Never pad solely to hit a duration |
| File naming | `<concept_id>_v<major.minor>_<stage>_<date>.<ext>` | Apply consistently |

Before publishing, check current YouTube upload recommendations and platform constraints. This table is a project delivery baseline, not a claim that YouTube requires these exact settings.

### 9.2 Render tiers

Use named render tiers so tests are comparable:

- **BLOCKOUT:** Primitive geometry, minimal lighting, low resolution, only critical frames or short segment.
- **PREVIEW:** Target aspect ratio, simplified materials, reduced render samples/quality, sufficient to judge motion and framing.
- **APPROVAL:** Near-final resolution and materials, representative full timeline, used for human review.
- **FINAL:** Approved resolution, frame rate, materials, samples, effects, and audio integration.

Store the exact settings for each tier. “Preview” or “final” is not a reproducible setting by itself.

### 9.3 Render integrity checks

- Verify expected frame count against timeline and frame rate.
- Check for missing, duplicated, corrupt, or out-of-order frames.
- Inspect fast motion, transparent materials, shadows, contact frames, and loop boundaries.
- Compare the final render with the approved picture lock.
- Confirm color management is consistent between viewport, image sequence, and encoded video.
- Confirm audio is synchronized and the output plays correctly in at least one independent player.
- If a render fails, preserve logs and resume from a documented checkpoint where supported; do not overwrite the last known-good output.

## 10. P9 — Audio, captions, and final edit

### 10.1 Sound design rules

- Choose sounds for the apparent material and event, not simply for loudness.
- Use original recordings or assets with documented commercial-use rights.
- Never label a designed sound as a real recording of the simulated event unless that is true.
- Align transient sounds to visible contact; check synchronization at normal speed and frame-by-frame for key impacts.
- Avoid clipping, harsh peaks, unintended clicks, abrupt noise-floor changes, and accidental silence.
- Sound must enhance rather than carry the only explanation of the scene.

### 10.2 Provisional audio target

There is no universal loudness value that guarantees the best Shorts experience. For consistent internal review, use a provisional mix target of approximately **-16 to -14 LUFS integrated** and **true peak at or below -1 dBTP**, then adjust when the actual content, platform behavior, and monitoring chain justify it. Record measured loudness for every final export. This is an internal starting point, not a YouTube requirement or a claim about performance.

If a mix has intentional silence, short impacts, or highly dynamic sound, prioritize clean playback and intelligibility over blindly forcing the integrated loudness number.

### 10.3 Captions and text

- English is the default language for on-screen labels and metadata.
- Use text only to clarify a question, condition, unit, or result.
- Keep labels short, readable on a phone, correctly spelled, and away from interface overlays.
- Do not use a caption to claim more than the simulation supports.
- If units are shown, specify them and keep them consistent.
- Review every caption in the exported video, not only in the editing project.

### 10.4 Edit checklist

- Remove dead time only when doing so preserves causal understanding.
- Do not speed up or slow down a physical event in a way that contradicts labels or comparisons.
- If time manipulation is used for artistic effect, disclose it where it could affect interpretation.
- Ensure transitions do not hide defects or change the apparent result.
- The first second must contain a meaningful visual state or action; no logo intro.
- The final payoff must be visible before the clip ends.
- A loop is optional; never force it at the cost of resolution.

## 11. P10 — Mandatory release QA

Every item below must be marked PASS, FAIL, or NOT APPLICABLE with reviewer initials/date. Blank items are not passes.

### Editorial and originality
- [ ] One primary pillar is identified.
- [ ] Premise, question/rule, and payoff are recorded.
- [ ] Originality score is at least 8/10; no zero on original premise or episode-specific value.
- [ ] Closest known references have been checked and logged.
- [ ] The episode is not a superficial variant or close reproduction.
- [ ] The first meaningful visual action is prompt and readable.
- [ ] The payoff is complete and understandable.

### Physics and factual integrity
- [ ] Fidelity mode is declared.
- [ ] Critical motion and contact events pass validation.
- [ ] No unresolved S0 or S1 defects.
- [ ] Comparisons use controlled conditions or clearly qualify limitations.
- [ ] Claims and units are checked.
- [ ] Stylized simulation is not represented as measured evidence.
- [ ] Any factual claims have sources recorded.

### Visual and technical
- [ ] Vertical framing and mobile readability pass.
- [ ] No unintended intersections, teleportation, flicker, jitter, clipping, or missing frames.
- [ ] Lighting, materials, shadows, and motion effects preserve readability.
- [ ] Captions and labels are accurate and legible.
- [ ] Export dimensions, frame rate, audio sync, and playback pass.
- [ ] Final file has been watched in full.

### Audio and rights
- [ ] No clipping, unwanted noise, sync errors, or accidental silence.
- [ ] All sound, music, fonts, textures, models, and other third-party assets have documented rights.
- [ ] Licenses cover the actual intended commercial use and required distribution.
- [ ] Asset manifest includes source, license, acquisition date, and restrictions.
- [ ] No external asset has an unknown rights status.

### Archive and release
- [ ] Concept card, scene spec, parameters, source project, and dependencies are archived.
- [ ] Render settings, final export, and QA record are archived.
- [ ] Filename and version are correct.
- [ ] Human reviewer approves release.
- [ ] Audience designation and disclosure decisions are accurate for the actual content.
- [ ] Publication metadata is reviewed separately from production QA.

Any FAIL blocks release. A NOT APPLICABLE entry requires a short explanation. Critical rights, factual integrity, and S0/S1 defects cannot be waived.

## 12. Asset, license, and dependency register

Maintain a machine-readable or tabular register with these fields:

- Asset ID and filename.
- Asset type (geometry, texture, font, sound, model, code, plugin, footage).
- Original creator/source URL.
- Date acquired/downloaded.
- Exact license name and version.
- Commercial use permitted? (YES/NO/UNCLEAR).
- Attribution required? (YES/NO and exact wording).
- Modification/redistribution restrictions.
- Evidence file or license snapshot location.
- Episode IDs using the asset.
- Reviewer and status.

Rules:
- **UNCLEAR** means do not publish using the asset until resolved or replaced.
- A tool’s availability does not imply that every output or included asset is commercially unrestricted.
- Record model version, repository/source, checksum where practical, license, hardware requirements, and usage limitations before downloading or running large models.
- Pin software/dependency versions after a working prototype; document upgrades and revalidate affected scenes.
- Do not place credentials, private tokens, or account secrets in the repository.

## 13. File organization and naming convention

Use this proposed layout for durable project storage. It may be adapted to the chosen toolchain, but the purpose of each category must remain clear.

```text
AI-Engine/
  README.md
  REVIEW_AND_UPDATED_PROJECT_FOUNDATION.md
  PRODUCTION_OPERATIONS_SPECIFICATION.md
  production/
    concepts/
      VPE-SS-001/
        concept.md
        scene_spec.yaml
        parameters/
        source/
        assets_manifest.csv
        previews/
        renders/
        audio/
        exports/
        qa/
        logs/
    style_guide/
    templates/
    benchmarks/
    decisions/
    research/
```

This is a logical organization proposal, not a requirement to store large binary renders in Git. Use appropriate durable storage for large outputs and keep links, checksums, and metadata in the repository when binary assets would make version control unwieldy.

### Naming

- Concept IDs: `VPE-SS-###` for Satisfying Systems, `VPE-PA-###` for Physics in Action, `VPE-EX-###` for The Experiment.
- Versions: semantic revisions such as `v0.1`, `v0.2`, `v1.0`; do not overwrite a released version.
- File names: lowercase ASCII, hyphens or underscores, no ambiguous “final-final2” suffixes.
- Exports: `<concept_id>_<version>_1080x1920_30fps_<date>.mp4` only if those exact properties are true.
- Every final export must link to its source concept, scene, settings, and QA record.

## 14. Production log and metrics

For each scene, record active human work separately from machine processing:

- Concept development time.
- Scene construction time.
- Debugging and correction time.
- Simulation time.
- Preview render time.
- Final render time.
- Audio/editing time.
- QA time.
- Number of failed simulations and renders.
- Number of manual interventions.
- Compute used and direct cost where measurable.
- Reusable asset/component percentage, with explanation.
- Final duration, file size, frame rate, and resolution.
- QA result and unresolved noncritical defects.

Do not merge active labor and unattended render time into one figure. Both matter but answer different production questions.

For published videos, add publication URL/date, observation date, views, and any analytics legitimately available from YouTube Studio. Public views cannot establish retention, RPM, revenue, or causal reasons for performance. Capture metrics at consistent intervals selected before the test; record the actual observation times rather than backfilling guessed values.

## 15. Engine and tool selection gate

No engine, renderer, AI model, editing tool, or sound source is approved until it passes a small benchmark.

### 15.1 Benchmark scene

Use the same benchmark across candidates:
- One rigid object rolls or falls onto a surface.
- One controlled collision/rebound.
- One small chain reaction or stacked-object interaction.
- One vertical camera setup.
- One representative material/light setup.
- One short preview and one target-quality render.
- One export and playback check.

If a candidate tool cannot support one of these tests, document why and use the closest comparable test; do not fabricate a score.

### 15.2 Scorecard

Score each category 1–5 and attach evidence; a score without a test note is invalid.

- Physical credibility for the intended scene.
- Stability and repeatability.
- Scriptability/procedural control.
- Visual quality at phone size.
- Preview and final render performance on actual hardware.
- Memory/VRAM use and failure behavior.
- Vertical export and post-production compatibility.
- Debugging, logs, and recovery.
- Learning and maintenance burden.
- License and commercial-use compatibility.
- Dependency stability and documentation.
- Cost and operational constraints.

Record hardware model, OS, driver/runtime versions, engine version, settings, output, time, memory, failures, and subjective visual assessment. Select only after comparing the measured results and the project’s stated priorities. If no candidate passes, simplify the product’s visual requirements or revise the workflow before proceeding.

## 16. Compute, checkpoints, and recovery

- Do not assume GPU availability or that a T4, cloud notebook, or other accelerator will always be available.
- Verify actual device visibility, memory, driver/runtime compatibility, and software support at the start of each benchmark session.
- Save the source scene and parameters before a long simulation or render.
- Save logs and the last known-good preview before trying a risky change.
- Where possible, render to numbered frames so interrupted jobs can resume.
- Check output completeness before encoding; never encode a partial sequence as if complete.
- Copy important source, parameters, logs, and deliverables to durable storage at each stage boundary.
- Test restoration from the archive before relying on it.
- Record environment and dependency versions in a lockfile or environment manifest when the selected tool supports it.
- Never treat a temporary session disk as the only copy of a project.
- Do not run downloaded code or model weights until source, license, provenance, and security risks are reviewed.

## 17. Pilot and scale-up policy

### First production proof
1. Approve one concept per pillar.
2. Create a blockout for each, but choose one representative scene for the first full technical benchmark.
3. Complete a measured benchmark and document the full time/cost/defect profile.
4. Produce three pilot Shorts at comparable quality only after the pipeline is feasible.
5. Have a reviewer assess all three with the same QA rubric.
6. If publishing is approved, establish measurement windows and capture analytics.
7. Decide whether to iterate, simplify, or stop based on evidence—not one view count or an assumed viral threshold.

### Scale-up is blocked until
- A repeatable workflow has been demonstrated.
- The critical visual and simulation defects are controlled.
- Asset rights and archive procedures work.
- Actual production time and cost are known.
- Distinct concepts can be produced without superficial repetition.
- The project owner explicitly approves a scale-up budget and target cadence.

Do not promise a daily or weekly publishing schedule before measuring production capacity.

## 18. Long-form production gate

Long-form work starts only after the Shorts test identifies a repeatable theme and there is enough material to justify a longer video.

Required long-form planning package:
- Central question or thesis.
- Sequence of distinct experiments and why each is necessary.
- Variables and result criteria.
- Escalation/progression.
- Source requirements for factual claims.
- Planned reuse of Shorts scenes and the additional value each reuse serves.
- Runtime estimate based on the actual outline, not padding.
- Production budget and QA plan.

Reject a long-form plan that is only a compilation, repeats the same result, or lacks a conclusion supported by the demonstrations.

## 19. Mandatory templates

### 19.1 Decision record

- ID:
- Date:
- Decision:
- Status:
- Options considered:
- Evidence/test:
- Rationale:
- Risks and trade-offs:
- Owner:
- Review trigger:
- Related files:

### 19.2 Shot record

- Shot ID:
- Purpose in the episode:
- Start/end frame:
- Camera and framing:
- Main event:
- Required objects:
- Relevant parameters:
- Audio/text cues:
- Expected state at end:
- Acceptance test:
- Known risks:
- Preview status:
- Final status:

### 19.3 Defect record

- Defect ID:
- Concept/scene/version:
- Severity S0–S3:
- First observed at stage:
- Reproduction steps:
- Expected behavior:
- Actual behavior:
- Evidence/log/frame:
- Suspected cause (label as hypothesis unless verified):
- Change made:
- Retest result:
- Closure reviewer/date:

### 19.4 Release record

- Concept ID/version:
- Final export filename and checksum:
- Runtime, resolution, frame rate, file size:
- Fidelity mode:
- Originality score:
- QA checklist location:
- Asset/license register location:
- Human reviewer/date:
- Release decision:
- Publication URL/date, when published:
- Analytics observation records:

## 20. Completion definition and unresolved items

### Production documentation is complete when
- Every stage has inputs, outputs, and exit criteria.
- Each pillar has explicit concept approval requirements.
- Scene/experiment parameters and fidelity claims are recorded.
- Simulation defects have severity levels and retest rules.
- Visual, audio, export, rights, and archive gates are defined.
- Tool selection requires a measured benchmark.
- Templates exist for concepts, scenes, defects, decisions, and releases.
- Unknowns are explicitly assigned a test rather than silently guessed.

### Production feasibility is NOT proven until
- A real benchmark has been run on the available hardware.
- A candidate engine and export path have been selected using measured results.
- At least one scene has passed the complete workflow.
- Actual active labor, render time, failures, and cost have been logged.
- Three comparable pilot Shorts have passed QA.
- Any publication and audience conclusions are supported by actual data.

### Explicitly unresolved
- Engine and renderer.
- Actual hardware/accelerator availability and compatible versions.
- Final frame rate and render quality settings.
- Real per-video production time and cost.
- Final visual identity, palette, and material library.
- Whether voiceover is useful.
- Which pillar or hook patterns produce repeatable audience response.
- Publishing cadence, channel branding, and monetization outcomes.

These items are not omissions in the procedure; they are empirical or owner decisions that cannot honestly be settled by prose alone. Each must be resolved through the specified benchmark, review, or explicit owner decision.

## 21. Change log

### 1.0.0 — 2026-10-20
- Established a stage-gated production lifecycle for all three pillars.
- Added concept and scene specification requirements, complexity classes, prototype tests, simulation validation, defect severity, render baseline, audio standards, QA, rights tracking, archive conventions, benchmark scorecard, recovery rules, and release templates.
- Marked untested export/audio settings as provisional and kept engine choice, runtime, cost, and market performance open until measured.
- No production software was installed, no engine was selected, no scene was built, and no video was rendered by creating this document.
