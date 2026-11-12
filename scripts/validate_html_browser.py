"""Offline browser check with cached Playwright and Chromium.

Run: uv run --offline --with playwright python scripts/validate_html_browser.py
"""

import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    requests: list[str] = []
    checked = 0
    expected_order = [
        "mission",
        "products",
        "county",
        "roles",
        "protect",
        "pillars",
        "planes",
        "identity",
        "lifecycle",
        "jobs",
        "registry",
        "environments",
        "request",
        "publication",
        "trace",
        "defender",
        "signals",
        "redteam",
        "intervention",
        "purview",
        "cloud",
        "gates",
        "references",
    ]
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000}, reduced_motion="reduce", offline=True
        )
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: requests.append(request.url))
        page.goto((root / "APEX_Foundry_Security_Agent365_Nov12_2026.html").as_uri())
        slides = page.locator(".slide").count()
        assert (
            page.locator(".slide").evaluate_all("(nodes) => nodes.map(node => node.id)")
            == expected_order
        )
        assert page.locator("#jump option").count() == slides == 23
        assert page.locator("#progress").get_attribute("max") == str(slides)
        assert page.locator("[data-plane]").count() == 6
        explorers = page.locator("[data-explorer]").evaluate_all(
            "(nodes) => [...new Set(nodes.map(node => node.dataset.explorer))]"
        )
        assert set(explorers) == {
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
        }
        page.locator("#notes-toggle").click()
        for index in range(slides):
            page.locator("#jump").select_option(index=index)
            slide = page.locator(".slide").nth(index)
            assert page.locator(".slide:visible").count() == 1
            assert slide.is_visible()
            assert page.locator("#counter").inner_text() == f"{index + 1:02d} / 23"
            assert page.locator("#progress").get_attribute("value") == str(index + 1)
            assert page.url.endswith("#" + expected_order[index])
            assert page.locator("#note-content").inner_text() == slide.get_attribute("data-note")
            expect(page.locator("#notes")).to_be_visible()
            for control in slide.locator("[data-key]").all():
                control.click()
                assert control.get_attribute("aria-pressed") == "true"
                group = control.evaluate(
                    "(node) => node.closest('[data-explorer]').dataset.explorer"
                )
                expect(page.locator(f"#{group}-panel h3")).not_to_be_empty()
                expect(page.locator(f"#{group}-panel p")).not_to_be_empty()
                checked += 1
        page.locator("#jump").select_option(value="6")
        for key in ("Enter", "Space"):
            node = page.locator('g[data-key="app"]')
            node.focus()
            page.keyboard.press(key)
            assert node.get_attribute("aria-pressed") == "true"
        page.locator("#jump").select_option(value=str(slides - 1))
        page.locator("#notes-toggle").click()
        page.locator("#depth").select_option(label="L600")
        assert page.locator("#depth-label").inner_text() == "L600"
        page.locator("#audience").select_option(label="Security")
        assert page.locator("#perspective").inner_text()
        theme = page.locator("html").get_attribute("data-theme")
        page.locator("#theme").click()
        assert page.locator("html").get_attribute("data-theme") != theme
        page.locator("#presenter").click()
        assert page.locator("#presenter").get_attribute("aria-pressed") == "true"
        page.locator("#notes-toggle").click()
        assert page.locator("#notes").is_visible()
        page.locator("#timer-toggle").click()
        expect(page.locator("#timer")).not_to_have_text("00:00", timeout=5000)
        page.locator("#timer-toggle").click()
        page.locator("#timer-reset").click()
        assert page.locator("#timer").inner_text() == "00:00"
        page.locator("#previous").click()
        page.locator("#next").click()
        page.locator("body").click(position={"x": 2, "y": 2})
        page.keyboard.press("Home")
        assert page.locator("#jump").input_value() == "0"
        assert page.locator("#previous").is_disabled()
        page.keyboard.press("ArrowRight")
        assert page.locator("#jump").input_value() == "1"
        page.keyboard.press("PageDown")
        assert page.locator("#jump").input_value() == "2"
        page.keyboard.press("PageUp")
        assert page.locator("#jump").input_value() == "1"
        page.keyboard.press("End")
        assert page.locator("#jump").input_value() == str(slides - 1)
        assert page.locator("#next").is_disabled()
        page.locator("#jump").focus()
        page.keyboard.press("p")
        assert page.locator("#presenter").get_attribute("aria-pressed") == "true"
        page.locator("#help").click()
        assert page.locator("dialog").is_visible()
        page.keyboard.press("Escape")
        page.emulate_media(media="print")
        assert page.locator(".slide:visible").count() == slides
        page.emulate_media(media="screen")
        page.set_viewport_size({"width": 390, "height": 844})
        for index in range(slides):
            page.locator("#jump").select_option(index=index)
            assert page.locator(".slide").nth(index).is_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
                expected_order[index]
            )
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.goto((root / "docs/index.html").as_uri())
        page.locator("#search").fill("no-match-synthetic-query-31415")
        assert page.locator(".doc-section:visible").count() == 0
        page.locator("#search").fill("")
        assert page.locator(".doc-section:visible").count() == 16
        for group in ("mode", "shell", "cloud"):
            for tab in page.locator(f'[data-tab-group="{group}"]').all():
                tab.click()
                assert tab.get_attribute("aria-selected") == "true"
                checked += 1
        for control in page.locator("[data-arch]").all():
            control.click()
            assert control.get_attribute("aria-pressed") == "true"
            checked += 1
        page.locator("#tree-options button").first.click()
        assert "Local" in page.locator("#tree-result").inner_text()
        page.locator("#tree-reset").click()
        assert "Select" in page.locator("#tree-result").inner_text()
        page.locator(".copy:visible").first.click()
        expect(page.locator("#copy-status")).not_to_be_empty()
        theme = page.locator("html").get_attribute("data-theme")
        page.locator("#theme").click()
        assert page.locator("html").get_attribute("data-theme") != theme
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.locator("#search").is_visible()
        page.emulate_media(media="print")
        assert page.locator(".doc-section:visible").count() == 16
        browser.close()
    assert not errors, errors
    assert all(url.startswith(("file:", "data:")) for url in requests), requests
    print(
        json.dumps(
            {
                "status": "PASS",
                "explorer_and_tab_controls": checked,
                "slides": slides,
                "explorers": len(explorers),
                "offline_context": True,
                "mobile_slides_checked": slides,
                "page_errors": errors,
                "network_requests": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
