"""Build a real-world showcase site and compare its warnings with a recorded baseline.

    uv run --locked python showcase/build.py [--update-baseline] [showcase/commons-lang]

Fetches the pinned upstream commit explicitly (documentation builds never download
sources themselves) and builds it under build/showcase/<name> once per theme in
showcase.json, writing html/<theme>/, warnings-<theme>.log and report.json there.
Exits nonzero if a theme's warning category exceeds its baseline in showcase.json;
--update-baseline records the current counts.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CATEGORY = re.compile(r"\[([\w.]+)\]$")


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def fetch(meta: dict, upstream: Path) -> None:
    """Checks out exactly the pinned commit, reusing a matching checkout."""
    if (upstream / ".git").exists():
        if git("rev-parse", "HEAD", cwd=upstream) == meta["commit"]:
            return
        shutil.rmtree(upstream)
    upstream.mkdir(parents=True)
    git("init", "--quiet", cwd=upstream)
    git(
        "fetch",
        "--quiet",
        "--depth",
        "1",
        meta["repository"],
        meta["commit"],
        cwd=upstream,
    )
    git("checkout", "--quiet", "FETCH_HEAD", cwd=upstream)
    head = git("rev-parse", "HEAD", cwd=upstream)
    if head != meta["commit"]:
        sys.exit(f"Fetched {head}, expected pinned commit {meta['commit']}.")


def build(docs: Path, html: Path, doctrees: Path, log: Path, theme: str) -> float:
    started = time.monotonic()
    subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx",
            # -Q and parallel builds do not reliably write the -w log, so build
            # serially and quietly, with warnings still recorded.
            "-q",
            "--keep-going",
            "-w",
            str(log),
            "-d",
            str(doctrees),
            str(docs),
            str(html),
        ],
        check=True,
        env={**os.environ, "SHOWCASE_THEME": theme},
    )
    return round(time.monotonic() - started, 1)


def count(log: Path) -> dict[str, int]:
    lines = log.read_text().splitlines() if log.exists() else []
    warnings = Counter(
        (match.group(1) if (match := CATEGORY.search(line)) else "other")
        for line in lines
        if "WARNING:" in line
    )
    return dict(sorted(warnings.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "showcase", nargs="?", default=Path(__file__).parent / "commons-lang", type=Path
    )
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args()
    source = args.showcase.resolve()
    meta_path = source / "showcase.json"
    meta = json.loads(meta_path.read_text())
    work = ROOT / "build" / "showcase" / source.name
    fetch(meta, work / "upstream")

    docs, html = work / "docs", work / "html"
    shutil.rmtree(docs, ignore_errors=True)
    shutil.rmtree(html, ignore_errors=True)
    shutil.copytree(source, docs, ignore=shutil.ignore_patterns("__pycache__"))
    report = {
        "name": meta["name"],
        "version": meta["version"],
        "commit": meta["commit"],
    }
    regressions = []
    # One doctree directory: later themes reuse the cached extraction.
    for theme in meta["themes"]:
        log = work / f"warnings-{theme}.log"
        log.unlink(missing_ok=True)
        seconds = build(docs, html / theme, work / "doctrees", log, theme)
        warnings = count(log)
        report[theme] = {"seconds": seconds, "warnings": warnings}
        pages = len(list((html / theme / "api").glob("*.html")))
        print(f"{theme}: {pages} API pages in {seconds}s")
        baseline = meta["warnings"].get(theme, {})
        for category in sorted(warnings.keys() | baseline.keys()):
            now, before = warnings.get(category, 0), baseline.get(category, 0)
            marker = " (above baseline)" if now > before else ""
            print(f"  {category:<28} {now:>5}  baseline {before:>5}{marker}")
            if now > before:
                regressions.append(f"{theme} {category}")
    (work / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    if args.update_baseline:
        meta["warnings"] = {
            theme: report[theme]["warnings"] for theme in meta["themes"]
        }
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
        print(f"Recorded baseline in {meta_path.relative_to(ROOT)}.")
        return 0
    if regressions:
        print(
            f"Warnings increased for {', '.join(regressions)}; see {work.relative_to(ROOT)}."
            " If intended, rerun with --update-baseline."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
