# RAEA local GPU rendering

Add the optional --raea flag to the same complete native selection you already
use. It adds one naturally named specialist shared by Codex and OpenCode.
It does not install upstream hooks, MCPs, background services or audio models.

The separate runtime uses official RAEA 0.1.0 for Apple Silicon macOS, pinned to
source d6f41c605ab71275162050cd08632cb56bd00e8a and the matching Apache-2.0
skill support c507860150995eb7c22ef9db23dee636c832428a. The installer verifies
the archive digest, GitHub build attestation and complete extracted payload.
The engine remains outside this MIT repository under its own FSL license.

From a checkout:

    python3 recipes/raea.py install
    python3 recipes/raea.py run --offline --source /approved/project/edit.tsx --outdir /owned/fresh/render --width 640 --height 360 --fps 30 --frames 60

Outside the checkout, use the absolute recipe recorded in the installed skill's
SOURCE.json or native-tools index. It needs existing GitHub CLI, FFmpeg and
FFprobe; it does not acquire credentials. Installation downloads about316 MB
and occupies about1.2 GB. Matching support files are retained with the runtime.

Rendering uses an isolated HOME, strips provider/proxy credentials, disables
audio auto-setup and enables the engine's offline mode. These are application
controls, not an operating-system sandbox. Inspect approved source and assets
before execution. Source guidance cannot authorize global setup, paid providers
or access to private accounts.

The wrapper preflights exactly one TSX composition through the matching SDK.
Its declared dimensions, rate and frame count must match the request before
video rendering starts, because this engine version lets source composition
metadata override its CLI flags. HTML is outside this checked lane.

The tested lane is a local 2D TSX animation to H264, with a complete frame
manifest and independently decoded PNG previews. The recipe checks dimensions,
rate, frame count, duration, decode errors and known GPU failure signals.
Its success status still requires visual inspection of current output.

This release predates an upstream GPU-error reporting fix. Artifact checks
reject known incomplete or false-success output; they cannot prove that every
possible missing object was detected. Native 3D, games, audio synthesis and
additional formats remain task-specific capabilities requiring their own proof.
No general speedup is claimed from one small render. Keep an existing suitable
renderer and editable project when changing engines would not improve the task.

Sources: [engine and license](https://github.com/shinyobjectz/raea/tree/d6f41c605ab71275162050cd08632cb56bd00e8a),
[release](https://github.com/shinyobjectz/raea/releases/tag/v0.1.0),
[matching support](https://github.com/shinyobjectz/raea-skills/tree/c507860150995eb7c22ef9db23dee636c832428a).
