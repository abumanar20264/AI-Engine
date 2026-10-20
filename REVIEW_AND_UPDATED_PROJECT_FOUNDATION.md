# AI-Engine: Critical Research Review & Updated Project Foundation

**Document ID:** AI-ENGINE-FOUNDATION  
**Version:** 0.3.0-research-update  
**Status:** PROPOSED — NOT APPROVED FOR IMPLEMENTATION  
**Review date:** 2026-10-20  
**Supersedes:** None. This is an additive review document; the original `README.md` remains unchanged.  
**Repository:** https://github.com/abumanar20264/AI-Engine  
**Scope:** English-language, global-audience video formats and a limited-compute, AI-assisted production workflow. This revision adds a preliminary public-demand scan; it does not validate audience demand for a new channel.

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
5. Which specific videos across large and small channels demonstrate repeated demand, and what counterexamples exist? A preliminary sample is now recorded in Section 13; a matched, systematic sample is still open.
6. Do comments contain repeated, verifiable requests for a deeper explanation, or are apparent gaps based only on a cursory search?
7. Which data sources and map licenses are suitable for the supply-chain candidate?
8. Can the creator sustain the required publication cadence without sacrificing research quality?
9. What audience signals from the first pilot justify a second test?
10. What is the actual local-to-Kaggle transfer and recovery mechanism? It has not been demonstrated.
11. Which narration method gives acceptable pronunciation, pacing, licensing, and audio quality?
12. What rights-clearance and disclosure checklist will be used before each upload?

## 13. Preliminary public-demand study (2026-10-20)

**Status: OBSERVATIONAL DESK RESEARCH — NOT A MARKET FORECAST.** This section records a first public scan of two candidate formats. It is not a randomized sample, not a full competitive audit, and not evidence of likely views, CTR, retention, RPM, or monetization for a new channel.

### 13.1 Research question and method

**Question:** Is there visible, repeated audience demand for (A) engineering/system failures and technical post-mortems, and (B) supply-chain, transport, and infrastructure explainers, across more than one established channel?

**Method used**
- Reviewed public video lists and channel-scan pages with visible titles, view counts, and in several cases upload dates and durations.
- Included multiple channels per candidate rather than treating one successful creator as proof of demand.
- Prioritized long-form examples and included recent uploads where the pages exposed them. Some counterexamples and lower-performing examples are deliberately retained.
- Recorded the displayed counts as a snapshot from pages crawled around 2026-10-20. The underlying pages state that their data is drawn from the YouTube Data API and refreshed periodically; individual counts may differ from a later live view.
- Used public view counts only as **reach signals**. They do not reveal traffic source, click-through rate, retention, viewer satisfaction, production costs, monetization status, or how much of a channel’s audience is transferable to a new creator.

**Limitations:** The sample is purposive and partly based on third-party pages, not a complete export from YouTube Studio. The channels vary greatly in size, age, topic breadth, upload cadence, and video age. The results establish that these subjects can attract viewers; they do not prove that one niche is easier to enter or more profitable. This scan does not include a systematic comment analysis or a reliable estimate of hours required to make each format.

### 13.2 Candidate A — engineering/system failures and technical post-mortems

The candidate includes infrastructure failures, engineering decisions, technical accidents, and causal explanations of how a system failed. The best editorial version is not merely a disaster recap: it explains the mechanism, evidence, decision chain, and what changed afterward.

