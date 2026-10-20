# AI-Engine: Critical Research Review & Updated Project Foundation

**Document ID:** AI-ENGINE-FOUNDATION  
**Version:** 0.2.0-proposal  
**Status:** PROPOSED — NOT APPROVED FOR IMPLEMENTATION  
**Review date:** 2026-10-20  
**Supersedes:** None. This is an additive review document; the original `README.md` remains unchanged.  
**Repository:** https://github.com/abumanar20264/AI-Engine  
**Scope:** English-language, global-audience video formats and a limited-compute, AI-assisted production workflow.

> **Decision boundary:** This document authorizes research and small, reversible experiments only. It does not authorize building a production system, committing to a niche, purchasing services, or claiming that any model has been tested.

## 1. Executive review

The original `README.md` contains a useful problem statement, 15 candidate niches, three shortlisted formats, a proposed production architecture, and several rounds of self-critique. It also contains material weaknesses: unsupported audience metrics, invented-looking comment quotations without traceable URLs, estimates presented as facts, contradictory claims, and proposed pass/fail thresholds that have no baseline.

The strongest conclusion is **not yet that one niche has been proven best**. It is that the project should validate a repeatable *editorial format* before engineering a production pipeline.

### Current recommendation

1. **Do not build the full production system yet.**
2. Use **system/outage explainers** and **supply-chain / infrastructure explainers** as the first two research-and-production candidates. Keep **prehistoric science explainers** as a reserve candidate until visual and scientific verification costs are measured.
3. Test each candidate with a small, comparable pilot using the same quality standard and disclosed production effort.
4. Prefer accurate vector diagrams, maps from authoritative geospatial data, charts, documents, and restrained motion. Treat image generation as optional art direction—not as a source of factual geometry or scientific anatomy.
5. Do not treat YouTube monetization, revenue per thousand views, search demand, or recommendation performance as predictable from niche labels alone.

This recommendation is **a working hypothesis**, not an approved final niche choice.

## 2. Evidence and status vocabulary

Use these labels throughout project documentation:

- **VERIFIED EXTERNAL FACT:** Supported by a cited primary or authoritative source.
- **OBSERVED PROJECT DATA:** Captured directly during a documented test or a reproducible audit, with date and method.
- **REPORTED EXAMPLE — UNVERIFIED:** A statement in the original research notes that has not been independently checked.
- **INFERENCE:** A reasoned interpretation of verified facts or observed data.
- **ESTIMATE:** A planning approximation; include assumptions and uncertainty.
- **HYPOTHESIS:** A proposition to test.
- **OPEN QUESTION:** A material unknown.
- **PROPOSED DECISION:** Awaiting explicit human approval.
- **APPROVED DECISION:** May be used only after explicit approval is recorded in a dated decision log.

No actual production benchmark, audience-retention result, monetization review, or model stability test has been supplied in the project material reviewed here. These must remain **NOT TESTED** until measured.

## 3. Critical review of the existing README

### 3.1 What is useful and should be retained

- The audience is global and primarily English-speaking.
- Multi-character cinematic continuity is deliberately out of scope.
- The local computer should retain authoritative copies of scripts, source records, project state, and final outputs.
- Kaggle should be treated as a temporary execution environment, not as durable storage or a continuously available server.
- Research, narration, visual assets, editing, and publication should remain distinct stages with review gates.
- Originality, rights clearance, factual accuracy, and platform policy must be considered from the beginning.
- The original shortlist is a useful set of hypotheses, not evidence that those options are validated.

### 3.2 Claims that must not be treated as established

The existing README includes approximate channel sizes, view counts, upload cadence, repeat-performance claims, viewer-comment quotations, estimated research hours, CPM/RPM ranges, search-versus-recommendation percentages, GPU memory peaks, and failure rates. Many entries lack direct video URLs, observation dates, collection methods, or reproducible measurements.

Examples requiring correction:

