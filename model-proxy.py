#!/usr/bin/env python3
"""Pinned Bonsai LAN streaming proxy. Python 3.9+, no dependencies."""
import argparse
import http.server
import ipaddress
import re
import secrets
import socketserver
import urllib.error
import urllib.request

MODELS = [{'directory': 'target-checkpoint',
  'files': [{'path': 'NOTICE.txt',
             'sha256': 'de0e0c48fb6f691a31e74f338e3ccf93f9ecdfe2866ab769c4bf8b79a7636a30',
             'size': 411},
            {'path': 'PACK-RUNTIME.md',
             'sha256': '486bf73b40dab072792cb2e48961a3698d4ca599f1355f3e628e4c64d8aa4cce',
             'size': 969},
            {'path': 'README.md',
             'sha256': '187aca6e2e8d01daa77e6faf64189ba015a5616f1627fdf2f4f2392d592bf5da',
             'size': 22732},
            {'path': 'chat_template.jinja',
             'sha256': 'c3cf9e34abf4f9e36c2d72165aa9c132d3e2a725b6c2586aaa3a8af9d7a81041',
             'size': 8952},
            {'path': 'config.json',
             'sha256': '238de7c512cc56a733421e3fd011d88f8260739e3d00e32c5d65b7943cc9f837',
             'size': 58145},
            {'path': 'files.json',
             'sha256': 'e9c78caf0915d7db3a368930d3f1c02d0c5ef3a5e6a98dffad4fb7677d7042bc',
             'size': 2855},
            {'path': 'generation_config.json',
             'sha256': 'cddd0dbd24dbf13229f872b4100c5a0bfe5186eeb09e171b2fc2bac701e98034',
             'size': 85},
            {'path': 'hadamard.json',
             'sha256': '7132a3ec364f0bdac1f08f905f24f0ad2f14245060f592637a0396826d3b5fe6',
             'size': 297903},
            {'path': 'model.safetensors',
             'sha256': '130de5925082c168b7866b2e91b52e44abbafc99017e3ca352b77b5b55a269ed',
             'size': 8595477990},
            {'path': 'preprocessor_config.json',
             'sha256': '27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516',
             'size': 390},
            {'path': 'reload-validation.json',
             'sha256': '41ec215fe19fa8ad59527fca6594a782d1b7f23b69948ef063311c768217788e',
             'size': 86},
            {'path': 'runtime/artifact.py',
             'sha256': '5279718d7671bd799e866f53099e82b0260117fec811f83011ba47a0abc7943e',
             'size': 5621},
            {'path': 'runtime/codec.py',
             'sha256': '7f7fd67637a7d9363eab8ebf7db59771830b690330ffef772379a0169ddb9608',
             'size': 2572},
            {'path': 'runtime/requirements.txt',
             'sha256': '358bc104a02ea598f1e6cde8e7eeed169b9ec34f69f3543b47b390706446a1e0',
             'size': 115},
            {'path': 'runtime/runtime.py',
             'sha256': '30ad3905775040a8167360a009168b9ede1436cb02dc43e9e743432482eafbbf',
             'size': 10674},
            {'path': 'runtime/vision_artifact.py',
             'sha256': '624e78d1fc7a0ddbaa637121ee823209c525b8e89f35fbc68d6d2f3f3fcfd87d',
             'size': 4221},
            {'path': 'tokenizer-validation.json',
             'sha256': 'b36f33d09bd3de3e19de3fd2cf493a69ec0a5e24acf648b0c9fba120d9357554',
             'size': 63},
            {'path': 'tokenizer.json',
             'sha256': '0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3',
             'size': 12809320},
            {'path': 'tokenizer_config.json',
             'sha256': 'b11349aafa7cdc6a320767cf7ceb29ed82f7eda5d65e8e0819e76f0ce947bf27',
             'size': 17928},
            {'path': 'LICENSE',
             'sha256': '69849221bfb90053de2134ef5e6d540287b4b98062326492f1f96f5da685524b',
             'size': 10174},
            {'path': 'runtime/LICENSE',
             'sha256': 'ccfab7ccb2ea306f71531c8ca77bb55507606cd90768b1e32b8b52ab5b48cf01',
             'size': 1066}],
  'repository': 'prism-ml/Ternary-Bonsai-2-27B-mlx-2bit',
  'revision': '3f926b415992eaa2ae9dd7b573706494d6bbf787'},
 {'directory': 'dflash-checkpoint',
  'files': [{'path': 'README.md',
             'sha256': '0c06405ffff835f4da26115114a6dd7bb4a8b8a6881c17edd3a1086a99281269',
             'size': 5397},
            {'path': 'config.json',
             'sha256': '873e3556509b0da06e29654ba00d4944888d4b5e8a33afde25f7eb27d321e980',
             'size': 1239},
            {'path': 'model.safetensors',
             'sha256': '67fc76d68dc5a9415511a4f394ef744d67510cd20e93b37cc2cc7d28e4bab65c',
             'size': 3848817896}],
  'repository': 'z-lab/Qwen3.8-27B-DFlash2',
  'revision': '50307d4c4cde6860d4eee73e2547cd786fe8e8a4'}]