| Channel / sample video | Public views shown | Signal and caveat |
|---|---:|---|
| Practical Engineering — “The Wild Story of the Taum Sauk Dam Failure” | 11.4M | A clear failure-focused topic can travel far on a large specialist channel; this is an outlier, not a baseline. |
| Practical Engineering — “Bridge Demolition is Complicated” | 576K | A relevant engineering topic can also perform below the channel’s median. |
| Practical Engineering — “The Hidden Engineering of Pressure Regulators” | 808.5K | Recent technical explainer; less sensational but still reached a substantial audience. |
| Practical Engineering — “Every US Electrical Outlet Explained” | 1.4M | Adjacent technical infrastructure topic, not a failure post-mortem. |
| Practical Engineering — “Stopping the Unstoppable” | 5.1M | Engineering intervention / mechanism topic; supports breadth within the engineering-explainer umbrella. |
| Plainly Difficult — “Bridge Collapsed Under …” | 301K | Recent failure/disaster title; exact displayed title is truncated on the statistics page. |
| Plainly Difficult — “Every Corner Cut Led to …” | 618K | A recent causal-failure framing exceeded several other recent uploads on the same channel. |
| Plainly Difficult — “Brand New Dam Fails Catastrophically” | 286K | A failure topic with moderate, not exceptional, reach. |
| Plainly Difficult — “The Deadliest Industrial …” | 250K | Industrial-disaster subject; the page truncates the full title. |
| Brick Immortar — “A COLLISION OF BLAME: The Total Collapse of Baltimore’s Key Bridge” | 446.7K | A topical bridge-collapse analysis; the snapshot was roughly five weeks after publication. |
| Brick Immortar — “DISASTROUS INDIFFERENCE: The Loss of SS El Faro” | 4.75M | Long-tail disaster analysis can accumulate millions of views. |
| Brick Immortar — “CRUSH DEPTH: The Nightmarish Loss of USS Thresher” | 4.7M | Another high-performing technical disaster case on the same channel. |
| Real Engineering — “NASA’S Plutonium Problem” | 4.1M | Adjacent high-stakes engineering/technical systems topic. |
| Real Engineering — “The Insane Engineering of the P-38 Lightning” | 3.6M | Technical engineering storytelling can attract large audiences beyond pure disaster coverage. |

**Sources for Candidate A**
- Practical Engineering channel scan (video list, view estimates, median, and stated sample): https://prepublish.ai/youtube-channel/PracticalEngineeringChannel
- Plainly Difficult video statistics and recent-upload table: https://www.speakrj.com/audit/report/UCb0MyY46T9ZYOzDHkYnIoXg/youtube/media-stats
- Brick Immortar channel statistics and video list: https://vidiq.com/youtube-stats/channel/%40brickimmortar/
- Real Engineering channel scan: https://prepublish.ai/youtube-channel/RealEngineering

**Interpretation:** There is repeated, cross-channel evidence of an audience for failure analysis and engineering explanation. The observed range is wide: from hundreds of thousands to several million views, with exceptional outliers. Therefore, the evidence supports **topic viability**, not a reliable expected-view estimate. Candidate A’s differentiation opportunity is a more rigorous, visual, source-led causal explanation—not copying disaster thumbnails or narration patterns.

**Production implications (inference, not measured):**
- A causal timeline, failure tree, annotated diagram, sourced photographs, and simple physics/engineering animations can explain many cases without recurring characters or generated video.
- Fact-checking may be demanding: distinguish confirmed findings, preliminary reports, competing hypotheses, and hindsight claims. Avoid assigning blame beyond what primary investigations support.
- Copyright clearance can be material if the format relies on CCTV, news clips, crash footage, or documentary footage. A vector-first visual language reduces dependency on unlicensed clips but does not remove the need for source attribution and careful evidence handling.
- Some topics are emotionally sensitive. Avoid exploitative thumbnails, graphic footage, and overconfident causal claims.

### 13.3 Candidate B — supply chain, transport, and infrastructure explainers

The candidate explains how goods, people, energy, and infrastructure systems work: logistics networks, railways, airports, shipping, roads, construction projects, and the economics or bottlenecks that shape them.

