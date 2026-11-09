# Creative and visual acceptance fixtures

This is an original portable fixture specification for the registry's references
to `creative_decisions.md`. It contains no private research report or prior test
results. It does not change any admission, pin, trial condition, asset grant or
user choice. A listed test is unrun until an actual target receipt establishes
otherwise. The component's additional acceptance checks remain controlling.

For each applicable lane, retain editable source, exact source/runtime versions,
dependency and asset hashes, parameters, seed, producing commands, raw evidence
and a reopened current export. Change one input and regenerate into a new output
directory. Reject the old input hash while preserving its accepted artifacts.
Use an independent comparator and a deliberately wrong input/output that must
fail. Visual review uses the supplied brief and product identity.

| Component | Small, reproducible task | Independent check and negative control |
|---|---|---|
| P203 Storybook | Build a local counter component with keyboard increment and a disabled state; retain stories and interaction tests. | Use the actual browser to increment twice and verify visible text and disabled behavior. A deliberately broken handler must fail; reopen the built static story. |
| P213 OpenPencil | In a disposable offline document, create two labeled vector shapes, one connector and a named color token. Export native source and SVG. | Reopen source and export, inspect label/connector geometry and editability; change one token and verify both affected shapes. A missing font or connector is a failure. Remains a trial. |
| P218 Manim | Animate a dot along x(t)=t, y(t)=t squared for t from 0 to 2, with explicit axes and units. | Decode the actual video, compare known positions at selected frame times and inspect labels against the mathematical source. An incorrect square or shifted frame must fail. Keep scene source. |
| P219 Motion | Animate a local disclosure panel with open, closed and reduced-motion states. | Operate it in the actual browser, check accessibility state/focus and final geometry; reduced motion must preserve meaning. A stale state or clipped panel fails. |
| P221 GSAP | Build a seekable two-second local timeline moving a square between declared coordinates with linear easing. | Seek repeatedly to 0, 0.5, 1 and 2 seconds; compare computed transforms with analytic positions and current screenshots. Scrub backward and repeat. Deliberate easing or timing drift fails. |
| P226 Remotion expertise | Use an eligible pinned Remotion project for a two-second, fixed-frame-rate composition with a frame-indexed cue. | Fully decode the actual export; count frames, locate the cue and compare source frame numbers. Change the cue by six frames and rerender. Retain the editable project and matching package locks. |
| P227 ManimGX | Render the P218 scene on its supported target and compare it with the ordinary compatible baseline. | Match source, resolution and frames; inspect positions, output parity and actual timing/resource measurements. A speed claim without parity or matched work fails. Remains a trial. |
| P265 ComfyUI | Run a small saved local graph with explicit rights-cleared checkpoint, seed, dimensions and output path. | Verify every node/model/asset hash, reopen the produced image, rerun with the same inputs and record actual determinism limits; change one declared input. A missing or silently substituted checkpoint fails. No auto-download is implied. |
| P274 Krita diffusion | In a disposable layered painting, modify only a named masked layer using an explicitly licensed local backend. | Reopen the current KRA and exported raster; compare protected layers/mask boundaries pixelwise and inspect the edit against the brief. An altered protected layer fails. Retain graph/model locks. |
| P282 Supervision | Generate two short sequences with known moving boxes and stable synthetic identities; produce annotated frames and tabular detections. | Compare every box, timestamp and identity with the generator's ground truth, including an empty frame and boundary crossing. Swapped IDs or off-by-one coordinates fail. |
| P286 Babylon.js | Make a local scene with one movable object, a collision boundary and a saved initial camera. | Run the actual target browser, apply deterministic inputs and compare resulting transforms/collision state; reopen source and current screenshot. Passing through the boundary fails. |
| P290 Unity MCP | In a disposable compatible Unity project, create one named object, modify a component and save the scene through the bounded bridge. | Independently reopen the actual scene and compare object/component values, then undo the recorded change. A tool success without a saved scene fails. Remains a trial; no production project is used. |
| L064 FAISS | Index explicit float vectors [0,0], [1,0], [0,2] using the declared distance metric, save and reload the index. | Compare neighbor IDs and distances with a direct exhaustive calculation; distinguish Euclidean from squared L2. Change one vector and rebuild; a stale index or wrong metric fails. |
| L067 SAM3 | On a small original set of simple scenes, define target masks and prompts before inference; use only an eligible fixed checkpoint. | Compare masks against independently labeled ground truth and an existing simpler method using declared IoU/error criteria, including absent-object and distractor cases. Record misses rather than treating a plausible mask as truth. Remains a trial. |
| L068 DINOv3 | Use a small original image set with declared transformations and a frozen feature extraction/retrieval protocol. | Verify input/weight hashes, finite output dimensions, cold-reload parity and retrieval against a direct distance calculation and held-out labeled baseline. Keep accuracy separate from plumbing. A changed checkpoint or leaked split fails. Remains a trial. |
| L092 LatentSync | Use an original non-identifying animated mouth and original synthetic sound, with explicit asset/model rights and known timing. | Inspect actual decoded frames against the known sound timeline and compare with the strongest existing alignment route on identical inputs. Retain source and actual synchronization errors. No person, face or voice is cloned. Remains a trial. |

Trial and substitute targets cannot be enabled through these descriptions alone.
Their registered conditions and per-ID verifier must be satisfied first. If the
platform, official application, model terms or target is unavailable, record the
precise prerequisite and keep the lane conditional.

For unlisted or excluded discovery records, this specification grants no
executable route. Consult the owning primary source and preserve its excluded
or reference-only status; do not infer admission from a shared method name.
