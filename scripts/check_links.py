#!/usr/bin/env python3
"""Validate local href/src targets and in-page anchors in the static academy."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for attr in ("href", "src"):
            value = attrs.get(attr)
            if value:
                self.links.append(value)


def read_page(path):
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


errors = []
pages = sorted(ROOT.rglob("*.html"))
parsers = {page: read_page(page) for page in pages}

for page, parser in parsers.items():
    for raw in parser.links:
        url = urlsplit(raw)
        if url.scheme or url.netloc or raw.startswith("//"):
            continue
        relative = unquote(url.path)
        target = (page.parent / relative).resolve() if relative else page.resolve()
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            errors.append(f"{page.relative_to(ROOT)}: missing target {raw}")
            continue
        if url.fragment and target.suffix.lower() == ".html":
            target_parser = parsers.get(target)
            if target_parser is None:
                target_parser = read_page(target)
            if unquote(url.fragment) not in target_parser.ids:
                errors.append(f"{page.relative_to(ROOT)}: missing anchor {raw}")

if errors:
    print("Local link check failed:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print(f"Local link check passed: {len(pages)} HTML pages checked.")
