#!/usr/bin/env python3
"""Abre a landing no mesmo prefixo do GitHub Pages: /HackBrasil-Solano/."""

from __future__ import annotations

import argparse

from landing_http import serve


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = serve(args.host, args.port)
    url = f"http://{args.host}:{args.port}/HackBrasil-Solano/"
    print(f"Landing em {url}")
    print("Ctrl+C encerra.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