- Statements such as “consistent 500k–3M views per upload,” “2x–5x subscriber count,” or “50+ uploads consistently achieving 200k–1M views” are **not validated by a cited, reproducible sample** in the reviewed document.
- Quoted comments are not accompanied by direct comment URLs or a documented sample. They cannot be presented as observed audience research.
- Claims such as “70% Search / 30% Recommendations,” specific niche CPM/RPM ranges, and fixed hours-per-video estimates should be removed unless supported by actual channel analytics or a credible, transparent study. Publicly visible views do not reveal traffic source, retention, CTR, RPM, or creator workload.
- Statements that maps or diagram channels are inherently at high risk of demonetization are too broad. Platform policy concerns originality and viewer value, not simply the use of diagrams, AI, maps, or templates.
- Claims that FLUX.1-schnell FP8 will use a specific amount of VRAM or crash at a particular rate on a Kaggle T4 are unverified until tested with a specified software stack and model files.
- “Manim runs on CPU” is directionally correct for its Cairo renderer, but does not prove that every scene, render quality, frame rate, or target duration will meet project needs on the user’s machine.
- A fixed stop rule such as CTR below 2.5% or RPM below $2.50 is not a universal scientific threshold. It should not be used without sufficient impressions, a defined test window, and context for format, topic, audience, and channel maturity.
- “Submit a test channel for monetization review” is not a clean early experiment: eligibility thresholds and review timing can prevent this from testing the actual editorial hypothesis.

### 3.3 Correct interpretation of the YouTube policy risk

**VERIFIED EXTERNAL FACT:** YouTube’s monetization policy describes “inauthentic content” as repetitive or mass-produced content and says monetized content should be original and authentic. The policy distinguishes this from “reused content.” YouTube also states that using automation or templates does not by itself determine the outcome; the final work must still offer creative, educational, or entertainment value. See the official policy: https://support.google.com/youtube/answer/1311392 (accessed 2026-10-20).

**Implication:** Do not design for “avoiding AI detection.” Design for substantive originality: original research, a distinct thesis, carefully verified narration, custom visual explanation, meaningful variation between episodes, documented rights, and human editorial review. No format can be guaranteed monetizable in advance.

## 4. Project purpose, objectives, and non-objectives

### 4.1 Purpose

Determine whether a sustainable, original video format can be produced to a competitive quality standard with a small team-of-one workflow and limited compute, before investing in production automation.

### 4.2 Objectives

1. Identify a specific, repeatable channel format for a global, English-speaking audience.
2. Validate recurring viewer interest using traceable public examples across multiple channels and multiple uploads.
3. Estimate the actual research, verification, narration, asset creation, editing, and quality-control workload.
4. Validate a minimum viable production workflow on the actual local machine and, only where needed, the available Kaggle GPU.
5. Publish a small pilot only after rights, factual accuracy, audio, visual quality, and originality checks pass.
6. Preserve all source citations, licenses, prompts, source assets, scripts, project files, and output manifests.
7. Make the final niche decision based on evidence, not assumed CPM, channel popularity, or model novelty.

### 4.3 Non-objectives

- Multi-character narrative films requiring persistent character identity and complex interaction.
- A fully autonomous, unattended, mass-publishing content factory.
- Assuming AI-generated content is automatically competitive, original, or profitable.
- Recreating a competitor’s distinctive script, storyboard, visual identity, or copyrighted footage.
- Running always-on infrastructure on ephemeral Kaggle sessions.
- Promising monetization, audience growth, or revenue.
- Building a generalized video engine before one format has passed a pilot.

## 5. Audience and candidate formats

**Target audience:** Global, primarily English-speaking viewers. Age, profession, geography, and viewing intent remain hypotheses to refine from evidence; they should not be stated as measured demographics.

### Candidate A — System failures and infrastructure explainers

**Format hypothesis:** Explain one real incident or engineering concept through a clear causal sequence, original diagrams, timelines, and primary-source references.

- **Strengths (inference):** Diagrams can be deterministic and reusable; no image diffusion is essential; the format can support evergreen concept videos and incident retrospectives.
- **Main risk:** Research requires technical competence. Incorrect causal claims can destroy trust. Prominent competitors may benefit from existing authority and distribution.
- **Minimum visual stack:** Custom vector diagrams, timelines, selected code/configuration callouts, labels, and restrained camera movement.
- **GPU dependency:** None required for the core format; actual local rendering speed is unknown.
- **Open question:** Can the project produce technically correct scripts and compelling narrative without excessive expert-review time?