| Channel / sample video | Public views shown | Signal and caveat |
|---|---:|---|
| Wendover Productions — “How the Channel Tunnel Works” | 2.1–2.2M | Recent long-form infrastructure explainer with substantial reach. Different trackers show slightly different snapshots. |
| Wendover Productions — “How the Trucking Industry Got So Terrible” | 3.9M | Strong example of a familiar system reframed around a problem. |
| Wendover Productions — “The Logistics of Natural Gas” | 2.3–2.4M | Complex supply-chain topic with broad explanatory framing. |
| Wendover Productions — “The Logistics of Music Festivals” | 1.3M | Shows that logistics can be applied to a non-industrial, relatable subject. |
| Wendover Productions — “The Logistics of Fruit” | 1.22M | Concrete everyday product connected to a global distribution system. |
| Wendover Productions — “The Design of Airline Route Networks” | 1.7M | A systems/network explanation with clear visual potential. |
| Wendover Productions — “Why Japanese Railways Win” | 1.8M | Transport comparison with an understandable central question. |
| Wendover Productions — “The Failed Logistics of Hurricane Katrina” | 890K | A failure-related logistics story; below the channel’s reported median, useful as a counterexample. |
| Half as Interesting — “Why Does the World’s Biggest Ship Exist?” | 1.17M | A specific transport question reached over one million views. |
| Half as Interesting — “This Is the Shortest Train in the United States” | 728K | A narrower rail topic still drew a substantial audience. |
| Half as Interesting — “The Crazy-Fast Logistics of Flower Distribution” | 167.6K | Counterexample: a logistics topic can underperform even on a relevant established channel. |
| The B1M — “The UK’s £49BN Heathrow Gamble” | 1.33M | Recent airport-capacity/infrastructure story with clear stakes and a project angle. |
| The B1M — “Can Britain’s Houses of …” | 647K | A recent built-environment topic; the source page truncates the title. |
| RealLifeLore — “The Incredible Logistics Behind the World’s Longest Flight” | 696K | Logistics can work inside broader geography/aviation storytelling, though this example is below one million. |
| Mustard — “Could This Change Air Travel Forever?” | 13M | Strong long-tail aviation example, but older and not a fair benchmark for a new channel’s early performance. |

**Sources for Candidate B**
- Wendover Productions channel scan and recent uploads: https://prepublish.ai/youtube-channel/Wendoverproductions
- “The Logistics of Fruit” YouTube video page: https://www.youtube.com/watch?v=NmhDcZHg7ik
- Half as Interesting channel scan: https://prepublish.ai/youtube-channel/halfasinteresting
- “Why Does the World’s Biggest Ship Exist?” YouTube video page: https://www.youtube.com/watch?v=WFxnsU1hu9k
- The B1M video page for “The UK’s £49BN Heathrow Gamble”: https://www.youtube.com/watch?v=x-yXy6NLWGY
- The B1M recent video statistics: https://www.speakrj.com/audit/report/UC6n8I1UDTKP1IWjQMg6_TwA/youtube/media-stats
- RealLifeLore channel scan: https://prepublish.ai/youtube-channel/RealLifeLore
- Mustard channel scan: https://prepublish.ai/youtube-channel/MustardChannel

**Interpretation:** Candidate B has repeated demand across several distinct channel brands and a wide range of subject applications. Strong examples often connect a complex system to a clear human-scale question, a constraint, a failure, a cost, or a surprising consequence. However, the lower-performing flower-logistics and Hurricane Katrina examples show that the category label itself does not guarantee performance. The large Wendover results also reflect a mature channel, established audience, and high production quality; they cannot be treated as a forecast for a new entrant.

**Production implications (inference, not measured):**
- Maps, flow diagrams, route/network graphics, timelines, charts, and annotated public documents offer a credible CPU-first production style.
- The format needs careful data provenance: route geometry, trade figures, capacity, dates, project budgets, and comparisons must be sourced and dated.
- Some infrastructure stories can be evergreen; project delays, policy disputes, strikes, disruptions, and new capacity decisions can create timely angles. A balanced channel plan should not depend entirely on news cycles.
- Topic selection should focus on a sharp explanatory question rather than a generic “how supply chains work” treatment.

### 13.4 Cross-candidate comparison

| Criterion | Candidate A: failures / technical post-mortems | Candidate B: supply chain / infrastructure |
|---|---|---|
| Evidence of existing audience | Present across Practical Engineering, Plainly Difficult, Brick Immortar, and Real Engineering | Present across Wendover, Half as Interesting, The B1M, RealLifeLore, and Mustard |
| Range of observed results | Hundreds of thousands to multi-million-view examples; notable outliers | Hundreds of thousands to multi-million-view examples; notable outliers |
| Repeatable visual grammar | Failure timeline, mechanism diagram, fault tree, evidence board, before/after | Map, network flow, capacity constraint, route comparison, timeline, cost breakdown |
| Main research burden | Technical correctness, investigation findings, causality, attribution, footage rights | Data freshness, map/route accuracy, economic assumptions, source comparability |
| Main editorial risk | Sensationalism, premature blame, graphic or reused footage | Generic broad explainers, unsupported statistics, overly broad topic scope |
| Initial production hypothesis | Strong fit for focused case studies and vector diagrams | Strong fit for maps and system diagrams; potentially broader topic supply |
| Evidence that is still missing | Actual time-to-research, repeatable production effort, pilot audience response | Actual time-to-research, repeatable production effort, pilot audience response |

