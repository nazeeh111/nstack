#!/usr/bin/env python3
"""Bounded local discovery of installed nstack instructions and runtime records."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re


def inventory(state):
    records, sources = [], []
    for filename, kind in (("native-skill-index.json", "skill"),
                           ("native-tools/index.json", "runtime")):
        source = state / filename
        if not source.is_file():
            continue
        raw = source.read_bytes()
        rows = json.loads(raw)
        if not isinstance(rows, list):
            raise ValueError("Expected an array in " + filename)
        sources.append({"file": str(source), "sha256": hashlib.sha256(raw).hexdigest()})
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("name"), str):
                continue
            record = {"kind": kind, "name": row["name"]}
            if kind == "skill":
                entry = Path(row.get("skill_path", ""))
                # The index cannot redirect frontmatter reads to private files.
                if entry.name != "SKILL.md" or not entry.resolve().is_relative_to(
                        (state / "native-releases").resolve()):
                    continue
                record.update(path=str(entry), instructions_present=entry.is_file())
                if entry.is_file():
                    with entry.open(encoding="utf-8") as stream:
                        head = stream.read(4096)
                    front = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", head, re.S)
                    if front:
                        match = re.search(r"(?m)^description:\s*(.+)$", front[1])
                        if match:
                            record["description"] = match[1].strip().strip("'\"")
                        if re.search(r"(?m)^disable-model-invocation:\s*true\s*$", front[1]):
                            record["manual_only"] = True
                record["deployment"] = row.get("deployment", "recorded")
            else:
                # Never emit arbitrary environment, provider or credential fields.
                for key in ("version", "source_revision", "native_mcp", "binary",
                            "python", "node", "entrypoint"):
                    if isinstance(row.get(key), str):
                        record[key] = row[key]
                if isinstance(row.get("checks"), str):
                    record["recorded_checks"] = row["checks"]
            records.append(record)
    return records, sources


def search(state, terms, limit=8):
    records, sources = inventory(Path(state))
    words = [word.casefold() for word in terms if word.strip()]
    ranked = []
    for record in records:
        text = " ".join(str(record.get(key, "")) for key in
                        ("name", "description", "native_mcp", "recorded_checks")).casefold()
        score = sum(word in text for word in words)
        if score:
            ranked.append((score, record))
    ranked.sort(key=lambda item: (-item[0], item[1]["kind"], item[1]["name"]))
    return {"matches": [row for _, row in ranked[:limit]], "total_matches": len(ranked),
            "sources": sources,
            "scope": "Local discovery only. A record or existing instructions do not prove "
                     "callability, current authorization or a successful operation. "
                     "Connected host tools and plugins require native discovery separately."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("terms", nargs="+")
    parser.add_argument("--state", type=Path, default=Path(os.environ.get(
        "NSTACK_STATE", Path.home() / "Library/Application Support/nstack")))
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.limit <= 30:
        parser.error("--limit must be between 1 and 30")
    try:
        print(json.dumps(search(args.state, args.terms, args.limit), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
