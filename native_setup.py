#!/usr/bin/env python3
"""Install the reviewed native skill collection without per-project initialization."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, shlex, shutil, stat, subprocess, sys, tempfile
P = pathlib.Path
ROOT = P(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "lib"))
import nstack
import install as profile_install
from transaction import Transaction, atomic_json, copy, fingerprint, same

def sha(data):
    return hashlib.sha256(data).hexdigest()

def tree(root):
    result = {}
    for p in sorted(root.rglob("*")):
        if p == root / "NATIVE-MANIFEST.json":
            continue
        rel = str(p.relative_to(root))
        if p.is_symlink():
            result[rel] = {"link": os.readlink(p)}
        elif p.is_file():
            result[rel] = {"sha256": sha(p.read_bytes()), "mode": p.stat().st_mode & 0o777}
        elif p.is_dir():
            result[rel] = {"directory": True, "mode": p.stat().st_mode & 0o777}
    return result

def selection():
    modes = {c["id"]: c["deployment"] for c in nstack.manifest()["components"]}
    rows = []
    for s in nstack.manifest()["skills"]:
        if modes[s["candidate_id"]] != "on demand" or s["delivery"] not in ("intact upstream leaf", "narrow-patched leaf"):
            continue
        name = nstack.shelf_name(s["candidate_id"], s["source_path"], s["source_repository"])
        prefix = s["candidate_id"].lower() + "-"
        if not name.startswith(prefix):
            raise ValueError("Unexpected source skill name")
        name = name[len(prefix):]
        rows.append((name, s))
    names = [name for name, _ in rows]
    if len(names) != len(set(names)):
        raise ValueError("Natural skill names collide")
    return rows

def index_rows(originals, addons, release):
    rows = []
    for name, s, _, r in originals:
        rows.append({
            "name": name, "candidate_id": s["candidate_id"],
            "repository": s["source_repository"], "revision": s["revision"],
            "source_path": s["source_path"], "license": s["rights"],
            "skill_path": str(release / "bundles" / name / r.get("entry_dir", ".") / "SKILL.md"),
            "deployment": "on demand",
            "installation_adaptation": "Natural entry name; complete reviewed support bundle retained.",
        })
    for name in addons:
        provenance = json.loads((ROOT / "addons" / name / "SOURCE.json").read_text())
        rows.append({"name": name, "skill_path": str(release / "bundles" / name / "SKILL.md"),
                     "deployment": "on demand", **provenance})
    return rows

def expected_tree(originals, addons, release, index):
    # Derive expected adapted bytes from verified original releases, never from
    # a cached adaptation's own self-authored inventory.
    expected = {"bundles": {"directory": True, "mode": 0o555},
                "skills": {"directory": True, "mode": 0o555}}
    def add_directory(rel):
        expected[str(rel)] = {"directory": True, "mode": 0o555}
    for name, _, source, receipt in originals:
        prefix = P("bundles") / name
        add_directory(prefix)
        entry = P(receipt.get("entry_dir", ".")) / "SKILL.md"
        original_entry = (source / entry).read_bytes()
        if sha(original_entry) != receipt["files"][str(entry)]:
            raise ValueError("Original selected entry changed during preparation")
        adapted, count = re.subn(r"(?m)^name:.*$", "name: " + name, original_entry.decode(), count=1)
        if count != 1:
            raise ValueError("Selected entry lacks a unique name")
        for file in source.rglob("*"):
            rel = file.relative_to(source)
            if file.is_dir():
                add_directory(prefix / rel)
            elif file.name == ".nstack-release.json" and file.parent == source:
                raw = (json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
                expected[str(prefix / "UPSTREAM-RELEASE.json")] = {"sha256": sha(raw), "mode": 0o444}
            elif file.is_file():
                digest = sha(adapted.encode()) if rel == entry else receipt["files"][str(rel)]
                expected[str(prefix / rel)] = {"sha256": digest, "mode": 0o555 if file.stat().st_mode & 0o111 else 0o444}
        expected[str(P("skills") / name)] = {"link": str(release / prefix / receipt.get("entry_dir", "."))}
    for name in addons:
        prefix = P("bundles") / name
        add_directory(prefix)
        for file in (ROOT / "addons" / name).rglob("*"):
            rel = prefix / file.relative_to(ROOT / "addons" / name)
            if file.is_symlink():
                raise ValueError("Linked addon source is not allowed")
            if file.is_dir():
                add_directory(rel)
            elif file.is_file():
                expected[str(rel)] = {"sha256": sha(file.read_bytes()), "mode": 0o555 if file.stat().st_mode & 0o111 else 0o444}
        expected[str(P("skills") / name)] = {"link": str(release / prefix)}
    raw = (json.dumps(index, sort_keys=True, indent=2) + "\n").encode()
    expected["index.json"] = {"sha256": sha(raw), "mode": 0o444}
    return expected

def prepare(state, chosen, addons):
    originals = []
    for name, s in chosen:
        release = nstack.build(s["candidate_id"], s["source_path"])
        r, _, _ = nstack.registered_release(release)
        originals.append((name, s, release, r))
    inputs = {
        "leaves": [(name, r["content_sha256"], r["builder_sha256"]) for name, _, _, r in originals],
        "addons": {name: tree(ROOT / "addons" / name) for name in addons},
        "adaptation": "full-bundle-natural-entry-v1",
    }
    digest = sha(json.dumps(inputs, sort_keys=True).encode())
    release = state / "native-releases" / digest
    index = index_rows(originals, addons, release)
    expected = expected_tree(originals, addons, release, index)
    if release.exists() or release.is_symlink():
        if release.is_symlink() or (release / "NATIVE-MANIFEST.json").is_symlink():
            raise ValueError("Native skill release changed: linked seal or release")
        seal = json.loads((release / "NATIVE-MANIFEST.json").read_text())
        if (seal["inputs"] != json.loads(json.dumps(inputs)) or seal["files"] != expected or
                tree(release) != expected or release.stat().st_mode & 0o777 != 0o555 or
                (release / "NATIVE-MANIFEST.json").stat().st_mode & 0o777 != 0o444):
            raise ValueError("Native skill release changed")
        return release, index
    release.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".native-", dir=release.parent) as temp:
        out = P(temp) / "release"
        (out / "bundles").mkdir(parents=True)
        (out / "skills").mkdir()
        for name, s, source, r in originals:
            dest = out / "bundles" / name
            shutil.copytree(source, dest)
            dest.chmod(0o755)
            entry = dest / r.get("entry_dir", ".")
            skill = entry / "SKILL.md"
            skill.chmod(0o600)
            text, count = re.subn(r"(?m)^name:.*$", "name: " + name, skill.read_text(), count=1)
            if count != 1:
                raise ValueError("Selected entry lacks a unique name")
            skill.write_text(text)
            skill.chmod(0o444)
            # Keep the original recipe receipt as provenance, not a seal on renamed bytes.
            (dest / ".nstack-release.json").rename(dest / "UPSTREAM-RELEASE.json")
            from closure import validate
            validate(dest)
            final_entry = release / "bundles" / name / r.get("entry_dir", ".")
            (out / "skills" / name).symlink_to(final_entry)
        for name in addons:
            source = ROOT / "addons" / name
            if not (source / "LICENSE").is_file():
                raise ValueError("Addon license missing")
            dest = out / "bundles" / name
            shutil.copytree(source, dest)
            (out / "skills" / name).symlink_to(release / "bundles" / name)
        atomic_json(out / "index.json", index)
        for p in out.rglob("*"):
            if not p.is_symlink():
                p.chmod(0o555 if p.is_dir() or p.stat().st_mode & 0o111 else 0o444)
        if tree(out) != expected:
            raise ValueError("Prepared native bundle differs from verified original inputs")
        atomic_json(out / "NATIVE-MANIFEST.json", {"inputs": inputs, "files": expected})
        (out / "NATIVE-MANIFEST.json").chmod(0o444)
        os.rename(out, release)
        release.chmod(0o555)
    return release, index

def knowledge_guidance(vault):
    location = f" at {vault}" if vault else " in the user's explicitly authorized vault"
    return ("Canonical knowledge uses Markdown and private local Git" + location + ". Keep source ownership, "
            "scope, stable note ID, revision/hash, event and observation dates, state, superseded generation "
            "and correction path. Reopen the owning source and reject stale or wrong-scope evidence. "
            "Use explicit vault/file targets. Keep private notes and accounts out of public Git. "
            "QMD requires an actual passage-recall need; Hindsight requires demonstrated cross-episode misses. "
            "Native automatic memory is separate from vault tests.")

def guidance(current, state, vault):
    begin, end = "<!-- nstack:start -->", "<!-- nstack:end -->"
    paragraph = (
        "Keep routine tasks native and use the project's ordinary checks. Reviewed skills are available "
        "across ordinary projects in ~/.agents/skills, with natural names and complete support files. "
        "No project-init step is required. Read the relevant complete SKILL.md and required support on demand. "
        f"If native summaries are limited, search {state / 'native-skill-index.json'} or use nstack search "
        "ARTIFACT OPERATION FAILURE. A catalog match or prepared source is not an executed operation."
    )
    if current.count(begin) != current.count(end) or current.count(begin) > 1:
        raise ValueError("Ambiguous nstack instructions")
    if begin in current:
        # Preserve the user's retained-plugin, model, runtime and knowledge instructions.
        a, b = current.index(begin), current.index(end)
        body = current[a:b]
        match = re.search(r"(?m)^Keep routine[^\n]*(?:\n(?!\n)[^\n]*)*", body)
        if not match:
            raise ValueError("Existing nstack block has no recognized native guidance paragraph")
        # Preserve an existing runtime pointer in the first paragraph.
        runtime = f" Installed specialist runtimes are indexed at {state / 'native-tools/index.json'}; use their recorded entrypoints."
        if (state / "native-tools/index.json").is_file():
            paragraph += runtime
        body = body[:match.start()] + paragraph + body[match.end():]
        # Replace only the previous generated publisher and project-record paragraphs.
        # User-owned text outside this block and newer plugin/vault choices survive.
        body = re.sub(r"(?m)^Use the project-bound publisher's activate_leaf[^\n]*\n\n", "", body)
        body = re.sub(r"(?m)^Keep source-backed, correctable knowledge in the owning project's canonical records\.[^\n]*", knowledge_guidance(vault), body)
        return current[:a] + body + current[b:]
    knowledge = (
        f"Canonical knowledge uses the authorized Markdown/Git vault at {vault}. " if vault else
        "Use only the user's explicitly authorized canonical Markdown/Git vault. "
    )
    block = f"""{begin}