**No aggregate winner is declared.** The sample is not random or matched for video age, channel size, or production budget. Summing or averaging these counts would create false precision. The most defensible conclusion is that both candidates are viable enough to justify a controlled pilot, and neither has been proven superior for a new creator.

### 13.5 Updated recommendation

**Proposed next step: run a six-video pilot, not a production-engine build.** Produce three videos in each candidate format using the same constraints:
1. Comparable target length and narration standard.
2. A written source ledger and claim-level fact check.
3. Primarily deterministic visuals; no multi-character animation requirement.
4. Record active labor separately for research, scripting, visual creation, narration, editing, and quality assurance.
5. Record visual defects, factual corrections, rendering time, and any paid or licensed assets.
6. If published, evaluate results after a predeclared window and report views together with impressions, CTR, average view duration, retention, and traffic source where YouTube Studio exposes them. Do not judge solely by raw views or a single viral outlier.
7. If publication is not yet appropriate, compare blind internal reviews for factual clarity, comprehension, pacing, and production time; treat that as a production test, not a demand test.

For each candidate, select one topic that is evergreen and one with a clear current or practical consequence, plus a third topic chosen from the evidence review. Do not make all three episodes variants of the same headline. Keep the audience, production quality bar, and length comparable enough that the test is interpretable.

### 13.6 Monetization and AI policy guardrail

YouTube’s official policy says repetitive or mass-produced “inauthentic content” can be ineligible for monetization; reused content is assessed separately. The policy also says the substance should offer original creative, educational, or entertainment value, and that using automated tools does not by itself determine eligibility. Therefore, the engine should automate workflow steps, not mass-produce interchangeable episodes. Each video needs a distinct thesis, independently verified research, original explanatory value, and meaningful editorial review.

Primary source: https://support.google.com/youtube/answer/1311392

### 13.7 Research log and confidence

- **Research date:** 2026-10-20.
- **Candidate A:** At least four distinct channels reviewed; multiple relevant videos documented.
- **Candidate B:** At least five distinct channels reviewed; multiple relevant videos documented.
- **Confidence that these broad subjects have existing audiences:** Moderate.
- **Confidence about which candidate is better for a new channel:** Low.
- **Confidence about monetization, RPM, CTR, retention, or workload:** Insufficient evidence.
- **Sample coverage:** More than eight relevant video examples are documented for each candidate, spanning at least four channels per candidate. This is a purposive desk sample, not a matched or randomized sample, and it does not contain eight examples from every channel.
- **Not done:** No comment-level demand analysis, no systematic matched sample, no direct YouTube Studio analytics, no new-channel pilot, no production timing experiment, and no model/Kaggle benchmark.

### 13.8 Sources added in this revision

1. Practical Engineering channel scan: https://prepublish.ai/youtube-channel/PracticalEngineeringChannel
2. Plainly Difficult recent video statistics: https://www.speakrj.com/audit/report/UCb0MyY46T9ZYOzDHkYnIoXg/youtube/media-stats
3. Brick Immortar video statistics: https://vidiq.com/youtube-stats/channel/%40brickimmortar/
4. Real Engineering channel scan: https://prepublish.ai/youtube-channel/RealEngineering
5. Wendover Productions channel scan: https://prepublish.ai/youtube-channel/Wendoverproductions
6. Half as Interesting channel scan: https://prepublish.ai/youtube-channel/halfasinteresting
7. The B1M video statistics: https://www.speakrj.com/audit/report/UC6n8I1UDTKP1IWjQMg6_TwA/youtube/media-stats
8. RealLifeLore channel scan: https://prepublish.ai/youtube-channel/RealLifeLore
9. Mustard channel scan: https://prepublish.ai/youtube-channel/MustardChannel
10. YouTube Help, monetization policies: https://support.google.com/youtube/answer/1311392

---

## 14. Additional candidate review — cross-generational, family-friendly visual content

