# Historical Saturn Toolchain & SDK Evidence Guide

This document is mandatory guidance for reverse-engineering tasks that use historical Sega Saturn development tools, SDK/library documentation, compiler/assembler/linker behavior, preserved source trees, binary fingerprints, or development-kit artifacts as evidence.

It does **not** establish which toolchain, SDK, libraries, or build environment Ancient used for The Story of Thor 2. That remains `UNKNOWN` until project-specific evidence proves it.

## Purpose

Historical development material can accelerate reconstruction by separating likely platform/library boilerplate from Ancient-specific game logic and by explaining code layout, object/link behavior, padding, relocation, startup code, generated helpers, library call shapes, and resource APIs.

The goal is not to recreate a 1996 Saturn development environment for its own sake. The goal is to extract bounded, reproducible evidence that improves Thor 2 module/boundary/semantic confidence.

## Non-negotiable boundary

Historical toolchains and SDKs are **evidence sources only**.

They must never:

- become an unreviewed production runtime dependency;
- replace reverse engineering of game-specific behavior;
- justify semantic names without Thor 2 binary/runtime evidence;
- cause proprietary SDK binaries, leaked/private material, commercial game data, or copyrighted source trees to be committed;
- cause the project to search for/download stolen or private development archives;
- be treated as proof that Ancient used a tool/library merely because Sega or another Saturn developer used it.

Public manuals, public preservation documentation, public interviews, public/open-source material, and user-supplied local tools may be analyzed. If licensing/provenance is unclear, keep binaries local and record only bounded derived observations necessary for RE.

## Candidate categories are hypotheses, not identity claims

Potential historical evidence may include, for example:

- Sega Saturn system/library documentation;
- Sega graphics/audio/file-system libraries;
- Hitachi SH-2 assembler/compiler/linker behavior;
- other period Saturn cross-development toolchains;
- public/open-source Saturn code with known provenance;
- library signatures and preserved manuals;
- game-specific debug/build strings.

These categories establish possibilities only. Do not claim Ancient used any candidate without project-specific evidence.

## Evidence hierarchy for toolchain/library claims

### Level A — direct project artifact

Examples:

- original Thor 2 source/build script naming a tool/library;
- original map/list/object/link command/build log;
- embedded build/tool version string demonstrably belonging to this game;
- developer statement specifically naming the toolchain/library for Thor 2.

With provenance checks, Level A may support `CONFIRMED`.

### Level B — distinctive binary fingerprint plus independent support

Examples:

- multiple unusual assembler/linker/compiler quirks reproduced by one candidate;
- distinctive library implementation matching exact topology/constants/strings;
- characteristic relocation/padding/layout behavior repeated across independently bounded regions;
- candidate match plus period/project-specific corroboration.

May support `HIGH` and only exceptionally `CONFIRMED` when evidence is distinctive and independently corroborated.

### Level C — ordinary opcode/layout similarity

Examples:

- generic SH-2 prologue/epilogue;
- common `JSR`, branch, move, stack-save, literal-pool, or alignment patterns;
- ordinary compiler-like register allocation;
- even/word alignment.

This is weak `HYPOTHESIS` evidence. Ordinary SH-2 machine code is not toolchain identity.

### Level D — ecosystem association

Examples:

- Sega distributed/supported a library/tool;
- another Saturn game used it;
- it was common in the period.

This establishes historical plausibility only.

## Required workflow for historical toolchain/library tasks

### 1. Define one bounded question

Good:

- Does one known Thor 2 block match a distinctive public library implementation?
- Can a candidate tool reproduce an unusual literal-pool/alignment/relocation pattern?
- Does a suspected filesystem/CD helper correspond to a known library function signature?
- Can a library signature strengthen a specific function boundary?

Bad:

- Identify the compiler for the whole game.
- Label every common helper as Sega SDK code.
- Rebuild the project with an old SDK before proving relevance.

### 2. Inventory only approved evidence

Allowed sources include:

- the project owner's private canonical Thor 2 image/revision;
- public technical manuals and bulletins;
- public preservation documentation;
- public/open-source Saturn source/disassemblies/decomp projects;
- user-supplied local historical tools with acceptable provenance.

Do not fetch proprietary/leaked SDK packages merely because references to them exist.

### 3. Record exact provenance

For every external artifact used in a conclusion record:

- artifact/tool/library name;
- version if known;
- public URL or local-user-supplied status;
- license/provenance limitation;
- whether the artifact is stored in the repository (normally NO for binaries/source with unclear rights);
- exact bounded observation derived from it.

