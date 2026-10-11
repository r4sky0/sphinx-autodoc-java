"""Build a real-world showcase site and compare its warnings with a recorded baseline.

    uv run --locked python showcase/build.py [--update-baseline] [showcase/commons-lang]

Fetches the pinned upstream commit explicitly (documentation builds never download
sources themselves), builds it under build/showcase/<name>, and writes html/,
warnings.log and report.json there. Exits nonzero if any warning category exceeds
the baseline in showcase.json; --update-baseline records the current counts.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
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

    docs, html, log = work / "docs", work / "html", work / "warnings.log"
    shutil.rmtree(docs, ignore_errors=True)
    shutil.rmtree(html, ignore_errors=True)
    shutil.copytree(source, docs, ignore=shutil.ignore_patterns("__pycache__"))
    started = time.monotonic()
    subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx",
            "-Q",
            "-j",
            "auto",
            "--keep-going",
            "-w",
            str(log),
            str(docs),
            str(html),
        ],
        check=True,
    )
    seconds = round(time.monotonic() - started, 1)

    warnings = Counter(
        (match.group(1) if (match := CATEGORY.search(line)) else "other")
        for line in log.read_text().splitlines()
        if "WARNING:" in line
    )
    report = {
        "name": meta["name"],
        "version": meta["version"],
        "commit": meta["commit"],
        "pages": len(list((html / "api").glob("*.html"))),
        "seconds": seconds,
        "warnings": dict(sorted(warnings.items())),
        "total": sum(warnings.values()),
    }
    (work / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"{meta['name']} {meta['version']}: {report['pages']} API pages in {seconds}s"
    )

    baseline = meta["warnings"]
    regressions = []
    for category in sorted(warnings.keys() | baseline.keys()):
        now, before = warnings.get(category, 0), baseline.get(category, 0)
        marker = " (above baseline)" if now > before else ""
        print(f"  {category:<28} {now:>5}  baseline {before:>5}{marker}")
        if now > before:
            regressions.append(category)

    if args.update_baseline:
        meta["warnings"] = report["warnings"]
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
        print(f"Recorded baseline in {meta_path.relative_to(ROOT)}.")
        return 0
    if regressions:
        print(
            f"Warnings increased for {', '.join(regressions)}; see {log.relative_to(ROOT)}."
            " If intended, rerun with --update-baseline."
        )
        return 1
    if report["total"] < sum(baseline.values()):
        print("Fewer warnings than the baseline; record them with --update-baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
