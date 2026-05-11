---
description: "Cross-cutting Mural seeding conventions: duplicate-then-populate, source-artifact-to-area binding, anchor inheritance, probe-before-bulk, layout primitives applied across DT, RAI, and UX/UI workflows."
applyTo: '**/.github/agents/design-thinking/dt-coach.agent.md, **/.github/agents/rai-planning/rai-planner.agent.md, **/.github/agents/project-planning/ux-ui-designer.agent.md'
---

## Mural Seeding Patterns

These conventions apply when an agent seeds a Mural board from a source artifact (DT method outputs, RAI Phase 2 packs, UX research notes). Workflow-specific contracts (cardinality assertions, A1/A2/A3 wedge bindings, journey-stage decompositions) live in the consuming agent. This file holds only the patterns that recur across every seeding workflow.

The skill is content-agnostic transport. An under-populated board surfaces as a missing agent-side decomposition rule, not a missing skill guard rail. See [mural-writeback-hygiene.instructions.md](mural-writeback-hygiene.instructions.md) for stable channel rules and [mural-human-record.instructions.md](mural-human-record.instructions.md) for the durable-record stance.

## Duplicate-then-Populate

When the user supplies a source board id, prefer `mural mural duplicate` or `mural template instantiate` over `mural mural create`. The user calling a board "the template" almost always means duplicate it literally so its anchors, frames, and area definitions carry forward. Coordinate fabrication is the failure mode this pattern exists to prevent.

```text
seed_request.has(source_mural)  -> mural mural duplicate
seed_request.has(template_id)   -> mural template instantiate
neither                         -> mural mural create  (last resort)
```

## Source-Artifact-to-Area Binding

Each seed run binds one named source artifact to one named area, and one source row produces one widget. The agent owns the binding map (which document, which section, which target area). The skill never invents bindings.

Workflow-specific binding tables (RAI A1 / A2 / A3 wedges, UX JTBD / Journey Stages / Pain Points / Opportunities / Accessibility, DT Method N output blocks) live in the consuming agent file, not here.

## Anchor Inheritance

When the source board ships per-area placeholder widgets, do not invent `(x, y)`, `(width, height)`, or `style.backgroundColor` for seeded stickies. Pair seeded stickies to placeholder anchors by reading order `(y, x)`, copy geometry and fill, PATCH via `mural widget update-bulk`, then `mural widget delete` only the anchors that were consumed.

```text
anchors = sort(placeholders, by=(y, x))
seeds   = sort(new_stickies, by=author_order)
for a, s in zip(anchors, seeds): patch(s, geometry=a, fill=a.style.backgroundColor)
delete(consumed_anchor_ids)
```

## Probe-before-Bulk

Author a one-widget probe payload bound to the target area and verify `areaChain` is non-empty via `mural widget get-with-context` before bulk-populating. An empty `areaChain` is a hard stop: surface the failure with the area id and parent ids observed, do not bulk-populate into an unbound area.

A clean probe also confirms the chosen `parentId` resolves to the intended area title, not a sibling frame with a similar name.

## Layout-Primitive Enforcement

Sibling placement uses `mural layout grid`, `mural layout row`, `mural layout cluster`, or `mural layout column`. Raw `(x, y)` integer literals on widget payloads are forbidden under any condition outside the Anchor Inheritance pattern above (where coordinates are copied, never authored).

If a layout primitive cannot express the intended arrangement, escalate to a new layout verb in the skill, not to inline coordinates.

## 404 Recovery

Treat HTTP 404 from any `mural` CLI verb as a re-read-SKILL.md trigger, not a drop-down-a-layer trigger. The verb name, argument shape, or required scope is wrong, and the fix lives in [SKILL.md](../../skills/experimental/mural/SKILL.md).

Do not import private skill helpers (`_authenticated_request`, `_merge_tags`, `_resolve_area_id`, etc.) into operator code. Private helpers are not a stable surface and any reach-around is treated as a regression in the consuming agent.

## Reserved Tag Manifest

Every seeded widget carries `authored-by-ai` (the Pattern C reserved author tag from [mural-writeback-hygiene.instructions.md](mural-writeback-hygiene.instructions.md)) plus exactly one workflow lineage tag from the manifest below. Tags are re-applied defensively on every seed run via `mural tag create` and `mural widget update-bulk` because workspace state may have drifted since the last invocation.

| Workflow                  | Lineage tag     | Set by                    |
|---------------------------|-----------------|---------------------------|
| RAI Phase 2 board seeding | `rai-phase2`    | `rai-planner.agent.md`    |
| DT Method N export        | `dt-method-{N}` | `dt-coach.agent.md`       |
| UX research bootstrap     | `ux-research`   | `ux-ui-designer.agent.md` |

Workflow tags must respect the 25-character cap from [mural-writing-style.instructions.md](mural-writing-style.instructions.md). Substitute the concrete value for `{N}` at seed time.

## Participating Workflows

Three agents pull these conventions via the `applyTo` glob in this file's frontmatter. Each agent owns its own decomposition rules and cardinality contracts, then references this file with `#file:` for the cross-cutting patterns above.

| Customization file                                                               | Workflow            | Inline contract owned by the customization                                           |
|----------------------------------------------------------------------------------|---------------------|--------------------------------------------------------------------------------------|
| [dt-coach.agent.md](../../../agents/design-thinking/dt-coach.agent.md)              | DT board export     | Per-method binding map; trigger milestones for Methods 1/3/4/5/6                     |
| [rai-planner.agent.md](../../../agents/rai-planning/rai-planner.agent.md)           | RAI Phase 2 seeding | A1 / A2 / A3 wedge bindings; per-area cardinality assertion; `state.json` write-back |
| [ux-ui-designer.agent.md](../../../agents/project-planning/ux-ui-designer.agent.md) | UX research seeding | JTBD / Journey / Pain / Opportunity / Accessibility decomposition                    |