### 4. Build a controlled fingerprint corpus

If a legitimate candidate tool/library is available, use tiny deterministic probes designed to distinguish behaviors.

Useful SH-2/toolchain cases can include:

- direct/indirect call forms;
- short/long branch selection where applicable;
- PC-relative literal loads;
- alignment and literal-pool placement;
- forward references;
- jump tables;
- section ordering;
- relocatable references;
- padding/fill behavior;
- ABI/callee-save patterns only when combined with more distinctive features.

Keep probes small. They are evidence experiments, not a new software project.

### 5. Retain potentially distinguishing features

Record features such as:

- selected instruction/addressing form;
- register choice only when actually distinctive;
- branch topology;
- literal-pool placement;
- padding/fill bytes;
- section/symbol ordering;
- relocation placement/type;
- linker layout;
- library strings/constants/tables;
- object/map/list metadata when legally inspectable.

Do not mask meaningful opcode/register/flow differences merely to improve a match score.

### 6. Normalize relocations conservatively

Distinguish:

- exact bytes;
- relocation/address-only difference;
- immediate-only difference;
- same instruction topology with different constants;
- structural-only similarity;
- mismatch;
- non-discriminating.

A relocation-tolerant match must document exactly which fields were normalized.

### 7. Start from independently evidenced Thor 2 ranges

Fingerprint known/candidate ranges only after revision/module provenance is established enough for the question being asked. Do not scan the entire image until a bounded fingerprint proves useful discriminatory power.

### 8. Separate toolchain/library identity from game semantics

A probable library/toolchain match may establish:

- likely boilerplate/library boundary;
- stronger code/data/function-boundary hypothesis;
- probable API contract;
- possible relocation/layout explanation.

It does **not** establish gameplay meaning.

`matches candidate filesystem helper` does not justify renaming a caller `LoadPlayerInventory`.

### 9. Combine independent evidence

Prefer conclusions supported by two or more of:

- static binary fingerprint;
- runtime execution/call evidence;
- exact strings/tables;
- cross-revision correspondence;
- public source/library correspondence;
- historical tool output;
- official documentation.

Toolchain/library evidence raises confidence only when it agrees with game-specific evidence.

### 10. Stop when discriminatory value is low

If several candidate tools/libraries produce indistinguishable ordinary code, record `non-discriminating` and stop expanding the probe. Do not manufacture a winner.

## Library signature discipline

Automatic library signatures are candidate generators, not truth.

For each hit:

1. record signature source/version;
2. record matched range and exact match strength;
3. inspect xrefs/call topology;
4. compare expected side effects/API contract;
5. seek runtime confirmation when the semantic label matters;
6. keep a generic/address-based name if evidence is insufficient.

A signature hit alone must not become `CONFIRMED` gameplay semantics.

## Candidate scoring discipline

Prefer explicit evidence over opaque probability scores.

Example:

```text
candidate: historical library helper X
exact distinctive matches: 2
relocation-only matches: 3
non-discriminating matches: 8
mismatches: 1
confidence: HYPOTHESIS
reason: no project-specific artifact identifies the library
```

Do not invent percentages without a defined and validated scoring model.

## Interaction with dynamic oracle

Dynamic evidence can establish that a candidate range executes and can reveal inputs/outputs/side effects. It cannot identify a compiler/assembler by itself.

Useful combined flow:

```text
module/boundary evidence
      +
runtime execution evidence
      +
historical tool/library fingerprint
      +
official/public documentation
      -> stronger bounded hypothesis
```

## Cross-revision interaction

When multiple legally available Thor 2 revisions/patches are analyzed, unchanged or relocatable blocks can strengthen a library/boilerplate hypothesis, but stable code may also be Ancient-owned. `unchanged across builds` is not equivalent to `SDK`.

## Hard stops

Stop and report before proceeding if:

- the only next step is downloading proprietary/leaked/private SDK/tool material;
- provenance is too unclear to use responsibly;
- the experiment requires committing copyrighted historical source/binaries;
- a candidate match is non-discriminating;
- the task expands into whole-game compiler identification;
- production C++ would be changed based only on a toolchain/library hypothesis;
- the task conflicts with the active milestone/experiment.

## Core conclusion

Historical Saturn tooling can accelerate Thor 2 RE, but only as bounded corroborating evidence. Ancient-specific toolchain/library identity remains `UNKNOWN` until the game itself or a direct project artifact proves otherwise.