### Candidate B — Supply-chain, transport, and infrastructure explainers

**Format hypothesis:** Explain how a specific physical or commercial system works—such as a shipping route, port, canal, commodity chain, or infrastructure bottleneck—using sourced maps, flow diagrams, real figures, and causal storytelling.

- **Strengths (inference):** A concrete question and physical process can create an accessible narrative; maps and flow diagrams are more controllable than generated geography; topics can combine evergreen systems with timely events.
- **Main risk:** Geographic data, trade figures, and claims about current events need careful sourcing. Generic map pans can become interchangeable.
- **Minimum visual stack:** Authoritative base maps, manually checked route layers, original vector overlays, sourced charts, and explanatory diagrams. Generated textures are optional and must not alter factual geography.
- **GPU dependency:** None for the core format; optional image generation must earn its place through measurable quality improvement.
- **Open question:** Does the format attract sustained interest beyond news spikes, and can research remain manageable?

### Candidate C — Prehistoric science and evolutionary systems

**Format hypothesis:** Explain a specific evolutionary adaptation, ecosystem, extinction mechanism, or fossil inference through sourced scientific illustrations, diagrams, timelines, and carefully qualified reconstructions.

- **Strengths (inference):** Visually rich and naturally suited to explanatory illustration; many topics are not dependent on current events.
- **Main risk:** Generated anatomy can be wrong; speculative reconstructions can mislead; scientific verification and image correction may erase any automation benefit.
- **Minimum visual stack:** Evidence-based diagrams, licensed/public-domain fossil imagery where applicable, timelines, maps, and clearly labeled reconstructions.
- **GPU dependency:** Optional, not foundational. Do not assume FLUX or SDXL is required.
- **Open question:** Can visual quality and scientific trust be achieved with a reasonable manual correction burden?

### Current candidate status

| Candidate | Status | What is established now |
|---|---|---|
| System failures / infrastructure | Candidate for pilot | Core diagrams can be designed without generative video; demand and workload remain unvalidated. |
| Supply chain / infrastructure | Candidate for pilot | A map-and-diagram workflow is technically plausible; repeat demand and differentiation remain unvalidated. |
| Prehistoric science | Reserve candidate | Still-image explanation is plausible; anatomy accuracy, workload, and audience performance remain unvalidated. |

No candidate has been selected as the final channel niche.

## 6. Demand research: required evidence standard

The earlier README does not provide sufficient traceable evidence to call the shortlist “validated.” The next research pass must create an auditable evidence ledger.

### 6.1 Required sampling method

For each candidate:

1. Select at least **8 relevant videos across at least 4 channels**, including smaller or less-established channels where discoverable.
2. Record exact video title, URL, channel URL, publication date, view count, observation date, duration, and subscriber count if visible.
3. Record views-per-day only as a derived descriptive measure with the calculation date; do not treat it as a reliable estimate of future performance.
4. Classify each video as evergreen, news-driven, mixed, or unclear.
5. Compare several uploads from the same channel and several channels covering related topics. Do not infer repeatability from one viral video.
6. Sample comments transparently: state which videos were sampled, how many comments were reviewed, the sampling rule, and whether the comments were top comments or recent comments. Do not invent representative quotes.
7. Capture search suggestions or public trend data only when the source and collection date are recorded. Do not invent search volumes.
8. Document counterevidence: low-performing comparable videos, topics that appear to depend on breaking news, and cases where a large creator’s brand likely explains part of the result.
9. Keep observed public metrics separate from private metrics that are unavailable, such as CTR, audience retention, traffic sources, RPM, and production hours.
10. Include the exact source URLs and a short note explaining what each source can and cannot establish.

### 6.2 Evidence categories that must not be conflated

