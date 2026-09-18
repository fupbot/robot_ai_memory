# Requirements: OKF for Robotics — Persistent Session Memory for ROS2

Working name: `okf_robotics` (placeholder — final package name TBD before publishing;
repo is currently `robot_ai_memory`, reconcile naming before Phase 3).

## Summary

Open-source ROS2 package suite giving robots and their LLM-based planners persistent,
portable, human-readable memory across sessions, built on Google Cloud's Open Knowledge
Format (OKF) — Apache-2.0, markdown + YAML frontmatter. Inspired by (not forked from)
Fabio Akita's `ai-memory` (MIT). Differentiator: existing robot-LLM memory solutions
(`bob_llm`/Qdrant, AgenticROS/JSON-mem0) are framework-locked; this is the first
portable/interoperable implementation for robotics.

## Goals

- Portfolio-grade OSS project demonstrating robotics + systems engineering.
- Fill a real, currently-unsolved gap: LLM planners in ROS lose context across
  sessions/restarts.
- Be first-to-robotics on OKF while the ecosystem is still small (~2 months old as of
  this writing).
- Simulation-first (Turtlebot + Gazebo), but designed with a path to real hardware —
  not sim-only as a permanent constraint.

## Non-goals

- Not a rosbag replacement. rosbag = what happened (raw, replayable state); OKF memory
  = what it meant (distilled, event-boundary facts). State this explicitly in the
  README to preempt "isn't this just rosbag?"
- Not real-time control software — no C++ performance case exists for the core work
  (I/O + structured text).
- Not requiring an LLM or API key to use the base package.

## License

- **Apache-2.0** for the whole project (already applied in `LICENSE`) — matches the OKF
  spec itself and is common in the ROS ecosystem.
- Explicit attribution to Fabio Akita's `ai-memory` (MIT) in the README as an
  architectural inspiration, even though no code is reused (independent
  reimplementation in a different domain — text coding sessions vs. multimodal robot
  sessions).

## rosbag boundary — design for broad, format-agnostic integration

