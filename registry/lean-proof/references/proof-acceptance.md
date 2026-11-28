# Accept a finished Lean proof

Write down the intended statement independently of the proposed proof. Check the types, quantifiers, units and side conditions against the original claim. A formal proof about natural numbers may leave the corresponding claim about integers open.

Build the named module in the project's pinned Lake environment. On a Stack+ Mac, `stack+ tools lake` gives the launcher, normally `nstack-extra lake`. In the examples below, substitute that launcher for `lake` when needed.

## Check the claim and its assumptions

Keep a small acceptance file outside the proof module. Import the compiled module and use its exported theorem at the independently written type. Inspect the target theorem's transitive axiom dependencies. For example, for an axiom-free scheduling identity:

```lean
import Schedule

example (start duration : Nat) :
    start + duration + duration = start + 2 * duration :=
  Schedule.finish_after_two_steps start duration

/-- info: 'Schedule.finish_after_two_steps' does not depend on any axioms -/
#guard_msgs in
#print axioms Schedule.finish_after_two_steps
```

Run `lake build Schedule` followed by `lake env lean Acceptance.lean`. The example rejects a weakened claim. The message check rejects a proof that relies on a placeholder, even through an imported lemma. For a theorem using standard axioms such as `propext`, record the reviewed expected list for that theorem. Treat unexpected dependencies, including `sorryAx` or a newly introduced premise, as an unfinished handoff. Run `lake env leanchecker Schedule` when replaying the compiled declarations in Lean's kernel would add assurance.

## Independent kernel check

For a consequential result, the tested Lean 4.36 toolchain also provides the external Rust checker Nanoda. Export the named declaration and its dependencies from the same build:

```sh
lake env leanexport Schedule -- Schedule.finish_after_two_steps > proof.ndjson
```

For the axiom-free example, save this policy as `nanoda.json`:

```json
{"use_stdin":true,"permitted_axioms":[],"unpermitted_axiom_hard_error":true,"nat_extension":true,"string_extension":true,"print_success_message":true,"pp_declars":["Schedule.finish_after_two_steps"],"pp_to_stdout":true}
```

Run `lake env nanoda_bin nanoda.json < proof.ndjson`. Check the exit status, the printed target declaration and type, and the count of verified declarations. An empty or wrong export cannot establish the target. Use the project's reviewed axiom policy and a checker compatible with its pinned toolchain. Preserve the statement, policy and commands with the proof. A verified model still needs evidence for assumptions about the world it describes.

[Lean axiom dependencies](https://lean-lang.org/doc/reference/latest/Axioms/) · [Lean exporter](https://github.com/leanprover/lean4export) · [Nanoda](https://github.com/ammkrn/nanoda_lib)