- **High absolute views:** a video has accumulated many views. This does not prove repeatability.
- **Repeated performance:** multiple videos or channels show comparable performance. This is stronger, but may still reflect creator size or distribution.
- **Sustained interest:** older videos continue to receive attention or the topic remains relevant across time. Public snapshots are only a proxy unless time-series data is captured.
- **Unmet demand:** requires direct evidence, such as repeated audience requests plus a credible gap in available answers. Few search results alone are insufficient.
- **Future growth:** remains speculative unless supported by additional evidence.

### 6.3 Evidence ledger template

Use one row per video or source:

| Field | Required value |
|---|---|
| Candidate | A / B / C |
| Video title and direct URL | Exact URL |
| Channel URL | Exact URL |
| Published date | Date shown by platform |
| Observation date | YYYY-MM-DD |
| Views / duration / visible subscribers | Captured values, or “not visible” |
| Topic class | Evergreen / news-driven / mixed / unclear |
| Visual approach | Diagrams / maps / live action / generated images / other |
| Comment sample | Method and count, or “not sampled” |
| What this supports | Narrow claim only |
| Alternative explanation | Creator size, timeliness, external promotion, etc. |
| Confidence | High / medium / low, with reason |

**Research gate:** Until this ledger is populated with direct, checked examples, the project must describe audience demand as **unvalidated**. This document deliberately does not repeat unsupported view counts from the original README as facts.

## 7. Technical feasibility and compute architecture

### 7.1 Proposed principle

**CPU-first, GPU-optional, local-storage-first.** Build the simplest version of a candidate using deterministic vector assets before adding diffusion, depth estimation, or video-generation models.

### 7.2 Stage allocation

| Stage | Proposed execution | Status |
|---|---|---|
| Research and source ledger | Local workflow + research tools | Workflow not benchmarked |
| Script drafting and editorial verification | Human-directed; AI assistance permitted | Required human gate |
| Diagrams and charts | Vector / Python tools, local CPU initially | Must be benchmarked on actual machine |
| Maps | Trusted geospatial data and vector rendering | Data source and workflow to be selected |
| Optional image generation | Kaggle T4 only after model identity, license, dependencies, and test are verified | Not tested |
| Narration | Compare available voice tools against a quality rubric | Models and voices not verified |
| Video composition and encoding | Local editor / FFmpeg / selected renderer | Must be benchmarked |
| Storage and recovery | Local persistent storage as source of truth; versioned manifests and checksums | Design proposed, not implemented |
| Publication | Human review and manual upload initially | No auto-publishing authorization |

### 7.3 External technical references

- **Manim Community:** official documentation identifies Cairo and OpenGL renderers; renderer behavior and configuration are documented at https://docs.manim.community/en/stable/reference/manim.constants.RendererType.html and https://docs.manim.community/en/stable/guides/configuration.html (accessed 2026-10-20). This establishes available rendering modes, not the speed of this project’s local machine.
- **FLUX.1-schnell:** its model card identifies a 12-billion-parameter text-to-image model, 1–4-step generation, and an Apache-2.0 license; it does not prove reliable execution on a specific T4/Kaggle software stack. https://huggingface.co/black-forest-labs/FLUX.1-schnell (accessed 2026-10-20).
- **SDXL base 1.0:** the model card lists the OpenRAIL++ license family and describes the base/refiner pipeline. The exact license and use conditions must be reviewed before commercial use. https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 (accessed 2026-10-20).
- **YouTube monetization policy:** see https://support.google.com/youtube/answer/1311392 (accessed 2026-10-20).

These references are **documentation evidence only**. They do not establish that a model is installed in the project’s Kaggle account, that the current weights are accessible, that dependencies resolve, or that inference succeeds.

### 7.4 Kaggle and artifact boundaries

Do not hard-code assumptions about session length, GPU availability, quotas, or storage persistence. Record the actual runtime and accelerator shown for each run, and check current Kaggle documentation and account terms before relying on a limit.

Every execution unit should be restartable and produce:
- input manifest and immutable source IDs;
- code/configuration version;
- model name, exact revision, and license record where applicable;
- runtime, device, software versions, and peak memory if measured;
- output filenames and SHA-256 hashes;
- success/failure status and error logs;
- a durable local copy before the job is considered complete.

