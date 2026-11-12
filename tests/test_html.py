"""Offline presentation contracts; browser checks remain a separate validation layer."""

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "APEX_Foundry_Security_Agent365_Nov12_2026.html"
PORTAL = ROOT / "docs" / "index.html"
SLIDES = (
    ("mission", "Microsoft Foundry + Security + Agent 365", "00:00", "00:45"),
    ("products", "Every Foundry agent lands in products you already sell", "00:45", "02:00"),
    ("county", "One county, two clouds, four questions", "02:00", "03:00"),
    ("roles", "Who enters the conversation, and when", "03:00", "06:00"),
    ("protect", "Protect · Prove · Operate", "06:00", "08:00"),
    ("pillars", "Six pillars, three verbs, one owner each", "08:00", "09:00"),
    ("planes", "Foundry + Agent 365 architecture: one flow, six planes", "09:00", "10:15"),
    ("identity", "Whose identity is the agent acting with?", "10:15", "11:30"),
    ("lifecycle", "A Foundry agent's lifecycle crosses three control planes", "11:30", "12:30"),
    ("jobs", "Foundry vs Agent 365: two jobs, one integration", "12:30", "14:00"),
    ("registry", "Agent Registry: every action changes one plane", "14:00", "15:00"),
    ("environments", "One repository, three environments, the same controls", "15:00", "16:00"),
    ("request", "A real agent request, then an attack it can't complete", "16:00", "20:00"),
    ("publication", "From Foundry publish to the Agent 365 registry", "20:00", "23:30"),
    ("trace", "Prove: release gates, traces and a verifiable audit trail", "23:30", "28:00"),
    ("defender", "Defender sees two levels: the deployment and the agent", "28:00", "29:30"),
    ("signals", "Why a finding shows in Defender but not in Agent 365", "29:30", "32:00"),
    ("redteam", "A red-team verdict is one layer of seven", "32:00", "33:45"),
    (
        "intervention",
        "Governance and intervention: seven switches, seven effects",
        "33:45",
        "35:00",
    ),
    ("purview", "Purview: what it sees once you turn it on", "35:00", "37:15"),
    ("cloud", "Check every capability in every cloud", "37:15", "39:00"),
    ("gates", "Release gates in CI, then run it in your own Azure", "39:00", "43:00"),
    ("references", "Three takeaways", "43:00", "45:00"),
)