**Status: PROPOSED CANDIDATE EXPANSION.** The following three formats were proposed for the global English-language audience: (C) size and scale comparisons, (D) animal hypotheticals / unusual biology, and (E) visual riddles / brain teasers. This section evaluates their fit against the project's constraints and a small public evidence scan. It does not approve a niche or substantiate claims of guaranteed virality.

### 14.1 Correct the core premise

“Family-friendly” and “made for kids” are not synonyms. YouTube says a video is not automatically made for kids simply because it is safe for everyone or children may watch it; the decision depends on intended audience and other factors. A video aimed at children as one of its target audiences can count as child-directed or “mixed audience,” so the creator must make the audience declaration accurately rather than selecting “not made for kids” merely to preserve features. Sources:
- YouTube Help, *Determining if your content is made for kids*: https://support.google.com/youtube/answer/9528076
- YouTube Help, *Set your channel or video's audience*: https://support.google.com/youtube/answer/9527654

This is a strategic choice, not a cosmetic label. If content is designated “made for kids,” YouTube restricts features including comments and personalized ads, alongside other engagement and monetization features. See: https://support.google.com/youtube/answer/9609276. Do not assume a family-friendly general-audience strategy is automatically a child-directed strategy, and do not misclassify child-directed content for commercial convenience.

The claim that cross-generational videos achieve “fantastic” retention or that replay loops guarantee recommendation is **not established**. YouTube's official explanation groups recommendation signals into appeal, engagement, and satisfaction, and emphasizes matching videos to viewers. Looping may be one observed behavior, but it is not a standalone guarantee. Sources:
- https://support.google.com/youtube/answer/16533387
- https://support.google.com/youtube/answer/16559650
- https://support.google.com/youtube/answer/16559651

### 14.2 Candidate C — size and scale comparisons

**Public evidence sampled**
- MoreBeckBros, “How BIG is Universe (Size Comparison)” — approximately 3.73 million views at the YouTube page snapshot: https://www.youtube.com/watch?v=TiUMtIxE_KE
- Mr Scientific, “UNIVERSE SIZE COMPARISON” — approximately 4.35 million views at the YouTube page snapshot: https://www.youtube.com/watch?v=fCmWZehG7Bg
- “Universe Size Comparison 2025” and “Ultimate Geography Size Comparison” were listed at roughly 151.5K and 168.1K views respectively on a third-party comparison page: https://socialcounts.org/compare/youtube-video-live-view-count/VxFY-Zq77CQ/youtube-video-live-view-count/0GmsjfIRs8w
- A small comparison-focused channel, Spacemarioedition, was listed with about 4.28K subscribers and 1.77M lifetime channel views; its cited long-form comparison had far fewer views than a popular Short. These are third-party snapshots, not verified analytics: https://universe-size-comparison.fandom.com/wiki/Spacemarioedition

**Interpretation:** There is evidence that universe/scale comparison is a viable visual subject, including large-view examples and smaller results. The public sample is not sufficient to claim “viral success” is typical, nor does it show that children and adults watch the same videos in equal proportions.

**Technical fit — high (inference):**
- Deterministic vector scaling, labeled silhouettes, rulers, logarithmic scales, and camera moves can be rendered without character animation or diffusion models.
- This is a good CPU-first prototype candidate; T4 use may be unnecessary unless optional art assets are generated.
- The main accuracy trap is false comparability: size, mass, volume, distance, age, and scale are different measures. Astronomical objects may have uncertain or changing estimates. Each comparison needs a declared unit, scale, and source, with logarithmic scaling clearly labeled where used.
- The niche is already familiar. Distinctive value must come from a strong question, accurate scale, pacing, and a surprising but well-supported sequence—not just a generic countdown.

**Proposed verdict:** Highest initial technical feasibility of the three new candidates; audience fit remains a hypothesis.

### 14.3 Candidate D — animal hypotheticals and unusual biology

**Public evidence sampled**
- WildCiencias was listed with approximately 573K subscribers and 191M channel views, with recent topics including animal-vs-animal questions and hypothetical introductions of predators into new ecosystems: https://similarchannels.com/c/wildciencias
- Animal Battle TV was listed at about 649K subscribers and 15.38M lifetime views; its top-video list includes hypothetical animal/prehistoric matchups from hundreds of thousands to a few million views: https://vidiq.com/youtube-stats/channel/UCYBn79tqT7g172gJUkuN5DQ/
- A channel describing itself as “WHAT IF WILD LIFE” explicitly describes its animal encounters as AI-generated simulations rather than real events: https://vling.net/en/channel/UCHqZ90v7_IHap8gdH5DV71A/channel-info