Never make Kaggle the sole copy of any valuable artifact. Do not describe synchronization as implemented until a real interruption/recovery test passes.

## 8. Minimum experiments before system construction

Experiments should answer a specific question at the lowest practical cost. Thresholds below are **proposed operational gates**, not universal industry benchmarks.

### Experiment 1 — Local deterministic visual benchmark

**Question:** Can the local machine render an original, readable, animated 2D explanation at acceptable quality and time?

- Render one 30–60 second 1080p sequence with 15–30 nodes, labels, arrows, highlights, and at least two transitions.
- Record hardware, software versions, wall-clock time, output size, frame rate, text legibility, clipping, and defects.
- Run twice from a clean state.
- **Pass:** Both runs complete; no missing assets or unreadable text; output is technically playable; measured time fits the proposed weekly workflow.
- **Fail:** Reproducible crashes, illegible labels, or runtime makes the format impractical.
- **Not measured yet:** All results.

### Experiment 2 — Research and fact-check workload

**Question:** Can the creator make a reliable script without specialist research becoming an unsustainable bottleneck?

- Produce one 700–1,000-word script for candidate A and one for candidate B, each with a claim-by-claim source ledger.
- Track active minutes separately for discovery, reading, drafting, verification, revisions, and visual planning.
- Mark every factual statement as sourced, inference, or uncertain.
- **Pass:** All material factual claims are traceable; no unresolved high-impact claim remains; the measured workload is acceptable to the project owner.
- **Fail:** Core causal claims cannot be verified or workload is unsustainable.
- Do not use an invented universal hour threshold. Set the acceptable time budget after the first two measured trials.

### Experiment 3 — Optional T4 model smoke test

**Question:** Is the specific image model already available and stable enough to contribute meaningful value?

- First inventory the actual model files, revisions, license, dependencies, and access requirements.
- Run a single low-risk test image, then a small batch of 10 images only if the first test passes.
- Record exact GPU model, free and peak VRAM if measurable, cold-start time, per-image time, errors, and output defects.
- **Pass:** No crash, outputs are saved and verified, and the images improve the pilot compared with deterministic alternatives.
- **Fail:** Access/dependency failure, unstable memory behavior, unacceptable quality, or no material improvement.
- Do not run a 100-image stress test until the small batch justifies it.

### Experiment 4 — Comparable visual prototype

**Question:** Can each candidate communicate its main idea with stills and simple motion?

- Create a 45–90 second unlisted prototype for A and B, using the same resolution, narration standard, sound level, and review rubric.
- Include original diagrams and evidence citations in the project file.
- Review for comprehension, factual accuracy, pacing, legibility, audio quality, and production effort.
- If time permits, prototype C using sourced illustrations and diagrams without assuming diffusion is necessary.
- **Pass:** Independent reviewers can accurately summarize the core explanation and identify no critical factual or visual error.
- **Fail:** The concept depends on assets that cannot be produced reliably or viewers cannot follow the causal story.

### Experiment 5 — Audience pilot

Only after the earlier gates pass, publish a small series with meaningfully distinct topics. Three uploads can test workflow and obvious presentation problems, but are not enough to establish a stable market or monetization outcome.

- Record publication dates, titles, thumbnail variants, impressions, CTR, views, average view duration, retention graph, traffic sources, comments, and subscriber conversion when YouTube Studio makes them available.
- Separate Shorts metrics from long-form metrics.
- Do not compare Shorts “viewed vs. swiped away” directly with long-form CTR.
- Assess performance after a predefined observation window and compare against the channel’s own baseline where available.
- **Pass:** The series demonstrates acceptable production repeatability and at least one promising audience signal that merits a second test.
- **Fail:** No evidence of audience interest after a reasonable, predeclared test, or production burden exceeds the owner’s budget.
- No single CTR, AVD, view count, or RPM cutoff should trigger an automatic niche decision without context.

## 9. Quality gates for any pilot

A video cannot be marked ready to publish unless all required checks pass.

