"""Explicit extraction for build systems and JDK-free Sphinx rendering."""

import argparse
import os
from pathlib import Path
import sys

from sphinx.errors import ExtensionError

from .extractor import atomic_write, extract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sources", nargs="+", type=Path, help="Java files or source roots"
    )
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument(
        "--classpath", default="", help=f"Compile classpath separated by {os.pathsep!r}"
    )
    parser.add_argument(
        "--classpath-file",
        type=Path,
        help="UTF-8 file containing a platform-separated compile classpath",
    )
    parser.add_argument(
        "--sourcepath",
        action="append",
        default=[],
        type=Path,
        help="Source lookup directory for ancestor docs; repeat for multiple roots",
    )
    parser.add_argument("--jdk", default="", help="JDK 25 home (default: java on PATH)")
    parser.add_argument(
        "--release", default="", help="Source/API release accepted by the installed JDK"
    )
    parser.add_argument("--cache", type=Path, default=Path(".java-autodoc-cache"))
    parser.add_argument("--warnings-as-errors", action="store_true")
    args = parser.parse_args()
    try:
        cp = args.classpath
        if args.classpath_file:
            cp += os.pathsep + args.classpath_file.read_text(encoding="utf-8").strip()
        model = extract(
            args.sources,
            [Path(p) for p in cp.split(os.pathsep) if p],
            args.cache,
            jdk=args.jdk,
            release=args.release,
            sourcepath=args.sourcepath,
        )
        diagnostics = model.root.findall("diagnostic")
        for diagnostic in diagnostics:
            print("warning: " + (diagnostic.text or ""), file=sys.stderr)
        if diagnostics and args.warnings_as_errors:
            return 1
        atomic_write(args.output, model.path.read_bytes())
    except (ExtensionError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
