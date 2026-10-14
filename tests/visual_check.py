"""Opt-in browser validation of the standalone fixture site in five themes.

    python -m playwright install chromium
    sphinx-build -W --keep-going -n examples/standalone/docs examples/standalone/docs/_build/html
    sphinx-build -W --keep-going -n -D html_theme=classic examples/standalone/docs \\
        examples/standalone/docs/_build/classic
    # ...and likewise for each other theme in THEMES, into _build/<theme>.
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
# Theme name and its build directory under examples/standalone/docs/_build.
THEMES = (
    ("alabaster", "html"),
    ("classic", "classic"),
    ("furo", "furo"),
    ("sphinx_rtd_theme", "sphinx_rtd_theme"),
    ("lumina", "lumina"),
)


def main():
    output = ROOT / "build/visual"
    output.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        partial(
            SimpleHTTPRequestHandler,
            directory=str(ROOT / "examples/standalone/docs/_build"),
        ),
    )
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    report = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for theme, folder in THEMES:
                for width in (1440, 390):
                    page = browser.new_page(viewport={"width": width, "height": 1000})
                    errors = []
                    page.on(
                        "pageerror", lambda error, errors=errors: errors.append(error)
                    )
                    base = f"http://127.0.0.1:{server.server_port}/{folder}"
                    # The theme's own layout: its index page and native Sphinx objects.
                    theme_width = 0
                    for reference in ("index", "reference"):
                        # Themes load icons and fonts late; measure the settled page.
                        page.goto(f"{base}/{reference}.html", wait_until="networkidle")
                        theme_width = max(
                            theme_width,
                            page.evaluate("document.documentElement.scrollWidth"),
                        )
                    # Anchors contain ":" and "(", which theme scripts must accept.
                    page.goto(
                        base
                        + "/api/type-demo.Widget.html#java:demo.Widget-convert(int)",
                        wait_until="networkidle",
                    )
                    # Some themes scroll smoothly; wait until the target is in view.
                    page.wait_for_function(
                        """() => {
                          const id = decodeURIComponent(location.hash.slice(1));
                          const top = document.getElementById(id).getBoundingClientRect().top;
                          return top > -1 && top < innerHeight;
                        }"""
                    )
                    assert page.locator("dl.java").count() >= 8
                    assert page.locator("h2", has_text="Constructors").count() == 1
                    assert page.locator("pre").count() > 0
                    assert page.locator("dl.java ul li ol li").count() == 2
                    assert page.locator('a[href^="#java:"]').count() > 0
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
                    table = page.locator("table.java-table")
                    assert (
                        table.locator("caption")
                        .inner_text()
                        .startswith("Conversion examples")
                    )
                    assert table.locator("thead th").count() == 3
                    assert 'Labelled "widget"' in table.inner_text()
                    wrapper = page.locator(".java-table-wrapper")
                    assert wrapper.bounding_box()["width"] <= width
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
                    # Classic has a fixed minimum width, and some themes overflow on phones
                    # for native objects too; Java content must not add to that.
                    assert api_width <= max(width, theme_width) + 1, (
                        f"Java content adds page overflow: {theme} at {width}px"
                    )
                    page.goto(base + "/index.html")
                    page.locator('.toctree-wrapper a[href="guide.html"]').first.click()
                    assert page.url.endswith("/guide.html")
                    page.goto(base + "/search.html?q=convert")
                    page.wait_for_function(
                        "document.querySelectorAll('#search-results li').length > 0"
                    )
                    page.screenshot(
                        path=str(output / f"{theme}-{width}-search.png"),
                        full_page=True,
                    )
                    assert not errors, f"Page errors in {theme} at {width}px: {errors}"
                    page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