### Editorial and factual accuracy
- Every material claim has a traceable source.
- Primary sources are preferred for incident post-mortems, technical documentation, public data, scientific claims, and official statistics.
- Inferences and uncertain explanations are explicitly qualified.
- Conflicting evidence is documented rather than hidden.
- No invented viewer quotes, metrics, or citations.

### Visual quality
- Text remains readable on a phone.
- Diagrams and maps are custom explanatory assets, not decorative filler.
- Geography, labels, scale, and causal arrows are checked.
- Generated visuals do not serve as evidence for real events or precise anatomy.
- A static visual should remain only as long as it contributes to comprehension; no universal maximum duration is assumed before testing.

### Audio and edit
- Narration is intelligible, naturally paced, and correctly pronounced.
- Loudness is measured with the chosen tool and checked by listening; target levels must be documented consistently rather than assumed to guarantee quality.
- No clipping, gaps, repeated phrases, or synchronization errors.
- Captions and on-screen claims are proofread.

### Originality, rights, and platform policy
- Each episode has a distinct question, argument, and explanatory contribution.
- Assets, music, sound effects, fonts, maps, datasets, and model licenses are recorded.
- Public availability does not automatically mean public-domain status or permission to reuse.
- Review YouTube’s current monetization, reused-content, advertiser-suitability, and altered/synthetic-content disclosure rules before publishing.
- Human review is mandatory; automatic publication is out of scope.

## 10. Risk register

| Risk | Consequence | Mitigation / evidence required |
|---|---|---|
| Audience demand overestimated | Time invested in a weak niche | Traceable multi-channel sample and small pilot |
| Creator halo mistaken for format demand | Competitor success fails to transfer | Include smaller channels and counterexamples |
| Unverified claims in scripts | Loss of trust and factual errors | Claim-level source ledger and editorial review |
| Generic/template-like output | Weak viewer value and monetization risk | Distinct thesis, original diagrams, material episode variation |
| AI visuals distort facts | Misleading maps, mechanisms, or anatomy | Use data-driven geometry; label reconstructions; manual QC |
| Model cannot run reliably on T4 | Lost sessions and wasted time | Smoke test, batch logs, local persistence |
| Kaggle interruption / data loss | Rework or artifact loss | Idempotent tasks, checksums, durable local copy |
| Copyright/licensing error | Claims, takedowns, or legal exposure | Asset registry and license review |
| Excessive manual work | Unsustainable publishing cadence | Track active labor per stage |
| Weak monetization economics | Channel not financially viable | Do not forecast RPM; evaluate real analytics only when available |

## 11. Decision records

### ADR-001 — Validate format before building a general engine

**Status:** PROPOSED  
**Decision:** Run research and visual pilots before production-system implementation.  
**Rationale:** The largest unresolved risk is not GPU capability; it is whether a differentiated format can be researched and produced at acceptable quality and workload.  
**Alternatives:** Build the engine first; reject. This risks automating an unvalidated format.  
**Reversal condition:** Only reconsider after a candidate passes the research, rendering, and pilot gates.

### ADR-002 — Use deterministic visuals as the baseline

**Status:** PROPOSED  
**Decision:** Start with custom vector diagrams, charts, sourced map layers, and simple motion. Use image generation only when a comparative test shows clear value.  
**Rationale:** Deterministic visuals are easier to fact-check, revise, and reproduce than generated geographic or anatomical details.  
**Alternatives:** Make diffusion-generated imagery the primary visual dependency; deferred pending evidence.  
**Reversal condition:** A model-assisted pipeline consistently improves viewer comprehension or production efficiency without introducing unacceptable factual defects.

### ADR-003 — Keep two primary candidates through initial validation

**Status:** PROPOSED  
**Decision:** Compare system/outage explainers and supply-chain/infrastructure explainers; keep prehistoric science as a reserve.  
**Rationale:** Candidate A minimizes GPU dependency but may require specialist technical verification. Candidate B offers concrete spatial storytelling but requires sourced data and geographic QA. A small comparison is more defensible than choosing from unverified claims.  
**Alternatives:** Commit immediately to system post-mortems; rejected for now because the evidence in the current README does not validate demand or workload.  
**Reversal condition:** One candidate demonstrates a clear, documented advantage in repeatable demand, audience comprehension, and feasible production effort.