## Selected toolkit

{paragraph}

Preserve model, effort, native permission controls and explicit plugin choices. Reference-only and rejected candidates are not standalone skills. Heavy runtimes stay on demand; trials and substitutes require their specific evidence. Read the actual tool help and source, keep scope, and verify the finished artifact. No new spending, API credentials or relaxed permissions follows from a skill instruction.

{knowledge}Keep source ownership, scope, stable note ID, revision/hash, event and observation dates, state, superseded generation and correction path. Reopen the owning source and reject stale or wrong-scope evidence. Use explicit vault/file targets. Keep private notes and accounts out of public Git. QMD requires an actual passage-recall need; Hindsight requires demonstrated cross-episode misses. Native automatic memory is separate from vault tests.
{end}"""
    return current.rstrip() + "\n\n" + block + "\n"

def check_parent(path):
    if path.parent.resolve() != path.parent:
        raise ValueError("Linked profile target parent: " + str(path))
    ancestor = path.parent
    while not ancestor.exists():
        ancestor = ancestor.parent
    if not ancestor.is_dir():
        raise ValueError("Profile target parent is not a directory: " + str(path))
    return ancestor

def preflight(targets, run):
    device = run.stat().st_dev
    for path, kinds in targets.items():
        ancestor = check_parent(path)
        if ancestor.stat().st_dev != device:
            raise ValueError("Profile target is on another volume: " + str(path))
        current = fingerprint(path)
        if current["kind"] not in kinds:
            raise ValueError("Unsupported profile target kind: " + str(path))
        locked = sum(getattr(stat, name, 0) for name in ("UF_IMMUTABLE", "SF_IMMUTABLE", "UF_APPEND", "SF_APPEND"))
        if current.get("metadata", {}).get("flags", 0) & locked or getattr(ancestor.stat(), "st_flags", 0) & locked:
            raise ValueError("Immutable or append-only profile target/parent: " + str(path))
        if not os.access(ancestor, os.W_OK | os.X_OK):
            raise ValueError("Profile target parent is not writable/searchable: " + str(ancestor))
        if sys.platform == "darwin":
            # Deny ACEs may forbid deletion even when access(W_OK) succeeds.
            # Reconcile these explicitly instead of changing native ACLs.
            paths = [ancestor] + ([path] if current["kind"] != "absent" else [])
            for item in paths:
                acl = subprocess.check_output(["/bin/ls", "-lde", str(item)], text=True)
                if re.search(r"(?m)^\s*\d+:.*\bdeny\b", acl):
                    raise ValueError("Profile target/parent has a native deny ACL; preserve and reconcile: " + str(item))

def apply(args):
    home = P(args.home).expanduser().resolve()
    state = P(args.state).expanduser().resolve()
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    for root in (home / ".agents/skills", home / ".codex/skills"):
        if state.is_relative_to(root.resolve()):
            raise ValueError("Private state must remain outside skill discovery")
    nstack.STATE = state
    target, agents = home / ".agents/skills", home / ".codex/AGENTS.md"
    index_path, profile = state / "native-skill-index.json", state / "native-profile.json"
    allowed = {target: {"absent", "file", "directory", "link"},
               agents: {"absent", "file"}, index_path: {"absent", "file", "link"},
               profile: {"absent", "file"}}
    preflight(allowed, state)
    if profile.is_file() and json.loads(profile.read_text()).get("home") != str(home):
        raise ValueError("Native state belongs to another home; use a separate state directory")
    chosen = selection()
    if args.only:
        names = set(args.only)
        if names - {name for name, _ in chosen}:
            raise ValueError("Unknown or non-installable selected skill name")
        chosen = [(name, s) for name, s in chosen if name in names]
    addons = [name for name, enabled in [("agent-reach", args.agent_reach), ("repository-docs", args.repository_docs)] if enabled]
    release, index = prepare(state, chosen, addons)
    check_parent(agents)
    derived_before = fingerprint(agents)
    if derived_before["kind"] not in ("absent", "file"):
        raise ValueError("AGENTS must be a regular file or absent")
    content = guidance(agents.read_text() if agents.exists() else "", state, args.vault)
    same(agents, derived_before)
    index_bytes = (json.dumps(index, sort_keys=True, indent=2) + "\n").encode()
    profile_bytes = (json.dumps({"release": str(release), "home": str(home), "names": [r["name"] for r in index]},
                                sort_keys=True, indent=2) + "\n").encode()
    desired = {agents: content.encode(), index_path: index_bytes, profile: profile_bytes}
    run = state / "runs" / ("native-" + release.name[:16])
    if fingerprint(target)["kind"] == "absent" and (run / "root-after").is_symlink() and all(
        p.is_file() and not p.is_symlink() and p.read_bytes() == data for p, data in desired.items()
    ):
        tx = Transaction(run)
        with tx.lock():
            row = next((r for r in reversed(tx.rows) if r["path"] == str(target) and r["phase"] == "applied"), None)
            if not row or row["after"].get("target") != str(release / "skills"):
                raise ValueError("Missing native skill ownership record")
            preflight(allowed, run)
            same(target, {"kind": "absent"})
            same(run / "root-after", row["after"])
            target.parent.mkdir(parents=True, exist_ok=True)
            copy(run / "root-after", target)
            same(target, row["after"])
        return {"changed": True, "repaired_removed_entry": True, "skills": len(index), "release": str(release)}
    if target.is_symlink() and os.readlink(target) == str(release / "skills") and all(
        p.is_file() and not p.is_symlink() and p.read_bytes() == data for p, data in desired.items()
    ):
        return {"changed": False, "skills": len(index), "release": str(release)}
    if (target.exists() or target.is_symlink()) and not args.replace:
        raise ValueError("Existing user skill root: inspect it, then pass --replace to back it up and replace it")
    code = profile_install.stage(state)
    run = state / "runs" / ("native-" + release.name[:16])
    run.mkdir(mode=0o700, parents=True, exist_ok=True)
    tx = Transaction(run)
    with tx.lock():
        same(agents, derived_before)
        preflight(allowed, run)
        if profile.is_file() and json.loads(profile.read_text()).get("home") != str(home):
            raise ValueError("Native state belongs to another home")
        before = {p: fingerprint(p) for p in [target, *desired]}
        before[agents] = derived_before
        for i, (p, old) in enumerate(before.items()):
            if old["kind"] != "absent":
                backup, rehearsal = run / "snapshot" / str(i), run / "rehearsal" / str(i)
                if backup.exists() or backup.is_symlink():
                    tx.preserve_attempt(backup, "snapshot")
                if rehearsal.exists() or rehearsal.is_symlink():
                    tx.preserve_attempt(rehearsal, "rehearsal")
                copy(p, backup)
                copy(backup, rehearsal)
                if fingerprint(rehearsal) != old:
                    raise ValueError("Backup restoration rehearsal differs")
        modes = {p: before[p]["metadata"]["mode"] if p == agents and before[p]["kind"] == "file" else 0o600 for p in desired}
        prepared = {p: tx.stage_file(p, data, modes[p], expected=before[p]) for p, data in desired.items()}
        pointer = state / "rollback.sh"
        helper = run / "rollback-native.sh"
        parent_file = run / "native-parent.json"
        if pointer.is_symlink() and pointer.resolve() == helper and parent_file.exists():
            previous = json.loads(parent_file.read_text())["previous"]
        elif pointer.is_symlink():
            previous_path = pointer.resolve(strict=True)
            if not previous_path.is_relative_to(state / "runs"):
                raise ValueError("Existing rollback helper is outside nstack ownership")
            previous = str(previous_path)
        elif pointer.exists():
            raise ValueError("Existing rollback command is not an owned symlink")
        else:
            previous = None
        atomic_json(parent_file, {"previous": previous, "state": str(state)})
        helper.write_text("#!/bin/sh\nset -eu\nexec " + shlex.quote(sys.executable) + " " +
                          shlex.quote(str(code / "native_setup.py")) + " rollback " + shlex.quote(str(run)) + " --chain\n")
        helper.chmod(0o700)
        # Recovery is registered before the first profile mutation.
        temp_pointer = state / ".native-rollback-next"
        if temp_pointer.exists() or temp_pointer.is_symlink():
            raise ValueError("Unexpected pending recovery pointer")
        temp_pointer.symlink_to(helper)
        os.replace(temp_pointer, pointer)
        tx.link(target, release / "skills", expected=before[target])
        for p, data in desired.items():
            tx.replace_file(p, data, modes[p], expected=before[p], prepared=prepared[p])
        after_link = run / "root-after"
        if after_link.exists() or after_link.is_symlink():
            tx.preserve_attempt(after_link, "previous-root-after")
        copy(target, after_link)
        same(after_link, fingerprint(target))
    return {"changed": True, "skills": len(index), "release": str(release), "run": str(run), "rollback": str(pointer)}

def rollback(run, chain):
    run = P(run).absolute()
    record = json.loads((run / "native-parent.json").read_text())
    tx = Transaction(run)
    with tx.lock():
        tx.rollback()
        pointer = P(record["state"]) / "rollback.sh"
        if pointer.is_symlink() and pointer.resolve() == run / "rollback-native.sh":
            if record["previous"]:
                temp = pointer.parent / ".native-rollback-previous"
                if temp.is_symlink() and os.readlink(temp) == record["previous"]:
                    pass  # Resume an interrupted, exactly owned pointer replacement.
                elif temp.exists() or temp.is_symlink():
                    raise ValueError("Unexpected previous rollback pointer; preserved")
                else:
                    temp.symlink_to(record["previous"])
                os.replace(temp, pointer)
            else:
                pointer.unlink()
    if chain and record["previous"]:
        subprocess.run([record["previous"]], check=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("install")
    a.add_argument("--state", default=str(nstack.STATE))
    a.add_argument("--home", default=str(P.home()))
    a.add_argument("--only", action="append", help="Exact natural name, for a deliberately limited install")
    a.add_argument("--replace", action="store_true")
    a.add_argument("--agent-reach", action="store_true", help="Explicitly add the separately reviewed Agent Reach skill")
    a.add_argument("--repository-docs", action="store_true")
    a.add_argument("--vault", help="Existing user-authorized vault path; does not create a vault")
    sub.add_parser("list")
    a = sub.add_parser("rollback")
    a.add_argument("run")
    a.add_argument("--chain", action="store_true")
    args = p.parse_args()
    try:
        if args.command == "list":
            print("\n".join(name for name, _ in selection()))
        elif args.command == "install":
            print(json.dumps(apply(args), indent=2))
        else:
            rollback(args.run, args.chain)
            print("Recorded native profile restored; private knowledge and project data retained.")
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        p.exit(1, str(e) + "\n")

if __name__ == "__main__":
    main()
