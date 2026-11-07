#!/usr/bin/env python3
"""Confere a landing estática do Solano, inclusive sob o prefixo do GitHub Pages."""

from __future__ import annotations

import re
import sys
import threading
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))

from landing_http import DOCS, PREFIX, serve  # noqa: E402

ROOT = DOCS.parent
REPO_URL = "https://github.com/moonixt/HackBrasil-Solano"
PREDICTED_PAGES = "https://moonixt.github.io/HackBrasil-Solano/"
REQUIRED_IDS = {
    "topo",
    "conteudo",
    "problema",
    "solucao",
    "para-quem",
    "como-funciona",
    "regioes",
    "memoria",
    "estado",
    "repositorio",
    "problema-titulo",
    "solucao-titulo",
    "para-quem-titulo",
    "como-funciona-titulo",
    "regioes-titulo",
    "memoria-titulo",
    "estado-titulo",
    "repositorio-titulo",
}
REQUIRED_PHRASES = [
    "Solano",
    "Hack Brasil",
    "Telegram",
    "OpenStreetMap",
    "FastAPI",
    "Next.js",
    "pgvector",
    "Postgres",
    "WhatsApp",
    "nome e telefone",
    "Sul",
    "Sudeste",
    "Centro-Oeste",
    "Norte",
    "Nordeste",
    "Porto Alegre",
    "São Paulo",
    "Brasília",
    "Manaus",
    "Salvador",
    "proposta",
    "Não há bot público",
    REPO_URL,
]
BANNED = [
    "t.me/",
    "telegram.me",
    "wa.me",
    "api.whatsapp.com",
    "depoimento",
    "depoimentos",
    "parceiro",
    "parceiros",
    "usuários ativos",
    "usuarios ativos",
    "milhares",
    "já no ar",
    "ja no ar",
    "agente@chain",
]
REGION_CITIES = {
    "Sul": ["Porto Alegre", "Curitiba", "Florianópolis", "Pelotas", "Joinville"],
    "Sudeste": ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Campinas", "Vitória"],
    "Centro-Oeste": ["Brasília", "Goiânia", "Campo Grande", "Cuiabá", "Anápolis"],
    "Norte": ["Manaus", "Belém", "Porto Velho", "Boa Vista", "Macapá"],
    "Nordeste": ["Salvador", "Recife", "Fortaleza", "São Luís", "Natal"],
}