URLS = {m["directory"] + "/" + f["path"]:
        "https://huggingface.co/" + m["repository"] + "/resolve/" + m["revision"] + "/" + f["path"]
        for m in MODELS for f in m["files"]}


def handler_for(token, urls=URLS):
    class Handler(http.server.BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(60)

        def log_message(self, *args):
            pass  # Never log capability URLs.

        def do_GET(self):
            self.forward()

        def do_HEAD(self):
            self.forward()

        def forward(self):
            prefix = "/" + token + "/"
            key = self.path[len(prefix):] if self.path.startswith(prefix) else ""
            if key not in urls:
                self.send_error(404)
                return
            headers = {"Accept-Encoding": "identity", "User-Agent": "bonsai-lan-proxy/1"}
            value = self.headers.get("Range")
            if value:
                if not re.fullmatch(r"bytes=([0-9]+-[0-9]*|-[0-9]+)", value):
                    self.send_error(400, "Only single byte ranges supported")
                    return
                headers["Range"] = value
            sent = False
            try:
                req = urllib.request.Request(urls[key], headers=headers, method=self.command)
                # urllib follows HF redirects. No client cookies/auth headers forwarded.
                with urllib.request.urlopen(req, timeout=60) as upstream:
                    if upstream.status not in (200, 206):
                        self.send_error(502)
                        return
                    self.send_response(upstream.status)
                    for name in ("Content-Length", "Content-Range", "Accept-Ranges", "ETag", "Last-Modified"):
                        if name in upstream.headers:
                            self.send_header(name, upstream.headers[name])
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    sent = True
                    if self.command == "GET":
                        while True:
                            block = upstream.read(1024 * 1024)
                            if not block:
                                break
                            self.wfile.write(block)
            except urllib.error.HTTPError as error:
                if not sent:
                    self.send_response(error.code if error.code in (403, 404, 416, 429) else 502)
                    for name in ("Content-Range", "Retry-After"):
                        if name in error.headers:
                            self.send_header(name, error.headers[name])
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                error.close()
            except (OSError, ValueError):
                if not sent:
                    self.send_error(502, "Upstream unavailable; retry")
                self.close_connection = True
    return Handler


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", default="127.0.0.1", help="Explicit LAN IPv4; default loopback only")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    ip = ipaddress.IPv4Address(args.bind)
    if not (ip.is_private or ip.is_loopback) or ip.is_unspecified or ip.is_multicast:
        parser.error("Use one explicit LAN IPv4, not 0.0.0.0 or a public address")
    if not 1 <= args.port <= 65535:
        parser.error("Port must be 1..65535")
    token = secrets.token_urlsafe(24)
    server = Server((args.bind, args.port), handler_for(token))
    base = "http://%s:%d/%s" % (args.bind, args.port, token)
    print("Ready immediately; no model cache or predownload. Stop with Ctrl+C.", flush=True)
    print("Trusted LAN only (unencrypted HTTP). Base URL: " + base, flush=True)
    print("Paste these commands into Terminal on the Mac (curl required):", flush=True)
    print("mkdir -p bonsai-models && cd bonsai-models", flush=True)
    for model in MODELS:
        for entry in model["files"]:
            key = model["directory"] + "/" + entry["path"]
            print("mkdir -p '" + key.rsplit("/", 1)[0] + "' && curl --fail --location --retry 3 -C - -o '" + key + "' '" + base + "/" + key + "'", flush=True)
    print("shasum -a 256 -c <<'BONSAI_SHA256'", flush=True)
    for model in MODELS:
        for entry in model["files"]:
            print(entry["sha256"] + "  " + model["directory"] + "/" + entry["path"], flush=True)
    print("BONSAI_SHA256", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