**Interpretation:** There is an existing audience for animal comparisons and hypothetical encounters, but the examples include stylized, game-like, or AI-simulated content. They do not prove demand for a more scientifically rigorous format or show that hypothetical “who would win” claims can be answered objectively.

**Technical fit — medium to high (inference):**
- Static animal plates with slow pans, parallax, silhouettes, range/weight/force graphics, and habitat maps are feasible without multi-character animation.
- Accurate anatomy, proportions, behavior, habitat, and extinct-animal reconstructions need reference sources and human review. Generated art can invent anatomical errors.
- “Who would win?” is often underdetermined: species, size, age, health, terrain, surprise, and behavior alter outcomes. Present scenarios and uncertainties rather than asserting a scientific certainty.
- Repeated AI-generated fights can become interchangeable or misleading. Each episode should have a distinct educational thesis and clearly label fictional scenarios.

**Proposed verdict:** Viable visual storytelling option, but greater risk of sensationalism, scientific overclaim, and generic AI output than size comparisons.

### 14.4 Candidate E — visual riddles and brain teasers

**Public evidence sampled**
- Hanging Out's public statistics page lists “Brain Teasers 65 #shorts” at approximately 11.23M views, while another brain-teaser Short is listed at about 6.08M views. The same page also shows a riddle video at roughly 154K views, a useful counterexample to uniform success: https://us.youtubers.me/hanging-out/youtube-videos-stats
- AJESU 1M is described as an English-language guessing/quiz channel, with about 4M subscribers and 1.5B total views across hundreds of videos in a third-party channel profile: https://open.subsub.io/channels/ajesu1m/view
- MindYourLogic Studios describes multiple quiz/riddle brands and reports large combined audiences across its channels: https://studios.mindyourlogic.com/Youtube
- Riddles for Shorts's public vidIQ page shows high channel subscriber count but relatively low view counts for several listed recent long-form puzzle videos. The channel's performance varies by format and upload: https://vidiq.com/youtube-stats/channel/UCcwxYuyhVkG0BCk43NMhAZQ/

**Interpretation:** Brain teasers and guessing formats can reach very large audiences, especially as Shorts, but results vary materially by format, channel, and individual upload. This evidence does not establish that the format is easy to differentiate or that a high replay rate guarantees recommendation.

**Technical fit — very high (inference):**
- Most puzzles can be made with deterministic code and tested for exactly one intended answer.
- Production cost is likely low relative to researched science explainers, but actual active labor has not been measured.
- Quality control is critical: ambiguity, incorrect answer keys, cultural/English-language assumptions, inaccessible color-only clues, and reused puzzle templates can damage trust.
- The format has a high commoditization risk. A channel must add original puzzle design, coherent difficulty progression, clear solutions, and a recognizable visual identity.
- If the content is directed at children, the audience declaration and associated feature limitations must be considered before choosing a comment-driven growth strategy.

**Proposed verdict:** Easiest low-cost production experiment, but differentiation and long-term channel identity are major risks.

### 14.5 Comparative scorecard

Ratings below are qualitative planning judgments, not measured performance. “High” means a relative fit with current project constraints, not a forecast of views.

| Criterion | C: Scale comparisons | D: Animal hypotheticals | E: Visual riddles |
|---|---|---|---|
| CPU/vector production fit | High | Medium–high | Very high |
| Need for generative imagery | Low / optional | Medium if using animal plates | None required |
| Research / fact-check burden | Medium–high | High | Low–medium, but answer validation is strict |
| Differentiation challenge | High | High | Very high |
| Risk of misleading factual claims | Medium | High | Medium (ambiguous or wrong solutions) |
| Evergreen potential | High | High | High, though puzzle format competition is dense |
| Fit for long-form depth | High if scale is explained, not just ranked | Medium–high | Medium; requires more than repeated short puzzles |
| Fit for Shorts | High | High | High |
| Best first experiment | 45–60s scale sequence with sourced units | One clearly labeled hypothetical with evidence and uncertainty | One original puzzle with unambiguous solution |

### 14.6 Updated project recommendation

