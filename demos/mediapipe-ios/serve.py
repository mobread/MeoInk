#!/usr/bin/env python3
"""Static server for Pocket Vision Lab.

Python's http.server does not know about .wasm or .mjs, and a wrong
Content-Type makes the browser refuse to compile the module or the WebAssembly
binary. This sets them correctly and adds no-transform so a proxy cannot
re-encode the model weights.

    ./serve.py [--port 8099] [--host 0.0.0.0]

For a phone you need HTTPS from a real certificate -- see README.md. This
server speaks plain HTTP and is meant to sit behind a TLS terminator.
"""
import argparse
import functools
import http.server
import socketserver

EXTRA_TYPES = {
    ".wasm": "application/wasm",
    ".mjs": "text/javascript",
    ".task": "application/octet-stream",
}


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, **EXTRA_TYPES}

    def end_headers(self):
        self.send_header("Cache-Control", "public, max-age=3600, no-transform")
        # Uncomment to enable cross-origin isolation (SharedArrayBuffer ->
        # multi-threaded inference). It also blocks the Google Fonts
        # stylesheet unless you self-host the fonts.
        # self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        # self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--host", default="0.0.0.0")
    args = ap.parse_args()

    import os
    handler = functools.partial(Handler, directory=os.path.dirname(os.path.abspath(__file__)))
    with Server((args.host, args.port), handler) as httpd:
        print("Pocket Vision Lab on http://%s:%d/" % (args.host, args.port))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
