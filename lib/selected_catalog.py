"""Inspect a Stack+ selection or stage one pinned bundle without changing a host."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "registry/stackplus-selections.json"


def relative(path):
    value = PurePosixPath(path)
    if not path or value.is_absolute() or ".." in value.parts or "\\" in path:
        raise ValueError(f"Invalid relative source path: {path!r}")
    return value


def git(repo, *args, **kwargs):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_NO_REPLACE_OBJECTS="1")
    return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-C", repo, *args],
                          check=True, env=env, **kwargs)


def export_leaf(row, catalog, package, work, local):
    source = row["source"]
    owner, pin = source["repository"], source["revision"]
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", owner) or not re.fullmatch(r"[0-9a-f]{40}", pin):
        raise ValueError("Invalid publisher or source revision")
    repo = local or work/"upstream"
    if local is None:
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "remote", "add", "origin", "https://github.com/"+owner+".git")
        git(repo, "config", "remote.origin.promisor", "true")
        git(repo, "config", "remote.origin.partialclonefilter", "blob:none")
        git(repo, "fetch", "--quiet", "--no-tags", "--depth=1", "--filter=blob:none", "origin", pin)
    actual = git(repo, "rev-parse", "--verify", pin+"^{commit}", capture_output=True, text=True).stdout.strip()
    if actual != pin:
        raise ValueError("Source revision did not match the selected commit")

    leaf = relative(row["leaf"])
    paths = [str(leaf), *catalog["shared_support"].get(row.get("shared"), [])]
    root_entries = git(repo, "ls-tree", "--name-only", "-z", pin, capture_output=True).stdout
    for name in os.fsdecode(root_entries).split("\0"):
        if re.fullmatch(r"(LICENSE|COPYING|NOTICE)(\.[a-zA-Z0-9_-]+)?", name, re.I):
            paths.append(name)
    for p in paths:
        relative(p)
    archive_path = work/"selected.tar"
    git(repo, "archive", "--format=tar", "--output="+str(archive_path), pin, "--", *paths)
    with tarfile.open(archive_path, "r:") as archive:
        for item in archive:
            target = package/relative(item.name)
            if item.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif item.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(item) as src, target.open("xb") as out:
                    shutil.copyfileobj(src, out)
                if item.mode & 0o111:
                    target.chmod(0o755)
            else:
                raise ValueError(f"Review linked or special file before staging: {item.name}")
    return package/leaf/"SKILL.md"


def apply_proof_acceptance(entry, reference):
    """Attach the selected Lean proof acceptance workflow to its upstream entry."""
    destination = entry.parent/"references/proof-acceptance.md"
    link = "[the proof acceptance workflow](references/proof-acceptance.md)"
    upstream_verification = "Never declare a proof complete while `sorry` placeholders or error diagnostics remain."
    guidance = f"Before accepting the final proof, follow {link}."
    original = entry.read_text()
    if original.count(upstream_verification) != 1:
        raise ValueError("Review the upstream Lean verification section before attaching proof acceptance")
    workflow = reference.read_bytes()
    destination.parent.mkdir(exist_ok=True)
    if not destination.exists() or destination.read_bytes() != workflow:
        destination.write_bytes(workflow)
    if guidance not in original:
        entry.chmod(entry.stat().st_mode | 0o200)
        entry.write_text(original.replace(upstream_verification, upstream_verification+"\n\n"+guidance))


def stage(row, catalog, destination, local):
    destination = destination.parent.resolve()/destination.name
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"Choose a new destination: {destination}")
    if not destination.parent.is_dir():
        raise ValueError("Create the destination's parent directory first")
    name = row["name"]
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".stackplus-") as tmp:
        work = Path(tmp)
        prepared = work/"prepared"
        package = prepared/"package"
        prepared.mkdir()
        if row.get("checkout_bundle"):
            origin = ROOT/relative(row["checkout_bundle"])
            shutil.copytree(origin, package, symlinks=True)
            entry = package/"SKILL.md"
        elif row.get("native_base"):
            # Original native builder applies the reviewed patches, closures and licenses.
            home, state = work/"isolated-home", work/"state"
            home.mkdir()
            isolated_env = dict(os.environ, HOME=str(home), CODEX_HOME=str(home/".codex"), NSTACK_STATE=str(state))
            subprocess.run([sys.executable, "-B", ROOT/"native_setup.py", "install", "--only", name,
                            "--home", home, "--codex-home", home/".codex", "--state", state],
                           cwd=ROOT, env=isolated_env, check=True, stdout=sys.stderr)
            material = (home/".agents/skills"/name/"SKILL.md").resolve(strict=True)
            original = next((p for p in material.parents if p.name == name and p.parent.name == "bundles"), None)
            if original is None or not original.is_relative_to(state):
                raise ValueError("Native builder returned an unexpected package location")
            shutil.copytree(original, package, symlinks=True)
            entry = package/material.relative_to(original)
        elif row.get("leaf"):
            entry = export_leaf(row, catalog, package, work, local)
        else:
            raise ValueError("This source is a reference. Inspect its selected coordinates.")
        for file in package.rglob("*"):
            if file.is_symlink() and not file.resolve(strict=True).is_relative_to(package):
                raise ValueError(f"Package link escapes its scope: {file.relative_to(package)}")
        raw = entry.read_text()
        first, header, body = raw.split("---", 2)
        if first.strip():
            raise ValueError("Skill entry has no YAML frontmatter")
        name_field = re.search(r"(?m)^name:[ \t]*[^\n]+$", header)
        if not name_field:
            raise ValueError("Skill entry has no name")
        original_name = name_field.group().partition(":")[2].strip().strip("\"'")
        if original_name != name:
            header = header[:name_field.start()]+"name: "+json.dumps(name)+header[name_field.end():]
        if row.get("description"):
            field = re.search(r"(?m)^description:[ \t]*(\S[^\n]*)$", header)
            if not field or field[1].startswith(("|", ">")):
                raise ValueError("Review changed publisher frontmatter before applying the selected description")
            header = header[:field.start()]+"description: "+json.dumps(row["description"])+header[field.end():]
        adapted = "---".join((first, header, body))
        if adapted != raw:
            entry.chmod(entry.stat().st_mode | 0o200)
            entry.write_text(adapted)
        if row.get("proof_acceptance"):
            apply_proof_acceptance(entry, ROOT/relative(row["proof_acceptance"]))
        (prepared/"skills").mkdir()
        (prepared/"skills"/name).symlink_to(os.path.relpath(entry.parent, prepared/"skills"))
        digest = hashlib.sha256()
        documents = {}
        for file in sorted(package.rglob("*")):
            if file.is_file():
                key = file.relative_to(package).as_posix()
                value = hashlib.sha256(file.read_bytes())
                digest.update(key.encode()+b"\0"+value.digest())
                documents[key] = value.hexdigest()
        receipt = {"name":name, "scope":row["scope"], "source":row.get("source", row.get("checkout_bundle")),
                   "files":len(documents), "package_sha256":digest.hexdigest(), "entry":entry.relative_to(prepared).as_posix(),
                   "document_sha256":documents}
        (prepared/"bundle.json").write_text(json.dumps(receipt, indent=2)+"\n")
        # mkdir refuses a destination created concurrently, including an empty one.
        destination.mkdir()
        try:
            prepared.rename(destination/"bundle")
        except BaseException:
            destination.rmdir()
            raise
    return destination/"bundle"/"skills"/name


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("terms", nargs="*", help="words in the native name, scope, source or path")
    parser.add_argument("--json", action="store_true", help="print structured source metadata")
    parser.add_argument("--stage", nargs=2, metavar=("NAME", "NEW_DIRECTORY"), help="prepare a complete selected package in a new directory")
    parser.add_argument("--source-checkout", type=Path, help="use a local Git object store for a pinned upstream leaf")
    args = parser.parse_args(argv)
    catalog = json.loads(CATALOG.read_text())
    if args.stage:
        if args.terms:
            parser.error("--stage takes one exact native name and a new directory")
        name, location = args.stage
        row = next((r for r in catalog["methods"] if r["name"] == name),None)
        if row is None:
            parser.error("Unknown selected method: "+name)
        if args.source_checkout and (row.get("native_base") or row.get("checkout_bundle")):
            parser.error("--source-checkout applies to direct publisher leaves")
        try:
            path = stage(row, catalog, Path(location), args.source_checkout)
        except (OSError, ValueError, subprocess.CalledProcessError, tarfile.TarError) as exc:
            parser.exit(1,"Stage failed: "+str(exc)+"\n")
        print(json.dumps({"skill":str(path)}) if args.json else str(path))
        return
    if args.source_checkout:
        parser.error("--source-checkout requires --stage")
    terms = [s.casefold() for word in args.terms for s in word.split() if s]
    rows = [r for r in catalog["methods"] if all(term in json.dumps(r,ensure_ascii=False).casefold() for term in terms)]
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        for row in rows:
            source = row.get("source",{})
            print(f"{row['name']}\t{row['scope']}\t{source.get('repository',row.get('checkout_bundle',''))}")


if __name__ == "__main__":
    main()
