# Artifact Retention Policy

## Tracked source

Track code, notebook templates, kernel metadata, project schemas, tests, and small files required to reproduce an approved workflow. Never track Kaggle credentials, local task databases, project drafts, temporary upload bundles, or downloaded Blender runtimes.

## Selected evidence

Track only evidence needed to support a durable engineering claim: a concise final report, its task/project/kernel identifiers, and hashes for referenced artifacts. Keep the report small and make explicit whether evidence was produced locally or remotely. Do not treat logs or a `COMPLETE` kernel state as a successful product result by themselves.

## Generated outputs

Treat MP4s, `.blend` files, extracted frames, full logs, benchmark output, and runtime caches as generated artifacts. Keep new run output outside Git or in an approved artifact store, with a report containing the source task ID and SHA-256. The generated Kaggle output directories are ignored for future untracked files.

## Historical records

Existing tracked output files are grandfathered evidence. Do not delete or rewrite them as part of cleanup. Any later reduction must be an explicit review that retains the corresponding report, identity, checksum, and retrieval location. The ignore rules do not untrack existing files.

## Before accepting a task result

- Confirm the task and project IDs match the saved input snapshot.
- Confirm required scene, physics, render, and video checks passed.
- Record the actual artifact paths, sizes, and SHA-256 values.
- Record audio as `NOT_AVAILABLE` when no audio artifact exists.
- Keep source, curated evidence, and generated outputs visibly distinct.