### ADR-004 — Do not encode monetization or revenue guarantees

**Status:** PROPOSED  
**Decision:** Treat monetization eligibility and revenue as uncertain outcomes; follow current official policies and measure only when real channel analytics are available.  
**Rationale:** Public view counts do not reveal RPM or monetization approval, and policy compliance cannot be guaranteed by format alone.  
**Reversal condition:** None; this is a documentation and governance principle.

## 12. Open questions blocking implementation

1. What exact CPU, RAM, GPU, storage, and operating-system resources are available on the local machine?
2. Which models and model versions are actually present in Kaggle, and can they be used under their license and access conditions?
3. What does a verified 700–1,000-word script cost in active research and editing time for candidates A and B?
4. Can a 45–90 second prototype communicate a clear causal explanation without character animation or generative video?
5. Which specific videos across large and small channels demonstrate repeated demand, and what counterexamples exist?
6. Do comments contain repeated, verifiable requests for a deeper explanation, or are apparent gaps based only on a cursory search?
7. Which data sources and map licenses are suitable for the supply-chain candidate?
8. Can the creator sustain the required publication cadence without sacrificing research quality?
9. What audience signals from the first pilot justify a second test?
10. What is the actual local-to-Kaggle transfer and recovery mechanism? It has not been demonstrated.
11. Which narration method gives acceptable pronunciation, pacing, licensing, and audio quality?
12. What rights-clearance and disclosure checklist will be used before each upload?

## 13. Current decision memo

### Established by cited external documentation
- YouTube’s monetization policy explicitly addresses repetitive or mass-produced “inauthentic content” and distinguishes reused content. Originality and viewer value matter; AI assistance alone does not establish a violation or guarantee eligibility. Source: https://support.google.com/youtube/answer/1311392.
- Manim documents both Cairo and OpenGL rendering options. That supports the availability of deterministic animation methods, not a performance claim for this project’s hardware. Sources: https://docs.manim.community/en/stable/reference/manim.constants.RendererType.html and https://docs.manim.community/en/stable/guides/configuration.html.
- FLUX.1-schnell’s model card identifies its architecture class, step range, and license. It does not prove execution reliability on the project’s Kaggle T4. Source: https://huggingface.co/black-forest-labs/FLUX.1-schnell.
- SDXL base 1.0 has a published model card and license information; license conditions still require review for the intended use. Source: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0.

### Still uncertain
- Whether any candidate can attract repeat viewers on a new channel.
- Whether the creator can deliver expert-level scripts efficiently.
- Whether the local machine can render the intended video quality within a workable time.
- Whether available models are installed, accessible, licensed for the intended use, and stable on the actual runtime.
- Whether a particular visual style helps retention or click-through.

### Immediate next actions
1. Populate the demand evidence ledger for candidates A and B.
2. Run the local deterministic visual benchmark.
3. Time one sourced script for each candidate.
4. Make two comparable short prototypes.
5. Review the evidence and explicitly approve, revise, or reject the next phase.

### Formal approval

**Project status remains PROPOSED.** No niche, model stack, publishing cadence, or production architecture is formally approved by this document. Approval must be recorded explicitly by the project owner in a dated decision entry.

---

## Appendix A — Source register

All sources below were accessed on **2026-10-20**.

1. YouTube Help, *YouTube channel monetization policies*: https://support.google.com/youtube/answer/1311392
2. Manim Community, *RendererType reference*: https://docs.manim.community/en/stable/reference/manim.constants.RendererType.html
3. Manim Community, *Configuration guide*: https://docs.manim.community/en/stable/guides/configuration.html
4. Black Forest Labs / Hugging Face, *FLUX.1-schnell model card*: https://huggingface.co/black-forest-labs/FLUX.1-schnell
5. Stability AI / Hugging Face, *Stable Diffusion XL base 1.0 model card*: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0

**Evidence limitation:** These sources support platform-policy and tool/model-documentation statements only. They do not independently validate market demand, creator metrics, audience comments, local rendering speed, Kaggle execution, monetization results, or the proposed niche ranking.
