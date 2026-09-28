# Optimized Bonsai worker: launch on approved work Mac

This is the ORIGINAL competition DFlash engine, not benchd and not serial mlx-server. Interface is raw token IDs/NDJSON, NOT a chat application. No model weights included. Intended M4 Pro macOS27; GPU operation untested. No Xcode needed by the intended packaged runtime, but that must be confirmed on the real target.

Archive is ad-hoc signed, NOT Developer-ID signed/notarized. Respect employer/MDM policy; if blocked ask IT. Do not disable Gatekeeper or bypass quarantine/work restrictions.

Verify external archive checksum, extract, then verify payload:

    shasum -a 256 -c bonsai-worker-macos-arm64.tar.gz.sha256
    tar -xzf bonsai-worker-macos-arm64.tar.gz
    cd bonsai-worker
    shasum -a 256 -c SHA256SUMS
    ./bench-worker --help

Keep executable, mlx.metallib, bundles and lib directory together. Model setup is separate and subject to its license and employer permission. Target pack is prism-ml/Ternary-Bonsai-2-27B-mlx-2bit at 3f926b415992eaa2ae9dd7b573706494d6bbf787; DFlash artifact z-lab/Qwen3.8-27B-DFlash2 at 50307d4c4cde6860d4eee73e2547cd786fe8e8a4. Use matching complete local exports (including tokenizer/config) and upstream manifests; not arbitrary GGUF/requantization. Neither CI nor launcher downloads these. Target ~8GB plus drafter ~3.85GB files does not equal peak runtime RAM; long contexts need more.

Source-derived protocol demonstration (token 1 is a numeric example, NOT a meaningful chat prompt):

    TARGET=/absolute/path/to/target-checkpoint
    DRAFTER=/absolute/path/to/dflash-checkpoint
    test -d "$TARGET" && test -d "$DRAFTER" || exit 1
    printf '%s\n' \
      '{"id":1,"kind":"free_decode_begin","seed_tokens":[1],"spec":{"mode":"dflash","dflash":{"depth":15}}}' \
      '{"id":2,"kind":"free_decode_run","count":16}' \
      | ./bench-worker runtime-worker --weights "$TARGET" --drafter "$DRAFTER" --speculative-protocol v1.1

The worker first emits hello. Check response id1 ok and effective_spec (dflash, depth15); preserve its seed_token as the FIRST generated token. Response id2 supplies subsequent tokens and speculative audit data. Production clients should await/check each response rather than blindly sending both; stop on errors. Replace [1] with IDs encoded using the target's exact tokenizer/chat template. Decode seed_token plus returned tokens with that same tokenizer. The upstream benchmark free-run deliberately disables EOS stopping and requests an exact count; it is greedy single-stream benchmark semantics, not normal chat sampling. Do not interpret arbitrary IDs as text or claim all 16 tokens are natural completion length.

Schema evidence: MLXRunners/BenchWorkerWire.swift (WorkerRequest, SpecConfig) and BenchWorker.swift (freeDecodeBegin/freeDecodeRun); accepted mtp-head.manifest.json selects DFlash depth15. The manifest file alone does not turn on drafting: pass the protocol flag, drafter and explicit request spec as above.

M4 takes ordinary kernels when NAX unavailable; M5 scores do not promise M4 throughput. Real target tests must check no-Xcode cold start, Metal load/JIT, tokenizer fidelity, DFlash activation, RAM and token outputs before relying on this build.

## Minimal text adapter proposal (not implemented)

Reuse the pinned swift-transformers Tokenizers package and existing MLXHuggingFace tokenizer loader. MLXRunners/RunnerLoading.swift already loads a local ModelContext and context.tokenizer; avoid separately loading model weights just to tokenize. A small Swift executable could load ONLY local tokenizer assets, apply exact chat template, encode input, spawn the unchanged worker with pipes, validate hello/effective_spec/errors, decode the initial seed_token plus subsequent tokens and enforce client-side EOS/display policy. No new model math/engine or serial replacement is necessary. This is separate optional frontend work, not required to package the authorized raw worker.