Do not fold all three new concepts into one channel without a unifying editorial promise. “Interesting things for everyone” is too broad to guide topic choice, visual identity, or returning-viewer expectations.

**Recommended test order**
1. **First test: scale and size comparisons.** It has the cleanest fit with vector graphics, no character continuity, low GPU dependence, and a clear visual progression. Treat this as the leading *prototype candidate*, not a proven best niche.
2. **Second test: animal biology / hypothetical comparisons.** Test a science-led treatment with explicit uncertainty and accurate visuals, not a generic AI fight.
3. **Separate low-cost benchmark: visual riddles.** Test this as a different channel-format hypothesis. Do not combine puzzle Shorts with scale-science long-form until audience overlap is demonstrated.

For a fair initial comparison, create one short prototype per format under the same production budget and quality gate. Record: active labor, factual defects, number of visual assets, rendering time, comprehension feedback from a small test group, and whether the premise is understandable without sound. If publishing, collect the same YouTube Studio measures after a predeclared time window. Do not use raw views alone to compare Shorts with long-form videos, or channels with different sizes and ages.

### 14.7 What remains unproven

- Whether the same viewers watch a candidate format alongside children or across multiple age groups.
- Whether any candidate has above-average retention or repeat viewing relative to comparable videos.
- Whether a new channel can break through without a large existing audience.
- Whether size comparisons are less crowded or more profitable than other candidates.
- Whether animal hypotheticals or riddles lead to better audience return, subscriber conversion, or production economics.
- Whether the creator's intended audience should be declared “made for kids,” “not made for kids,” or varies by individual video. This must be decided from the actual creative intent and content, not from a growth tactic.

### 14.8 Sources added in this revision

1. YouTube Help, *Determining if your content is made for kids*: https://support.google.com/youtube/answer/9528076
2. YouTube Help, *Set your channel or video's audience*: https://support.google.com/youtube/answer/9527654
3. YouTube Help, *What happens when content is made for kids*: https://support.google.com/youtube/answer/9609276
4. YouTube Help, *YouTube's Recommendation System*: https://support.google.com/youtube/answer/16533387
5. YouTube Help, *Understand content performance*: https://support.google.com/youtube/answer/16559650
6. YouTube Help, *Good to know about recommendations*: https://support.google.com/youtube/answer/16559651
7. MoreBeckBros, *How BIG is Universe (Size Comparison)*: https://www.youtube.com/watch?v=TiUMtIxE_KE
8. Mr Scientific, *UNIVERSE SIZE COMPARISON*: https://www.youtube.com/watch?v=fCmWZehG7Bg
9. SocialCounts comparison page: https://socialcounts.org/compare/youtube-video-live-view-count/VxFY-Zq77CQ/youtube-video-live-view-count/0GmsjfIRs8w
10. Spacemarioedition channel overview: https://universe-size-comparison.fandom.com/wiki/Spacemarioedition
11. WildCiencias channel overview: https://similarchannels.com/c/wildciencias
12. Animal Battle TV statistics: https://vidiq.com/youtube-stats/channel/UCYBn79tqT7g172gJUkuN5DQ/
13. WHAT IF WILD LIFE channel overview: https://vling.net/en/channel/UCHqZ90v7_IHap8gdH5DV71A/channel-info
14. Hanging Out video statistics: https://us.youtubers.me/hanging-out/youtube-videos-stats
15. AJESU 1M channel overview: https://open.subsub.io/channels/ajesu1m/view
16. MindYourLogic Studios: https://studios.mindyourlogic.com/Youtube
17. Riddles for Shorts statistics: https://vidiq.com/youtube-stats/channel/UCcwxYuyhVkG0BCk43NMhAZQ/

---

## 15. Current decision memo

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
1. Treat the public-demand scans in Sections 13 and 14 as preliminary evidence, not a niche decision.
2. Approve a prototype shortlist explicitly; current leading prototype candidate is scale/size comparisons, with animal biology and visual riddles as separate hypotheses.
3. Produce one short prototype per selected format under a comparable quality and time budget.
4. Record active labor, factual defects, rendering time, and comprehension feedback; if published, compare YouTube Studio analytics over a predeclared window.
5. Only after the prototype gate, decide whether to run a six-video pilot or build production tooling.

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