def lin(channel: float) -> float:
    value = channel / 255
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def contrast(foreground: str, background: str) -> float:
    def luminance(hex_color: str) -> float:
        color = hex_color.lstrip("#")
        red, green, blue = (int(color[i : i + 2], 16) for i in (0, 2, 4))
        return 0.2126 * lin(red) + 0.7152 * lin(green) + 0.0722 * lin(blue)

    hi, lo = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.attrs: list[tuple[str, str, str]] = []
        self.metas: list[dict[str, str]] = []
        self.lang = ""
        self.h1 = 0
        self.tags: list[str] = []
        self._in_title = False
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        self.tags.append(tag)
        if tag == "html":
            self.lang = values.get("lang", "")
        if tag == "h1":
            self.h1 += 1
        if tag == "meta":
            self.metas.append(values)
        if tag == "title":
            self._in_title = True
        if values.get("id"):
            self.ids.append(values["id"])
        for attr in ("href", "src"):
            if attr in values:
                self.attrs.append((tag, attr, values[attr]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)
        if self._in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return "".join(self.title_parts).strip()

    @property
    def text(self) -> str:
        return "".join(self.text_parts)


def fetch(url: str) -> tuple[int, str, bytes]:
    try:
        with urlopen(url, timeout=5) as response:
            body = response.read()
            ctype = response.headers.get("Content-Type", "")
            return response.status, ctype, body
    except HTTPError as error:
        return error.code, error.headers.get("Content-Type", ""), error.read()


def main() -> int:
    errors: list[str] = []

    def fail(message: str) -> None:
        errors.append(message)

    index_path = DOCS / "index.html"
    css_path = DOCS / "styles.css"
    if not index_path.is_file():
        fail("docs/index.html ausente")
        return report(errors)
    if not css_path.is_file():
        fail("docs/styles.css ausente")
    if not (DOCS / ".nojekyll").is_file():
        fail("docs/.nojekyll ausente — o Jekyll do Pages legado pode alterar o HTML")
    if not (DOCS / "404.html").is_file():
        fail("docs/404.html ausente")
    if not (DOCS / "favicon.svg").is_file():
        fail("docs/favicon.svg ausente")

    page = Page()
    raw_html = index_path.read_text(encoding="utf-8")
    page.feed(raw_html)

    if page.lang != "pt-BR":
        fail(f"html lang deve ser pt-BR, veio {page.lang!r}")
    if page.h1 != 1:
        fail(f"a página precisa de um único h1, veio {page.h1}")
    if "Solano" not in page.title or "Brasil" not in page.title:
        fail(f"title fraco ou ausente: {page.title!r}")
    if not any(meta.get("name") == "viewport" and "width=device-width" in meta.get("content", "") for meta in page.metas):
        fail("falta meta viewport")
    description = next((meta.get("content", "") for meta in page.metas if meta.get("name") == "description"), "")
    if len(description) < 40:
        fail("meta description ausente ou curta demais")
    for tag in ("header", "main", "footer", "nav"):
        if tag not in page.tags:
            fail(f"falta o elemento <{tag}>")
    if not any(tag == "a" and attr == "href" and value == "#conteudo" for tag, attr, value in page.attrs):
        fail("falta o atalho de pular para #conteudo")

    duplicate_ids = sorted({item for item in page.ids if page.ids.count(item) > 1})
    if duplicate_ids:
        fail(f"ids duplicados: {', '.join(duplicate_ids)}")
    missing_ids = sorted(REQUIRED_IDS - set(page.ids))
    if missing_ids:
        fail(f"ids obrigatórios ausentes: {', '.join(missing_ids)}")

    text = page.text
    folded = text.casefold()
    raw_folded = raw_html.casefold()
    for phrase in REQUIRED_PHRASES:
        if phrase.casefold() not in folded and phrase.casefold() not in raw_folded:
            fail(f"texto obrigatório ausente: {phrase}")
    for phrase in BANNED:
        if phrase.casefold() in raw_folded:
            fail(f"texto proibido encontrado: {phrase}")
    for region, cities in REGION_CITIES.items():
        for city in cities:
            if city not in text:
                fail(f"cidade de exemplo ausente ({region}): {city}")

    for tag, attr, value in page.attrs:
        if value.startswith("#"):
            anchor = value[1:]
            if anchor and anchor not in page.ids:
                fail(f"âncora sem destino: {value}")
            continue
        if value.startswith(REPO_URL):
            continue
        if value.startswith(("http://", "https://", "mailto:", "//")):
            fail(f"link externo fora do repositório: {value}")
            continue
        if value.startswith("/"):
            fail(f"caminho absoluto quebra o subdiretório do Pages: {attr}={value}")
            continue
        target = (DOCS / value.split("?", 1)[0].split("#", 1)[0]).resolve()
        try:
            target.relative_to(DOCS.resolve())
        except ValueError:
            fail(f"caminho local escapa de docs/: {value}")
            continue
        if not target.is_file():
            fail(f"arquivo local ausente: {value}")

    css = css_path.read_text(encoding="utf-8")
    variables = dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})\s*;", css))
    expected = {
        "paper": "#f3ecdf",
        "ink": "#1c1916",
        "soft": "#3f3a34",
        "muted": "#5c564e",
        "card": "#fbf7f0",
        "green": "#1c4536",
        "green-deep": "#10281f",
        "cream": "#f7f1e6",
        "blue": "#1d4e89",
        "gold-ink": "#6e5016",
    }
    for name, hex_color in expected.items():
        if variables.get(name, "").lower() != hex_color:
            fail(f"variável --{name} deveria ser {hex_color}, veio {variables.get(name)!r}")

    pairs = [
        ("ink", "paper", 7),
        ("soft", "paper", 7),
        ("muted", "paper", 4.5),
        ("ink", "card", 7),
        ("muted", "card", 4.5),
        ("cream", "green", 7),
        ("cream", "green-deep", 7),
        ("blue", "paper", 4.5),
        ("gold-ink", "paper", 4.5),
        ("gold-ink", "card", 4.5),
    ]
    for foreground, background, minimum in pairs:
        if foreground not in variables or background not in variables:
            continue
        ratio = contrast(variables[foreground], variables[background])
        if ratio < minimum:
            fail(
                f"contraste {foreground} sobre {background} = {ratio:.2f}, mínimo {minimum}"
            )

    for needle in (
        "background: var(--paper)",
        "color: var(--ink)",
        "background: var(--green)",
        "color: var(--cream)",
        ":focus-visible",
        "prefers-reduced-motion",
        "forced-colors",
        "min-height: 44px",
        "min-height: 48px",
        ".prose a.button",
        ".site-footer .wordmark",
    ):
        if needle not in css:
            fail(f"CSS sem regra esperada: {needle}")

    for url in re.findall(r"url\(([^)]+)\)", css):
        cleaned = url.strip().strip("'\"")
        if cleaned.startswith(("data:", "http://", "https://")):
            fail(f"CSS não deve depender de URL externa: {cleaned}")
            continue
        if cleaned.startswith("/"):
            fail(f"url() absoluta quebra o subdiretório do Pages: {cleaned}")
            continue
        asset = (css_path.parent / cleaned).resolve()
        try:
            asset.relative_to(DOCS.resolve())
        except ValueError:
            fail(f"url() escapa de docs/: {cleaned}")
            continue
        if not asset.is_file():
            fail(f"fonte ou asset do CSS ausente: {cleaned}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for phrase in (
        "docs/index.html",
        PREDICTED_PAGES,
        "previsão",
        "python3 scripts/check_landing.py",
        "python3 scripts/preview_landing.py",
        "dev/moonixt",
        "/docs",
    ):
        if phrase not in readme:
            fail(f"README sem a orientação de publicação: {phrase}")
    if re.search(r"página está no ar|site está publicado|já publicada em https://moonixt.github.io", readme, re.I):
        fail("README afirma publicação que este teste não pode garantir")

    not_found = Page()
    not_found.feed((DOCS / "404.html").read_text(encoding="utf-8"))
    if not_found.lang != "pt-BR" or not_found.h1 != 1:
        fail("404.html precisa de lang pt-BR e um h1")
    if "Solano" not in not_found.title:
        fail("404.html sem Solano no title")

    server = serve("127.0.0.1", 0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{port}{PREFIX}/"
        status, ctype, body = fetch(base)
        if status != 200 or "text/html" not in ctype:
            fail(f"GET {PREFIX}/ deveria ser HTML 200, veio {status} {ctype}")
        if b"<title>Solano" not in body:
            fail("HTML servido no prefixo não contém o title do Solano")

        file_base = f"http://127.0.0.1:{port}{PREFIX}/index.html"
        for start in (base, file_base):
            status, _, html_body = fetch(start)
            if status != 200:
                fail(f"GET {start} veio {status}")
                continue
            served = Page()
            served.feed(html_body.decode("utf-8"))
            for tag, attr, value in served.attrs:
                if value.startswith(("#", "mailto:", "http://", "https://", "//")):
                    continue
                absolute = urljoin(start, value)
                asset_status, _, _ = fetch(absolute)
                if asset_status != 200:
                    fail(f"{attr} {value!r} a partir de {start} resolve para {absolute} ({asset_status})")
                if not absolute.startswith(base):
                    fail(f"{value!r} escapou do prefixo {PREFIX}: {absolute}")

        status, ctype, css_body = fetch(base + "styles.css")
        if status != 200 or "--paper" not in css_body.decode("utf-8"):
            fail("styles.css não está disponível sob o prefixo")
        root_status, _, _ = fetch(f"http://127.0.0.1:{port}/styles.css")
        if root_status == 200:
            fail("styles.css respondeu na raiz do host; o teste deixaria passar um path absoluto")

        for font in (
            "fonts/fraunces.woff2",
            "fonts/fraunces-italic.woff2",
            "fonts/atkinson-400.woff2",
            "fonts/atkinson-700.woff2",
            "fonts/atkinson-400i.woff2",
        ):
            status, font_type, font_body = fetch(base + font)
            if status != 200 or not font_body.startswith(b"wOF2"):
                fail(f"fonte inválida sob o prefixo: {font} ({status}, {font_type})")

        status, _, missing = fetch(base + "caminho-que-nao-existe")
        if status != 404 or "não existe".encode() not in missing and b"nao existe" not in missing.lower():
            fail(f"404 da landing inesperado: status {status}")

        status, _, escaped = fetch(base + "../README.md")
        if status == 200 and b"HackBrasil Solano" in escaped:
            fail("o servidor de preview vazou o README fora de docs/")
    except URLError as error:
        fail(f"falha ao servir a landing local: {error}")
    finally:
        server.shutdown()
        server.server_close()

    return report(errors)


def report(errors: list[str]) -> int:
    if errors:
        print(f"{len(errors)} problema(s) na landing:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Landing OK: título, seções, links, contraste e prefixo /HackBrasil-Solano/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
