# Bonsai optimized worker — pinned macOS ARM64 build

Inspected 2026-09-28. Published for an authorized GitHub Actions build. No installations or model downloads. Intended target: WORK M4 Pro / macOS27, without Xcode; current Linux/home machine is not the target. Upstream checkout unchanged.

## Crucial entrypoint distinction

- Root mlxfast-swift: transform/verification utility, NOT inference.
- Vendored bench-worker: REAL optimized inference engine, not benchd. MLXRunners/Qwen35Runner loads target and DFlash. Engine Protocol v1.1 NDJSON/token-ID operations include free_decode_begin/free_decode_run. It is a developer endpoint, not a text/chat CLI.
- Vendored mlx-server: REAL OpenAI-compatible text server, but explicitly uses SERIAL ModelContainer, NOT ContinuousBatchingV2/MLXRunners where competition DFlash is activated. No --drafter/DFlash CLI option. Packaging it alone loses the requested competition speculative decoding. Evidence: Vendor/mlx-swift-lm/Libraries/MLXLMServer/CLI/MLXServerRunner.swift and Runtime/MLXModelContainerEngine.swift lines 9–12, versus MLXRunners/Qwen35Runner.swift.

The original optimized raw worker is now the authorized product. Runnable .github/workflows/build.yml and scripts/build.sh + scripts/package.py are prepared. LAUNCH.md documents its real protocol and optional future tokenizer frontend. No serial substitution or new inference engine. Workflow is manual/public-only; see the Actions tab for actual build status.

## Source provenance

Pinned **831fae740de35a106e85768d8b0534b4af422b13**.

https://github.com/Layr-Labs/mlxfast-bonsai2-27b-engine/commit/831fae740de35a106e85768d8b0534b4af422b13

“Accept submission f22fbffb-4a09-43e9-b091-f9524a9e530a”, 2026-09-27 17:42:50 UTC, yukon-autoresearch bot. accepted-commit.txt records this.

https://www.yukon.org/ embeds challenge metadata in Next.js hydration: id 9d563dbc-5f17-4636-9476-04dd6a24a6ad, name davidtai/mlxfast-bonsai2-27b, sourceRef matches pin, updated 2026-09-27T17:42:56.548Z. Status PAUSED. Narrow extract: provenance.json, tested extractor extract-provenance.py. This corroborates challenge-current accepted source, NOT an independently captured leaderboard row/score. Exact leaderboard row remains outstanding.

https://api.github.com/repos/Layr-Labs/mlxfast-bonsai2-27b-engine/releases returned []: no upstream release binary found. tools/fetch-benchd.sh distributes measurement harness, not inference engine. No suitable ready-made DFlash application identified.

## Runner and Xcode

https://docs.github.com/en/actions/reference/runners/github-hosted-runners lists **macos-26** as standard **arm64**. Public repositories get free/unlimited standard hosted runners. Private repos use allowance then bill; none authorized. Personal account != private repo. This repository is public and publication/build is authorized. No -large/-xlarge.

https://github.com/actions/runner-images/blob/main/images/macos/macos-26-arm64-Readme.md lists macOS26.6.2, full Xcode26.6 default. Upstream CI uses macos-26; manifests require Swift>=6.3. Verify actual moving runner toolchain. Preflight xcrun -sdk macosx metal -v; fail clearly if separate Metal component absent. No automatic installs. Full Xcode needed on BUILD host, not necessarily target. DO NOT run upstream setup.sh (downloads models/tools).

## M4 compatibility

MLX device.cpp:is_nax_available() checks macOS>=26.2 AND GPU architecture generation>=17 (>=18 for suffix p). quantized.cpp:qmm_dispatch and matmul.cpp use ordinary kernels otherwise. M4 does not gain M5 NAX by upgrading OS. Retain both paths/all accepted source edits; no stock MLX substitution. Competition M5 performance is not promised on M4.

Build success != GPU compatibility. Standard hosted VM build/help cannot certify M4 GPU execution. Manifest floor macOS14 is not proof every compiled Metal path works on all OS releases. Align deployment/Metal targets deliberately (>=26.2 for this target), inspect Mach-O requirements; actual macOS27/M4 validation remains necessary.

## Packaging design after entrypoint decision

1. Exact SHA/root Package.resolved frozen; root path dependencies preserve vendored MLX edits.
2. Root command: swift build -c release --force-resolved-versions --scratch-path .build-worker --product bench-worker (mlx-server only if serial mode explicitly accepted).
3. Inspected tools/build-mlx-metallib.sh builds matching AOT library. Set MLXFAST_MLX_METALLIB to product directory; retain .fingerprint. Preserve runtime-effective mlx-generated sources. No setup/benchmark/model-fetch scripts.
4. Bundle executable, colocated mlx.metallib, required SwiftPM .bundle resources including pagedattention.metal, recursive non-system dylibs, dependency/vendored licenses and THIRD_PARTY_NOTICES. device.cpp lines214+ search colocated library first.
5. Recursive otool -L audit; relocate non-system dylibs/rpaths to packaged @loader_path paths, ad-hoc re-sign changed files if needed. Reject leftover /Users/runner, /opt/homebrew, .build, Xcode dylib references. Do not copy OS frameworks/libSystem. Audit Swift runtime requirements.
6. Include source SHA, Package.resolved, compiler/SDK/deployment metadata, Metal fingerprint, launch instructions and complete license tree. SHA256SUMS for every payload file; tar.gz and external SHA256. No .git/private workspace files.
7. Relocated --help smoke test with original build paths unavailable, no model loads. Actual no-Xcode cold launch, text+DFlash, fidelity, memory, and M4 fallback need device validation.

Existing SERIAL syntax only if approved: ./mlx-server --model /absolute/local/checkpoint --host 127.0.0.1 --port 8080. Missing directories become Hub IDs; wrapper must reject nonexistent paths to avoid unintended downloads. No DFlash text CLI is invented.

## Work Mac security

A no-certificate artifact is unsigned or ad-hoc signed, NOT Developer-ID signed/notarized. Gatekeeper or employer MDM may block it. Do not disable Gatekeeper globally, strip quarantine to evade policy, or bypass work restrictions. Use only an employer-approved application approval/signing route; otherwise stop and ask IT. No signing credentials collected and no notarization promised.

## Validation / blockers

Read manifests, CLI/server/runner, Metal builder/dispatch, official docs; source SHA clean. Public metadata extractor tested with Python standard library. No Swift/Mac/Metal compile, package or GPU test. No release checksum exists; PREPARATION_SHA256SUMS covers docs only.

Outstanding: exact leaderboard row, successful Actions build/resources/dylib audit, real M4/macOS27 test and work-policy approval. See workflow-design.md and PUBLISH_ALLOWLIST.txt. No executable exists yet. Python compilation, bash syntax and YAML parse/pin/trigger/runner assertions passed locally; this is not a Mac compile. Never publish workspace/nested .git.
