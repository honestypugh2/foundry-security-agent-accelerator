"""Offline contracts for the participant technical portal."""

import re
from html.parser import HTMLParser
from pathlib import Path

PORTAL = Path(__file__).resolve().parents[1] / "docs" / "index.html"


class Document(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[str] = []
        self.assets: list[str] = []
        self.controls: list[dict[str, str | None]] = []
        self.feed(source)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.append(str(attributes["id"]))
        if tag == "a" and attributes.get("href"):
            self.links.append(str(attributes["href"]))
        if tag in {"script", "img", "iframe", "link"}:
            asset = attributes.get("src") or attributes.get("href")
            if asset:
                self.assets.append(asset)
        if attributes.get("role") == "button":
            self.controls.append(attributes)


def test_offline_portal_has_unique_resolvable_anchors() -> None:
    source = PORTAL.read_text()
    document = Document(source)
    assert len(document.ids) == len(set(document.ids))
    assert not document.assets, "The portal must not fetch external assets"
    assert "https://" not in "".join(re.findall(r"fetch\([^)]*\)", source))
    for href in document.links:
        if href.startswith("#"):
            assert href[1:] in document.ids, href
        elif not href.startswith("https://"):
            assert (PORTAL.parent / href).is_file(), href
        else:
            assert href.startswith("https://learn.microsoft.com/"), href


def test_portal_security_boundaries_and_accessible_controls_are_explicit() -> None:
    source = PORTAL.read_text()
    for boundary in ("SYNTHETIC", "DRY_RUN", "VERIFICATION_REQUIRED", "read-only"):
        assert boundary in source
    assert "production authentication" in source
    assert "ingestion proof" in source
    assert "@media print" in source
    assert "prefers-reduced-motion" in source
    for control in Document(source).controls:
        assert control.get("tabindex") == "0"
        assert control.get("aria-label")
        assert control.get("aria-pressed") in {"true", "false"}


def test_portal_commands_tabs_and_reference_content() -> None:
    source = PORTAL.read_text()
    for command in (
        "uv run fsa demo --mode local",
        "uv run fsa demo --mode azure",
        "uv run fsa evaluate",
        "make setup",
        "make validate",
        "make agent365-preflight",
        "make agent365-status",
        "make agent365-verify",
    ):
        assert command in source
    for group in ("shell", "mode", "cloud"):
        assert f'data-tab-group="{group}"' in source
        assert f'data-panel-group="{group}"' in source
    for feature in ("tree-result", "copy-status", "search-status", "versions"):
        assert feature in Document(source).ids