- OKF entries **reference** raw logs rather than duplicate them (e.g., "see bag
  `run_042.mcap` at t=134.2s").
- Explicit decision: do not hard-couple to one logging format. Keep the reference
  field(s) in the schema generic enough to point at rosbag2/mcap, legacy `.bag`, or
  non-ROS log formats — the goal is broadest possible interoperability, not a
  rosbag2-specific integration.
- **Resolved (Phase 0 spec review):** OKF's own `sources` frontmatter family is the
  mechanism — each entry is `{resource, id, title, author, usage_count, last_modified}`
  where `resource` is an arbitrary URI. No custom field needed. A rosbag reference is
  just `sources: [{resource: "mcap://bags/run_042.mcap#t=134.2s"}]`; a non-ROS log is
  `sources: [{resource: "file:///var/log/planner.log#L442"}]`. Format-agnostic for
  free, because `resource` is spec'd as "a URI that uniquely identifies the underlying
  asset," not a ROS-specific type.

## Encoding approach

- **Deterministic/templated by default.** ROS events already have structure (topic
  type, fields, timestamps) — map to OKF concepts via templates, no inference needed.
- No API key/cost/latency/non-determinism required for baseline usage.
- **LLM is opt-in**, layered on top, for:
  - Turning structured events into readable prose narrative (`log.md`).
  - Memory consolidation/deduplication over time.
  - NOT for querying — the querying planner's own LLM does the reasoning; the MCP
    server just serves structured data.
- Split: capture/encode deterministically, let the querying LLM reason.

## Safety & real-time behavior

- Eventual real-hardware target raises the bar here versus a pure sim/portfolio
  project.
- **Capture node must never block or slow the control/planning loop.** Writes to OKF
  storage happen off the hot path.
- Chosen approach: **non-blocking with buffering**, not drop-on-backpressure. Events
  are enqueued (in-memory, spillable to disk if the queue grows) and flushed
  asynchronously, so no event is silently lost under load, but nothing about the
  capture path may add latency to control/planning topics.
- Revisit concrete queue depth / disk-spill thresholds / backpressure alarms once
  running against real hardware; sim-only load characteristics may not need this
  complexity initially but the interface should assume it from the start (don't design
  in a way that requires a rewrite to add buffering later).

## Language: Python

- I/O + structured text work, not real-time control — no C++ performance case.
- Matches the ecosystem it integrates with (MCP servers, `okf-toolkit`, `hermes-okf`,
  PyYAML).
- Lower contribution barrier (`rclpy` vs `rclcpp`) for an OSS project wanting outside
  contributors.
- Event-boundary-only writes (not per-tick) mean no hot-path performance pressure in
  the common case.
- Escape hatch (not built preemptively): if watching very high-frequency topics for
  trigger conditions becomes a *measured* bottleneck, consider a small C++ subscriber
  publishing a lightweight "event detected" topic for the Python OKF writer to consume.

## ROS2 distro compatibility

Researched 2026-09-16 (current data, not assumed from training knowledge — a new
distro shipped after this assistant's knowledge cutoff). ROS 2 now alternates an
LTS release (5-year support) on even years with a standard release (1.5-year support)
on odd years, per REP 2000 / each release's own platform-support page from Lyrical
onward.

| Distro | Released | EOL | Ubuntu | Python |
|---|---|---|---|---|
| Humble Hawksbill | May 2022 | May 2027 (LTS) | 22.04 | 3.10 |
| Jazzy Jalisco | May 2024 | May 2029 (LTS) | 24.04 | 3.12 |
| Kilted Kaiju | May 2025 | Nov/Dec 2026 (non-LTS) | 24.04 | 3.9+ |
| Lyrical Luth | May 2026 | May 2031 (LTS) | 26.04 (+ Windows 11 tier 1) | 3.12–3.14, adds new `rclpy` `await`-based async API |

**Decision: officially support Humble + Jazzy + Lyrical** (the three LTS releases).
Kilted is explicitly out of the CI/support matrix — it's non-LTS and reaches EOL
within ~2 months of a realistic MVP ship date, so CI investment there has poor payoff.
Revisit if a future odd-year release turns out to matter more than Kilted did.

There are two independent compatibility problems, not one:

1. **Python version spread (3.10 → 3.14).** Affects all three packages, especially
   `okf_robotics_core`/`okf_robotics_mcp` (which have zero `rclpy` dependency — see
   Package architecture). Target **Python 3.10 as the floor** (Humble's version);
   never use syntax/stdlib features newer than 3.10 in shared code (e.g. no
   `tomllib`, no 3.11+ exception groups) even though Lyrical ships 3.12–3.14.
2. **`rclpy`/nav2 API drift.** Only affects `okf_robotics_capture`. Core `rclpy`
   pub/sub/executor API has been stable since Foxy, but Lyrical adds new
   `await`-based async `rclpy` semantics, and nav2's behavior-tree XML/action
   schemas shift release to release. Mitigations:
   - Stick to the classic callback/executor `rclpy` pattern everywhere; never
     *require* Lyrical's new `await` semantics as a baseline (fine as an opt-in
     enhancement later, behind a capability check).
   - Don't hardcode nav2 topic names or message field paths — keep them in
     `config/capture_params.yaml` (see Package architecture) so a user on an
     older/newer nav2 can remap without forking code.
   - If a genuinely distro-specific difference is unavoidable, isolate it behind a
     small `_compat.py` shim rather than scattering `if ROS_DISTRO == ...` checks
     through the codebase — but the goal is to need zero such shims.

**Verification, not just claims:** a GitHub Actions CI matrix (Phase 3) using the
official `ros:<distro>-ros-base` Docker images via `ros-tooling/setup-ros` +
`ros-tooling/action-ros-ci` (the standard tooling across the ROS ecosystem), one job
per distro in {Humble, Jazzy, Lyrical}, running `colcon build && colcon test` on every
push/PR. A compatibility claim without CI proving it on all three is just a hope.
Release to each distro's rosdistro index via `bloom-release` once registered on the
ROS package index (Phase 3) — that's the actual distribution mechanism, separate from
CI.

## Search (v1)

- **Grep/ripgrep-based**, not SQLite/FTS5, for v1.
- Rationale: zero extra dependencies, fully portable, matches the "plain markdown,
  readable by `cat`" philosophy; expected event volume (event-boundary writes only) is
  low enough that grep-based search should be sufficient.
- Explicitly deferred, not ruled out: FTS5/SQLite (or similar) can be added later as an
  optional accelerator if/when volume or query patterns demand it — keep the search
  interface in `okf_robotics_core` abstracted so the backend can be swapped without
  changing callers.

## Package architecture (planned)

1. **`okf_robotics_core`** (Python library) — OKF bundle read/write, schema validation
   for robotics-specific concept types, grep-based search behind an abstracted
   interface (swappable backend later).
2. **`okf_robotics_capture`** (ROS2 node, `rclpy`) — subscribes to task/planning/
   diagnostic topics, writes structured OKF concepts on meaningful events only, via a
   non-blocking buffered writer (see Safety section).
3. **`okf_robotics_mcp`** (Python, MCP server) — exposes query/search over the OKF
   bundle so an LLM-based planner can ask "what happened last time in this
   environment."

### Workspace layout

All three packages live as sibling directories in this repo (standard ROS "meta-repo"
pattern, e.g. how `navigation2` structures `nav2_core`, `nav2_bt_navigator`, etc. as
siblings) — the repo root doubles as a colcon workspace's `src/` contents, or gets
dropped into one:

```
robot_ai_memory/
  okf_robotics_core/
  okf_robotics_capture/
  okf_robotics_mcp/
  requirements.md
  README.md
  LICENSE
```

All three are `ament_python` packages (colcon-buildable, each with its own
`package.xml`). `okf_robotics_core` declares **no `rclpy` dependency** — it's pure
Python + PyYAML — so it stays independently pip-installable/testable, and
`okf_robotics_mcp` doesn't need a sourced ROS environment just to serve queries from an
existing bundle.

### `okf_robotics_core` — pure Python library, zero ROS dependency

```
okf_robotics_core/
  package.xml, setup.py
  okf_robotics_core/
    bundle.py            # Bundle(root_path): read/write concepts, walk tree, append_log()
    concepts/
      base.py             # Concept: type/title/description/resource/tags/sources/
                           #   generated/verified/status/stale_after + body text;
                           #   to_markdown()/from_markdown()
      mission.py, task_attempt.py, replan_event.py,
      failure_note.py, environment_observation.py, param_change.py
                           # thin subclasses adding type-specific optional fields
    frontmatter.py         # YAML frontmatter parse/serialize helpers
    validator.py            # permissive validator (see conformance constraint above) —
                             #   warnings, never hard rejection, for unknown type/missing
                             #   optional fields/broken links
    links.py                 # bundle-relative link resolution + backlink graph
    search/
      base.py                # SearchBackend ABC: search(query, filters) -> [Result]
      grep_backend.py         # v1 implementation, shells out to rg/grep -r
  test/
```

Responsibility: everything that reads or writes the bundle on disk. No ROS knowledge —
it doesn't know what a "task" or "topic" is, only what a `Concept` and a `Bundle` are.
This is what makes it swappable/reusable outside ROS later if the OKF-robotics idea
generalizes.

### `okf_robotics_capture` — ROS2 node (`rclpy`), depends on `okf_robotics_core`

```
okf_robotics_capture/
  package.xml, setup.py
  launch/capture.launch.py
  config/capture_params.yaml   # topics to watch, per-trigger config
  okf_robotics_capture/
    capture_node.py             # rclpy Node: subscribes to configured topics
    triggers/
      base.py                    # EventTrigger: given a msg, decide if this is an
                                  #   event boundary (task start/end, replan, failure)
      task_lifecycle.py, replan_trigger.py, diagnostics_trigger.py
    encoders/
      base.py                     # deterministic template: ROS msg -> Concept
      mission_encoder.py, task_attempt_encoder.py,
      replan_encoder.py, failure_encoder.py
    buffer.py                     # HotMemoryBuffer: bounded in-memory queue, put()
                                   #   never blocks caller; spills to disk if full
    writer.py                      # flush-thread-only: drains buffer, calls
                                    #   okf_robotics_core.Bundle to write concepts
  test/
```

Responsibility: the only package that touches ROS topics. Message arrives → trigger
decides "is this an event boundary" → encoder builds a `Concept` deterministically →
`buffer.put()` (non-blocking) → a separate flush timer/thread drains the buffer and
calls `writer` to persist via `okf_robotics_core`, off the subscription callback path
entirely. This is the concrete implementation of the buffered-non-blocking design
already decided in the Safety section, and mirrors `hermes-okf`'s hot/cold split.

### `okf_robotics_mcp` — MCP server, depends on `okf_robotics_core`

```
okf_robotics_mcp/
  package.xml, setup.py
  okf_robotics_mcp/
    server.py                # MCP stdio server entrypoint, registers tools
    tools/
      search_bundle.py         # generic grep-search passthrough
      get_concept.py            # fetch one concept + resolved link neighbors
      graph_neighbors.py         # bounded-depth graph traversal from a concept
      environment_history.py      # walk backlinks from an Environment Observation to
                                   #   find every Mission Run/Task Attempt/Failure Note
                                   #   that references it — the demo's core query
      recent.py                    # reads log.md entries, most-recent-first
    graph.py                  # backlink index built over okf_robotics_core.Bundle
  test/
```

Responsibility: read-only query surface. No LLM reasoning happens here — it serves
structured concept data and graph relationships; the *calling* planner's LLM decides
what to do with it, per the Encoding approach split already decided.

### End-to-end flow (validates the module boundaries against the demo scenario)

1. Turtlebot nav task starts in Gazebo → nav2 accepts the goal → capture's
   `task_lifecycle` trigger fires → `task_attempt_encoder` builds a `Task Attempt`
   concept (`resource: map://gazebo_house_world`, `sources` pointing at the active
   rosbag if one is recording) → `buffer.put()` → async flush writes
   `missions/.../tasks/task-NNN.md` and appends the mission's `log.md`.
2. Task fails and nav2 replans → `diagnostics_trigger`/`replan_trigger` fires →
   `replan_encoder` builds a `Replan Event`, bundle-relative-linked back to the Task
   Attempt.
3. Mission ends → `mission.md` frontmatter flips `status: draft` → `status: stable`.
4. Next session: the *querying* LLM replanner calls `okf_robotics_mcp`'s
   `environment_history(resource="map://gazebo_house_world")` → `graph.py` finds
   `environments/gazebo_house_world.md`, follows backlinks, gathers linked Task
   Attempts/Replan Events/Failure Notes → returns them to the calling LLM, which
   reasons over the history and adjusts its plan. `okf_robotics_mcp` never itself
   invokes an LLM.

## Schema design notes

Based on reviewing the canonical spec (`GoogleCloudPlatform/open-knowledge-format`,
current version **v0.2**) and two existing implementations, `okf-agent-memory` (Go,
targets coding agents) and `hermes-okf` (Python, targets the Hermes agent). Full spec
facts: bundle = directory tree of `.md` files with YAML frontmatter; only `type` is
required; reserved filenames `index.md` (directory listing) and `log.md` (chronological
history, newest first, ISO date headings) must not be used for concept docs; consumers
**must tolerate** unknown `type` values, missing optional fields, and broken links — no
central schema registry, by design.

### Concept type mapping (OKF convention → ROS meaning)

| OKF convention | ROS mapping | Why |
|---|---|---|
| `type` (free-form, required) | New types: `Mission Run`, `Task Attempt`, `Replan Event`, `Failure/Recovery Note`, `Environment Observation`, `Param/Planner Change` | Spec forbids rejecting unknown types — no registry needed |
| `resource` (URI to the real asset) | e.g. `map://gazebo_house_world`, `topic://nav2/behavior_tree` | Anchors a concept doc to an actual ROS entity |
| `sources` (provenance list) | rosbag/log references — see rosbag boundary section above | Format-agnostic by construction |
| `generated: {by, at}` | `by: okf_robotics_capture/<version>` for templated writes; `by: process:okf-narrator-llm` for LLM prose | Matches the deterministic-capture/LLM-opt-in split |
| `verified: [{by, at}]` | Human operator annotates a `Failure Note` afterward → `by: human:<id>` | Promotes trust tier (unverified → machine-confirmed → human-reviewed); signal for the querying LLM to weight |
| `status: draft/stable/deprecated` | `draft` while a mission is in progress, `stable` once closed | Doubles as a crash-recovery signal — an unflushed/interrupted mission simply stays `draft` |
| `stale_after` | Environment Observations expire (e.g. "corridor was clear" shouldn't be trusted indefinitely) | Cheap staleness filter without embeddings |
| Actor convention (`<producer>/<version>`, `human:<id>`, `process:<id>`) | Drop-in fit for ROS node/package identity and human operator IDs | No adaptation needed |
| Per-directory `index.md`/`log.md` | One `log.md` per mission subdirectory plus a bundle-root one | Matches "write at event boundaries only" |
| Bundle-relative cross-links | Task Attempt → Environment Observation → prior Mission Run in the same environment | This graph traversal *is* the "what happened last time here" query |
| `code_refs` (an `okf-agent-memory` extension, not core spec) | ROS analog `config_refs`: bind a Param Change/Replan Event to the exact `nav2_params.yaml` or behavior-tree XML active at the time | Precedent for binding a decision to a config artifact |
| Attested Computation type (`runtime`, `executor`, `attester`) | Stretch/future idea only: record a Task Attempt as a reproducible computation for replay | Not needed for MVP — flag as a possible v2 idea |

### Prior art directly validating earlier decisions

- `hermes-okf`'s "hot buffer + async flush to bundle" two-memory model independently
  validates the non-blocking buffered capture design (see Safety section) — same
  pattern, built for the same reason (writer must not block the hot path).
- `hermes-okf`'s session naming (`2026-06-14T22-14-58Z`, Windows-safe ISO 8601) is
  reused verbatim for `missions/<timestamp>-<slug>/` directory names — avoids collisions
  across concurrent runs.
- `okf-agent-memory` uses in-memory BM25 + an embedded MCP server; this project
  deliberately chose grep instead (see Search section) — an intentional
  portability-over-power tradeoff, worth a one-line README callout since a reviewer
  familiar with `okf-agent-memory` may otherwise read it as an oversight.

### Proposed bundle layout

```
missions/2026-09-16T14-30-00Z-nav_loop_demo/
  mission.md          # type: Mission Run
  log.md
  tasks/
    task-001.md        # type: Task Attempt
  events/
    replan-001.md       # type: Replan Event
    failure-001.md       # type: Failure/Recovery Note
environments/
  gazebo_house_world.md  # type: Environment Observation — accumulates across missions
params/
  nav2_params_v3.md      # type: Param/Planner Change
```

Mirrors `okf-agent-memory`'s domain-folder pattern (`project/`, `architecture/`,
`roadmap/`) combined with `hermes-okf`'s session-timestamp pattern.

### Implementation constraint from the conformance rules

`okf_robotics_core`'s validator must be **permissive by construction** — it must not
reject a bundle for unknown `type` values, missing optional frontmatter, or broken
cross-links. This is a spec requirement, not a style choice.

## Demo scenario (north star)

- **Turtlebot + Gazebo**, with an LLM replanner performing repeated navigation tasks
  that visibly improves using past-session memory. Every scope decision in Phase 0–2
  should be evaluated against whether it serves this scenario.
- Sim-first, but capture-node design (see Safety) should not preclude later running the
  same package against a real Turtlebot or similar platform.

## Implementation plan (phased)

**Phase 0 — Validate (2–3 days)**
- [x] Read the actual OKF spec closely. Canonical home has moved to
      `GoogleCloudPlatform/open-knowledge-format` (the `knowledge-catalog` repo's
      `okf/` subdirectory referenced in the original brief now points there). **Pinned
      version: v0.2.**
- [x] Review `okf-agent-memory` / `hermes-okf` source for conventions to match — see
      Schema design notes above.
- Confirm demo scenario: Turtlebot + Gazebo + LLM replanner (decided above).

**Phase 1 — Schema design (1 week)**
- [x] Define session/concept types (see Schema design notes).
- [ ] Explicitly document the rosbag boundary (reference, don't duplicate) in README.
- [x] Sketch the 3-package structure before writing code (see Package architecture →
      Workspace layout / per-package module sketches above).

**Phase 2 — Build MVP (3–4 weeks)**
- [x] Build `okf_robotics_core` — implemented and verified (manual check standing in
      for `pytest`, which isn't installed in the dev sandbox; real `pytest` files
      exist but haven't been run by `pytest` itself yet).
- [x] Build `okf_robotics_capture` — implemented; everything except `capture_node.py`
      itself is verified (no `rclpy` in this sandbox), including a full simulated
      mission through the real trigger→encoder→buffer→writer pipeline.
- [x] Build `okf_robotics_mcp` — implemented; everything except `server.py` itself is
      verified (no `mcp` SDK in this sandbox). `server.py` guards against the SDK's
      v1→v2 `FastMCP`→`MCPServer` rename (July 2026) with a try/except import shim.
- [ ] Wire up the Turtlebot + Gazebo demo scenario end-to-end in a real ROS2
      environment; get a screen-recordable result. Requires an actual ROS2 install —
      not yet done.
- [ ] Unit test suites (`pytest`) for `okf_robotics_capture` and `okf_robotics_mcp` —
      deferred to the end per explicit instruction; `okf_robotics_core`'s test files
      already exist.

**Phase 3 — Make it adoptable (1–2 weeks)**
- README: 30-second problem statement + copy-pasteable quick start + rosbag-boundary
  explanation + `ai-memory` attribution.
- `ros2 launch` example, not just library usage.
- Apache-2.0 LICENSE (done), CONTRIBUTING.md, issue templates, CHANGELOG.
- Working `package.xml`, buildable via `colcon`.
- GitHub Actions CI: matrix across Humble + Jazzy + Lyrical using `ros:<distro>-ros-base`
  images via `ros-tooling/setup-ros` + `ros-tooling/action-ros-ci`, `colcon build`
  + `colcon test` per distro (see ROS2 distro compatibility section) — ROS users check
  for this before trusting a package.
- Register on ROS package index once stable.
- Resolve final package name (currently placeholder `okf_robotics`; repo is
  `robot_ai_memory`).

**Phase 4 — Share it (in this order)**
1. ROS Discourse (discourse.ros.org) — post once a working demo exists.
2. OKF spec's own GitHub Discussions/issues.
3. ROS Index / awesome-ros lists.
4. r/ROS, r/robotics.
5. Short demo video/GIF alongside all of the above.

## Key messaging for README / pitch

Lead with **"Portable vs. proprietary."** Existing robot-LLM memory solutions are
framework-locked; this treats robot mission memory as interoperable data (plain
markdown+YAML, git-diffable, readable by `cat`, portable to any OKF-compatible tool)
rather than an implementation detail of one agent stack.

## Open items / decisions still needed

- [x] Read OKF spec and pin version — **v0.2**, canonical repo is now
      `GoogleCloudPlatform/open-knowledge-format`.
- [x] Review `okf-agent-memory` / `hermes-okf` conventions — see Schema design notes.
- [x] Shape of the rosbag/log reference field — resolved: use OKF's own `sources`
      family, no custom field needed.
- [x] ROS2 distro compatibility strategy — resolved: officially support Humble + Jazzy
      + Lyrical (LTS releases only, Kilted excluded as near-EOL non-LTS); Python 3.10
      floor; CI matrix proves it. See ROS2 distro compatibility section.
- [ ] Final package name (`okf_robotics` vs. reconciling with repo name
      `robot_ai_memory`).
- [ ] Concrete buffered-writer parameters (queue depth, disk-spill threshold,
      backpressure signaling) — revisit once real-hardware testing is in scope.
- [ ] Finalize concept-type field lists per type (e.g. does `Task Attempt` need a
      `duration`/`outcome` field beyond the generic OKF ones?) — next schema pass.
- [ ] Decide whether `config_refs` is its own top-level frontmatter family or nested
      under `sources`.
