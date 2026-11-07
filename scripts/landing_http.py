"""Serve a pasta docs/ sob o prefixo de projeto do GitHub Pages."""

from __future__ import annotations

import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PREFIX = "/HackBrasil-Solano"

EXTRA_TYPES = {
    ".woff2": "font/woff2",
    ".svg": "image/svg+xml",
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}


def resolve_under_docs(url_path: str) -> tuple[Path | None, int]:
    """Mapeia um caminho de URL para um arquivo em docs/.

    Retorna (arquivo, status). Status 200 é o arquivo pedido. Status 404 pode
    apontar para docs/404.html. Caminhos fora do prefixo ou com `..` não saem
    de docs/.
    """
    path = url_path.split("?", 1)[0]
    if path != PREFIX and not path.startswith(PREFIX + "/"):
        return None, 404

    rel = path[len(PREFIX) :].lstrip("/")
    if rel == "":
        rel = "index.html"

    if any(part == ".." for part in Path(rel).parts):
        return None, 403

    docs_root = DOCS.resolve()
    candidate = (DOCS / rel).resolve()
    try:
        candidate.relative_to(docs_root)
    except ValueError:
        return None, 403

    if candidate.is_dir():
        candidate = candidate / "index.html"
    if candidate.is_file():
        return candidate, 200

    fallback = docs_root / "404.html"
    if fallback.is_file():
        return fallback, 404
    return None, 404


def content_type(path: Path) -> str:
    if path.suffix in EXTRA_TYPES:
        return EXTRA_TYPES[path.suffix]
    guessed = mimetypes.guess_type(path.name)[0]
    return guessed or "application/octet-stream"


class LandingHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._respond(include_body=True)

    def do_HEAD(self) -> None:
        self._respond(include_body=False)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _respond(self, include_body: bool) -> None:
        file, status = resolve_under_docs(self.path)
        if file is None:
            body = b"Nao encontrado\n"
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if include_body:
                self.wfile.write(body)
            return

        data = file.read_bytes()
        self.send_response(status)
        self.send_header("Content-Type", content_type(file))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if include_body:
            self.wfile.write(data)


def serve(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), LandingHandler)