class Document(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[str] = []
        self.assets: list[str] = []
        self.controls: list[dict[str, str | None]] = []
        self.slides: list[dict[str, str | None]] = []
        self.slide_text: list[list[str]] = []
        self.headings: list[list[str]] = []
        self._slide = False
        self._heading = False
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
        if tag == "section" and "slide" in str(attributes.get("class", "")).split():
            self.slides.append(attributes)
            self.slide_text.append([])
            self.headings.append([])
            self._slide = True
        if self._slide and tag in {"h1", "h2"}:
            self._heading = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "section":
            self._slide = False
        if tag in {"h1", "h2"}:
            self._heading = False

    def handle_data(self, data: str) -> None:
        if self._slide:
            self.slide_text[-1].append(data)
            if self._heading:
                self.headings[-1].append(data)


def test_offline_documents_have_unique_resolvable_anchors() -> None:
    for path in (DECK, PORTAL):
        source = path.read_text()
        document = Document(source)
        assert len(document.ids) == len(set(document.ids)), path
        assert not document.assets, "Core documents must not fetch external assets"
        assert "https://" not in "".join(re.findall(r"fetch\([^)]*\)", source))
        for href in document.links:
            if href.startswith("#"):
                assert href[1:] in document.ids, (path, href)
            elif not href.startswith("https://"):
                assert (path.parent / href).is_file(), (path, href)
            else:
                assert href.startswith("https://learn.microsoft.com/"), href


def test_synthetic_status_and_security_boundaries_are_explicit() -> None:
    for path in (DECK, PORTAL):
        source = path.read_text()
        for boundary in ("SYNTHETIC", "DRY_RUN", "VERIFICATION_REQUIRED", "read-only"):
            assert boundary in source, (path, boundary)
        assert "production authentication" in source
        assert "ingestion proof" in source
        assert "@media print" in source
        assert "prefers-reduced-motion" in source
        for control in Document(source).controls:
            assert control.get("tabindex") == "0"
            assert control.get("aria-label")
            assert control.get("aria-pressed") in {"true", "false"}


def test_deck_has_all_explorers_and_presentation_controls() -> None:
    source = DECK.read_text()
    document = Document(source)
    for explorer in (
        "mission",
        "pillars",
        "planes",
        "identity",
        "registry",
        "signals",
        "purview",
        "redteam",
        "trace",
        "gates",
        "cloud",
        "demo",
    ):
        assert f"{explorer}-panel" in document.ids
    for control in (
        "theme",
        "presenter",
        "notes-toggle",
        "timer-toggle",
        "timer-reset",
        "previous",
        "next",
        "jump",
        "progress",
        "depth",
        "audience",
        "print",
    ):
        assert control in document.ids


def test_deck_has_substantive_slides_in_exact_spec_order_with_45_minute_notes() -> None:
    document = Document(DECK.read_text())
    actual = [
        (s.get("id"), s.get("data-title"), s.get("data-start"), s.get("data-end"))
        for s in document.slides
    ]
    assert actual == list(SLIDES)
    for index, (slide, heading, body) in enumerate(
        zip(document.slides, document.headings, document.slide_text, strict=True)
    ):
        _, title, start, end = SLIDES[index]
        assert " ".join(" ".join(heading).split()) == title
        note = str(slide.get("data-note", ""))
        assert note.startswith(f"{start}–{end}. Say:"), title
        assert len(note.split()) >= 35, (title, "Presenter must have actionable narration")
        body_text = " ".join(body)
        assert len(body_text.split()) >= 35, (title, "Not a title-only placeholder")
        assert f"{index + 1:02d} / " in body_text
        assert ("hidden" in slide) == (index != 0)
    assert len({str(slide["data-note"]) for slide in document.slides}) == len(SLIDES)
    assert 'max="23"' in DECK.read_text()


def test_dedicated_topics_have_distinct_evidence_and_intervention_boundaries() -> None:
    document = Document(DECK.read_text())
    bodies = {
        slide["id"]: " ".join(body).lower()
        for slide, body in zip(document.slides, document.slide_text, strict=True)
    }
    contracts = {
        "products": ("access", "do", "observe", "intervene"),
        "county": ("contoso county", "synthetic", "government", "dry_run"),
        "roles": ("data owner", "identity administrator", "independent approver", "operations"),
        "planes": (
            "entra identity",
            "data + tools",
            "observation",
            "policy",
            "foundry",
            "agent 365",
        ),
        "lifecycle": ("build", "evaluate", "publish", "register", "operate", "retire"),
        "jobs": ("workload", "enterprise", "licensing", "registration"),
        "registry": ("block", "developer disable", "legacy exception", "unknown"),
        "environments": ("local", "commercial", "government", "policy", "verification_required"),
        "request": ("s1", "s4", "rehearse", "trace show", "expected", "dry_run"),
        "publication": ("--from-json", "simulated", "unknown", "not an agent registry query"),
        "trace": ("eval --gate", "audit verify", "trace show", "strict", "expected"),
        "defender": ("posture", "runtime", "no simulated alerts"),
        "signals": ("scope", "eligibility", "licence", "cloud", "unknown"),
        "redteam": (
            "verdict",
            "response",
            "invocation",
            "authorization",
            "execution",
            "downstream",
            "adjudication",
            "unknown",
            "raw",
        ),
        "intervention": (
            "blueprint",
            "unblock",
            "developer disable",
            "restore",
            "expire",
            "cleanup",
        ),
        "purview": ("dlp", "licence", "workload", "retention", "documentation only"),
        "cloud": ("verification_required", "service", "feature", "model", "region", "licence"),
        "gates": ("make validate", "fsa eval --gate", "runtime bypass", "authorization"),
        "references": ("protect deliberately", "prove precisely", "operate honestly"),
    }
    for slide, keywords in contracts.items():
        for keyword in keywords:
            assert keyword in bodies[slide], (slide, keyword)
    architecture = re.search(r'<svg class="architecture".*?</svg>', DECK.read_text(), re.S)
    assert architecture is not None
    assert set(re.findall(r'data-plane="([^"]+)"', architecture.group())) == {
        "application",
        "runtime",
        "governance",
        "identity",
        "data",
        "observation",
    }


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
