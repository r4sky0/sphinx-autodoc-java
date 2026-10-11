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
                    page.goto(base + "/api/type-demo.Widget.html")
                    assert page.locator("dl.java").count() >= 8
                    assert page.get_by_text("Constructors", exact=True).count() == 1
                    assert page.locator("pre").count() > 0
                    assert page.locator("ul li ol li").count() == 2
                    assert page.locator('a[href^="#java-"]').count() > 0
                    overflow = page.evaluate(
                        "document.documentElement.scrollWidth > window.innerWidth + 1"
                    )
                    page.screenshot(
                        path=str(output / f"{theme}-{width}.png"), full_page=True
                    )
                    report.append(
                        {"theme": theme, "width": width, "page_overflow": overflow}
                    )
                    assert not overflow, f"Page overflow: {theme} at {width}px"
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
