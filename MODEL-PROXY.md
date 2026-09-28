# Small LAN model proxy

One Python file, no dependencies, no model cache, starts immediately. The host needs Python 3.9+ and Internet access to Hugging Face. Windows: use `py -3` instead of `python3`. No Python or Xcode is needed on the Mac: it uses its built-in curl and shasum.

Download [model-proxy.py](https://raw.githubusercontent.com/Matt2111/bonsai-q2-27b-macos-mlx-fast-build/main/model-proxy.py) onto the serving computer. Replace the example address with **that computer's LAN IPv4 address** (network settings):

    python3 model-proxy.py --bind 192.168.1.50

Then paste the download/checksum command block it prints into Terminal on the Mac. It fetches the complete target and DFlash directories automatically through this computer, and checks SHA256. Wait for **every file to report OK**; do not launch incomplete/failed files. Re-run failed curl commands to resume. If the upstream ignores Range, curl refuses unsafe resume: delete only that incomplete file and retry. Downloads are direct to their filenames, not atomic; only use after verification. A checksum failure requires deleting/re-downloading the affected file.

Mac disk needed: **12.46 GB** plus free-space margin. Host disk: only this script. Network traffic: ~12.46 GB Internet into host and LAN into Mac. It does not compress or duplicate/archive the models. Keep the host running and awake; Ctrl+C stops. A restart generates a new URL/token, so use the newly printed commands.

Output relative to the Mac's starting folder:

- `bonsai-models/target-checkpoint`
- `bonsai-models/dflash-checkpoint`

Use their absolute paths for TARGET and DRAFTER in [LAUNCH.md](LAUNCH.md). This downloads models only, not a chat app or runtime.

## Boundaries

Both devices must be on the same reachable trusted LAN. Guest Wi-Fi/client isolation, corporate firewall or VPN routing can prevent access. This is not an Internet tunnel; no router forwarding/firewall changes are made. Respect employer/IT policy. No connection from outside your LAN is provided; do not publish/forward the port. HTTP is unencrypted; the random URL is a capability, not TLS. Keep it private. Default bind is localhost only; 0.0.0.0 is rejected.

Only 24 exact pinned file routes can be fetched (19 target + 3 draft + 2 target license files). No directory listing, local filesystem serving, arbitrary URL forwarding, uploads, model-code execution or credentials. GET, HEAD and single Range requests stream with 1 MiB buffers; redirects from Hugging Face are followed server-side. Download integrity is checked on the Mac, not before streaming. Intended for a few trusted LAN clients, not a hardened public server.

Pins and sizes/hashes come from upstream fixtures and were checked against pinned HF trees; small files were downloaded and hashed. Large weights were **not** downloaded for testing; their published LFS SHA256 was checked against the upstream manifests. [model-manifest.json](model-manifest.json) is a readable inventory, not required to run the script. Target LICENSE and runtime/LICENSE are included. The drafter has no standalone LICENSE at this revision; its pinned README carries its license metadata. Review model terms before use.

Loopback mock tests cover GET, HEAD, Range, redirect, invalid ranges, wrong token, traversal/arbitrary route denial and POST rejection. No full model download or real Mac/LAN runtime test was performed.
