"""Opt-in browser validation; run after building Alabaster and Classic HTML.

    python -m playwright install chromium
    python tests/visual_check.py

Produces screenshots and a JSON report under build/visual. Not part of pytest:
browser binaries must be installed explicitly. A failed check exits nonzero.
"""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "build/visual"
    output.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        partial(SimpleHTTPRequestHandler, directory=str(ROOT / "docs/_build")),
    )
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    report = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for theme, folder in (("alabaster", "html"), ("classic", "classic")):
                for width in (1440, 390):
                    page = browser.new_page(viewport={"width": width, "height": 1000})
                    base = f"http://127.0.0.1:{server.server_port}/{folder}"
                    page.goto(base + "/index.html")
                    theme_width = page.evaluate("document.documentElement.scrollWidth")
                    page.goto(base + "/api/type-demo.Widget.html")
                    assert page.locator("dl.java").count() >= 8
                    assert (
                        page.locator(
                            'dt.sig a[href*="type-demo.Transformer.html"]'
                        ).count()
                        > 0
                    )
                    assert (
                        page.locator('dt.sig a[href*="java/lang/String.html"]').count()
                        > 0
                    )
                    assert page.get_by_text("Constructors", exact=True).count() == 1
                    assert page.locator("pre").count() > 0
                    assert page.locator("ul li ol li").count() == 2
                    assert page.locator('a[href^="#java-"]').count() > 0
                    lines = page.locator("dl.java .line-block > .line")
                    assert lines.all_text_contents() == [
                        "First line",
                        "Second line",
                        "Third line",
                        "Last line.",
                    ]
                    assert (
                        lines.nth(1).bounding_box()["y"]
                        > lines.nth(0).bounding_box()["y"]
                    )
                    assert (
                        page.get_by_role("link", name="query parameters").get_attribute(
                            "href"
                        )
                        == "https://example.test/?a=1&b=2"
                    )
                    api_width = page.evaluate("document.documentElement.scrollWidth")
                    page.screenshot(
                        path=str(output / f"{theme}-{width}.png"), full_page=True
                    )
                    report.append(
                        {
                            "theme": theme,
                            "width": width,
                            "theme_page_width": theme_width,
                            "api_page_width": api_width,
                            "page_overflow": api_width > width + 1,
                        }
                    )
                    # Classic has a fixed sidebar/minimum width even without Java content.
                    assert api_width <= max(width, theme_width) + 1, (
                        f"Java content adds page overflow: {theme} at {width}px"
                    )
                    page.goto(base + "/index.html")
                    page.locator('a[href="guide.html"]').first.click()
                    assert page.url.endswith("/guide.html")
                    page.goto(base + "/search.html?q=convert")
                    page.wait_for_function(
                        "document.querySelectorAll('#search-results li').length > 0"
                    )
                    page.screenshot(
                        path=str(output / f"{theme}-{width}-search.png"), full_page=True
                    )
                    page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
