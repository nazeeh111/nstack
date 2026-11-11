#!/usr/bin/env python
"""
Check every quoted line in a council session against the seats' brains.

Usage:
  python .claude/skills/roast-room/scripts/check_quotes.py <session folder>

Scans round-*.md and verdict.md for quotes attributed to a source id, like "..." (S095), and looks
for each in the brain files. A quote that is in no brain is either a quote of
another seat or the founder (fine if it appears in an earlier round file of the
same session) or an invented quote (flag it and remove it from the verdict).
Exit code 1 if any quote is unaccounted for.
"""
import re
import sys
from pathlib import Path

# Source brains stay private and are selected explicitly; no credential/config lookup.
import argparse


def arguments():
    parser = argparse.ArgumentParser(description="Local corpus excerpt lint; not original-source authentication")
    parser.add_argument("session", type=Path)
    parser.add_argument("--brains", required=True, type=Path)
    args = parser.parse_args()
    if not args.brains.is_dir() or not any(args.brains.glob("*/*.md")):
        parser.error("selected private brain corpus is absent or empty")
    return args


def norm(s):
    s = s.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    args = arguments()
    session = args.session
    brains = args.brains
    brain_text = norm(" ".join(p.read_text(encoding="utf-8", errors="replace") for p in brains.rglob("*.md")))
    session_files = sorted(session.glob("round-*.md")) + [p for p in [session / "verdict.md"] if p.exists()]
    brief = norm((session / "brief.md").read_text(encoding="utf-8")) if (session / "brief.md").exists() else ""
    bad, ok, internal = [], 0, 0
    seen_session = ""
    for f in session_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        # only quotes attributed to a source id, e.g. "..." (S095) or "..." [S048, 2026]
        for q in re.findall(r"[\"“]([^\"“”\n]{20,400})[\"”][^\n\"]{0,40}?[\(\[]S\d{3}", text):
            nq = norm(q)
            if len(nq.split()) < 6:
                continue
            if nq in brain_text:
                ok += 1
            elif nq in seen_session or nq in brief:
                internal += 1
            else:
                bad.append((f.name, q))
        seen_session += " " + norm(text)
    print(f"local corpus matches (not source authentication): {ok}; quotes of earlier rounds or the brief: {internal}; unverified: {len(bad)}")
    for name, q in bad:
        print(f"  UNVERIFIED [{name}] \"{q[:160]}\"")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
