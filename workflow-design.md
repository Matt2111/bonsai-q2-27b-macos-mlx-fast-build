# Prepared workflow

.github/workflows/build.yml is now runnable preparation for the authorized ORIGINAL bench-worker. Manual workflow_dispatch only; public-repo guard before runner allocation; contents:read; checkout credentials not persisted; source/action SHA pins; standard macos-26 arm64; 60-minute timeout; no installs/model loads; exact archive/checksum artifact allowlist. Published for manual execution; consult Actions for actual results.

Build preflight requires existing Swift>=6.3/full Xcode/Metal/CMake/Python. Fail closed if absent. Script builds root dependency product with frozen Package.resolved, then matching upstream Metal library, packages bundles/licenses/source and recursively relocates/audits dylibs, signs ad-hoc, tests relocated --help with original build directory hidden, checks hashes and archives. No stock MLX or serial-server replacement.

Mac build is untested. Unknown dynamic dependencies fail rather than yielding a misleading portable archive. Real target still needs model/GPU/no-Xcode tests and employer approval. Optional thin tokenizer adapter is described in LAUNCH.md, not implemented.
