#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$(cd "${1:?source checkout required}" && pwd)"
PIN=831fae740de35a106e85768d8b0534b4af422b13
[[ "$(uname -s)" == Darwin && "$(uname -m)" == arm64 ]]
[[ "$(git -C "$SOURCE" rev-parse HEAD)" == "$PIN" ]]
[[ -z "$(git -C "$SOURCE" status --porcelain)" ]]
for tool in swift cmake python3 xcrun xcodebuild otool install_name_tool codesign lipo; do command -v "$tool" >/dev/null; done
[[ "$(xcode-select -p)" == */Xcode*.app/Contents/Developer ]]
swift --version | python3 -c 'import re,sys; m=re.search(r"Swift version ([0-9]+)[.]([0-9]+)",sys.stdin.read()); assert m and tuple(map(int,m.groups())) >= (6,3), "Swift >=6.3 required"'
xcrun -sdk macosx metal -v
export MACOSX_DEPLOYMENT_TARGET=26.2
export MLXFAST_BUILD_JOBS=3
cd "$SOURCE"
swift build -c release --force-resolved-versions --scratch-path .build-worker --jobs 3 --product bench-worker
PRODUCTS="$(swift build -c release --force-resolved-versions --scratch-path .build-worker --show-bin-path)"
export MLXFAST_MLX_METALLIB="$PRODUCTS/mlx.metallib"
bash tools/build-mlx-metallib.sh
git diff --exit-code -- Package.swift Package.resolved Vendor
mkdir -p "$ROOT/dist"
python3 "$ROOT/scripts/package.py" "$SOURCE" "$PRODUCTS" "$ROOT/dist/bonsai-worker" "$ROOT"
# Remove original build path from reach without deleting artifacts. A plain help
# check validates dyld relocation only, NOT Metal/GPU/model loading.
mv "$SOURCE/.build-worker" "$SOURCE/.build-worker-hidden"
trap 'mv "$SOURCE/.build-worker-hidden" "$SOURCE/.build-worker"' EXIT
(cd / && "$ROOT/dist/bonsai-worker/bench-worker" --help)
(cd "$ROOT/dist/bonsai-worker" && shasum -a 256 -c SHA256SUMS)
cd "$ROOT/dist"
tar -czf bonsai-worker-macos-arm64.tar.gz bonsai-worker
shasum -a 256 bonsai-worker-macos-arm64.tar.gz > bonsai-worker-macos-arm64.tar.gz.sha256
