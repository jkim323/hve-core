---
title: "Transparency Note: HVE Core (May 2026)"
description: "Public Transparency Note for HVE Core, a prompt-engineering and agentic-customization framework distributed by microsoft/hve-core."
author: HVE Core RAI Reviewers
ms.date: 2026-05-14
ms.topic: overview
keywords:
  - responsible-ai
  - rai
  - transparency-note
  - hve-core
  - copilot
estimated_reading_time: 18
---
## Overview

| Field          | Value                                                                                                                                              |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| System         | HVE Core (microsoft/hve-core)                                                                                                                      |
| Document type  | Transparency Note                                                                                                                                  |
| Cycle          | May 2026                                                                                                                                           |
| Companion docs | [Review Summary](docs/planning/rai/hve-core-2026-05/rai-review-summary.md), [Backlog Handoff](docs/planning/rai/hve-core-2026-05/rai-backlog-handoff.md) |
| Last updated   | 2026-05-14                                                                                                                                         |

## What is a Transparency Note?

A Transparency Note explains how an AI-related system works, the choices its maintainers made that influence its behavior, and the limitations users should consider when deciding whether and how to adopt it. It is intended to help adopters understand what the system can and cannot reasonably be expected to do, where human oversight is required, and how to use it responsibly.

This Transparency Note covers HVE Core (the contents of the `microsoft/hve-core` repository). It does not cover the underlying inference platforms that consume HVE Core artifacts (GitHub Copilot Chat in Visual Studio Code, GitHub Copilot CLI, Microsoft Foundry, and any third-party LLM hosts), each of which carries its own documentation and Transparency Note where applicable.

## The basics of HVE Core

### Introduction

HVE Core is a static corpus of prompt-engineering and agentic-customization artifacts: custom agents, prompts, instructions, skills, collections, PowerShell scripts, GitHub Actions workflows, and a Visual Studio Code extension. Its purpose is to give engineering teams a curated, governance-aware starting point for AI-assisted software work that runs on top of GitHub Copilot.

HVE Core does not train models, does not host inference, does not call external services at runtime, and does not process personally identifiable information within its own boundaries. Inference happens entirely on the host platform (GitHub Copilot Chat or GitHub Copilot CLI). HVE Core's Responsible AI exposure is concentrated in three areas:

1. What the artifacts say to and about the downstream model that the host platform invokes.
2. The trust adopters place in artifacts that carry Microsoft branding through the `microsoft/hve-core` repository and the official Visual Studio Code extension.
3. The persistent memory layer and the customer-handoff workflows that some agents orchestrate.

This Transparency Note describes the system at the level of the umbrella repository. Per-agent appendices at the end of this document add specifics for the highest-impact governance-bearing agents and the one direct generative-AI touchpoint (the Customer Card Render skill).

### Key terms

| Term                 | Meaning in HVE Core                                                                                                                                                                                  |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Artifact             | A static file shipped by HVE Core: agent definition, prompt, instructions, skill, collection, script, or workflow. Artifacts are consumed by downstream tooling; they do not execute on their own.   |
| Custom agent         | A persona definition (`*.agent.md`) that GitHub Copilot Chat can adopt to perform a specialized workflow. Custom agents may invoke subagents and reference instructions, prompts, and skills.      |
| Prompt               | A reusable user-message template (`*.prompt.md`) intended to be loaded into a Copilot Chat or CLI session.                                                                                         |
| Instructions         | Behavioral guidance (`*.instructions.md`) that an agent or session loads to shape the model's responses for a given file scope, language, or workflow.                                             |
| Skill                | A self-contained capability package (`SKILL.md` plus optional scripts and references) that documents a reusable domain capability.                                                                 |
| Collection           | A bundled set of artifacts (`*.collection.yml` plus a companion markdown description) that a publisher can install as a unit through one of the distribution channels.                             |
| Subagent             | A custom agent invoked by another agent for a focused task (typical examples: a researcher subagent for read-only investigation, an implementer subagent for a single phase of work).                |
| Distribution channel | One of six routes by which HVE Core artifacts reach an adopter: VS Code extension, npm package, GitHub plugin marketplace, direct git clone, internal Microsoft mirror, customer-handoff repository. |
| Host platform        | The Copilot surface that performs the actual inference: GitHub Copilot Chat in Visual Studio Code, or GitHub Copilot CLI. HVE Core does not include or replace this platform.                        |
| Memory layer         | The persistent notes feature exposed by the host platform. HVE Core agents may write user-scope, session-scope, or repository-scope memory. Storage and retention are controlled by the host.        |
| Governance-bearing   | An adjective applied to agents whose outputs influence downstream decisions in a binding-by-default way (planning agents, code-review agents that gate pull requests, customer-handoff agents).      |

## Capabilities

### System behavior

HVE Core ships static text artifacts and supporting tooling. When an adopter loads an HVE Core artifact into the host platform, three things happen:

1. The host platform reads the artifact contents into its session context.
2. The user interacts with the host platform's model, which is shaped by the artifact's instructions.
3. The model's responses are returned to the user through the host platform's standard surface.

HVE Core itself has no inference runtime, no API endpoints, no external network calls during artifact authoring or distribution, and no telemetry pipeline. Validation tooling (linters, frontmatter checks, Pester tests, plugin generation) runs in CI on pull requests; nothing runs on adopter machines unless the adopter explicitly invokes a packaged script or installs the Visual Studio Code extension.

A small set of artifacts crosses the boundary into direct generative output:

* The **Customer Card Render** skill drives a synthetic-persona slide-rendering pipeline that uses image generation. This is the only direct generative-AI touchpoint that ships in HVE Core. Because the output is synthetic media depicting people-like figures, the skill enforces a low-fidelity visual style and is documented separately in Appendix 5 alongside its AI-disclosure, redaction, and stereotyping-review controls.
* The **PowerPoint Builder** and **TTS Voice-over** experimental skills produce slide decks and voice audio from authored YAML, but they do not generate likenesses of people or claim to be the speaker; they are conventional content-assembly tools that consume model output authored elsewhere.

#### Responsibility boundary

| Aspect                         | HVE Core (microsoft/hve-core)                                              | Host platform (Copilot Chat or CLI)                                            |
| ------------------------------ | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Inference                      | None                                                                       | All inference happens here                                                     |
| Model selection and management | Recommends models in artifact frontmatter; cannot enforce a model choice   | Selects, hosts, and operates the model                                         |
| Safety classifiers             | None                                                                       | Provides input and output classification, jailbreak detection, content filters |
| User authentication            | None                                                                       | Manages identity, tenant scope, and access controls                            |
| Telemetry and feedback         | None at the artifact level; CI logs only                                   | Collects user interaction telemetry per the host's privacy statement           |
| Persistent memory              | Authors agents that write to memory; does not store memory itself          | Stores, retains, and exposes the memory layer                                  |
| Attribution                    | Embeds "Brought to you by microsoft/hve-core" attribution where convention | Surfaces attribution to the user through the chat session                      |

### Use cases

#### Intended uses

HVE Core is designed to be adopted in these scenarios:

* **Engineering productivity scaffolding for Microsoft engineers and field teams.** Agents and prompts that codify common engineering workflows (research, planning, implementation, review, discovery) reduce the activation cost of starting a new task with Copilot.
* **Coding-standards enforcement through Copilot.** Per-language instruction files and code-review agents bring consistent guidance into Copilot sessions when adopters work in C#, Python, PowerShell, Rust, Bash, Bicep, Terraform, or related ecosystems.
* **Governance-aware planning support.** The RAI Planner, Security Planner, and SSSC Planner agents help teams structure assessments aligned with the NIST AI RMF, STRIDE, and the OpenSSF Scorecard family. The agents produce drafts; qualified humans must review and validate every output.
* **Backlog management assistance for Azure DevOps, GitHub Issues, and Jira.** Agents can search, draft, triage, and prepare backlog updates for human review and approval.
* **Design Thinking facilitation in customer engagements.** Coaching agents support a structured Design Thinking workflow; the Customer Card Render skill produces synthetic personas for stakeholder communication subject to the constraints in Appendix 5.
* **Project planning artifacts.** Agents help draft architecture decision records, business requirements documents, product requirements documents, user journeys, and architecture diagrams for human refinement.
* **Documentation operations.** Agents help maintain documentation coverage, validate links, and apply consistent style across markdown files.

#### Considerations when choosing other use cases

HVE Core is a static artifact corpus, not a managed service. Adopters retain full responsibility for the inference platform, the data that flows through it, and the consequences of any actions taken by humans on the basis of agent output. Adopters should not use HVE Core artifacts in any of the following ways without independent design, validation, and human oversight:

* **Customer-facing chat surfaces.** No HVE Core agent is engineered, evaluated, or rated for direct end-user exposure. Agents are tooling for the engineer or analyst at the keyboard.
* **Autonomous decisions in regulated domains.** Recommendations from any HVE Core agent are advisory. Use in financial, medical, legal, employment, education, housing, insurance, or other regulated decisions without qualified human review is not supported.
* **Inference of personal attributes.** Agents and prompts must not be repurposed to infer protected characteristics of individuals from incidental data.
* **Surveillance.** HVE Core artifacts must not be used to monitor individuals without their knowledge and consent in jurisdictions that require it.
* **Synthetic media of real people without disclosure.** The Customer Card Render skill produces synthetic personas only and enforces a low-fidelity style. It must not be reconfigured to render likenesses of identifiable individuals or to omit the synthetic-media disclosure.
* **Jailbreak or guardrail evasion.** Artifacts must not be modified to suppress the host platform's safety controls.
* **High-stakes automated determinations.** Agent outputs are not calibrated for use as the sole basis of any decision with significant consequences for an individual.
* **Use on unsupported clients.** HVE Core is engineered for current GitHub Copilot Chat in Visual Studio Code and the GitHub Copilot CLI. Behavior on other clients, on outdated versions, or on third-party LLM hosts is not characterized.

Legal and regulatory considerations: organizations must evaluate their own legal and regulatory obligations before using AI-related tooling. AI services may not be appropriate in all scenarios and must comply with applicable laws and the terms of service of the host platform.

## Limitations

HVE Core's nature as a static artifact corpus, combined with its dependence on a downstream inference platform, produces a specific limitations profile.

* **No inference runtime.** HVE Core cannot validate the actual responses a downstream model produces from its instructions. Artifact quality is verified through linting, frontmatter validation, link checking, plugin-generation gates, and human pull-request review. Runtime fitness-for-purpose against a specific model and prompt depends on the host platform.
* **Behavior is mediated by the host platform.** Different Copilot Chat versions, different model selections, and different VS Code Copilot extensions can produce materially different results from the same artifact. HVE Core does not pin the model and cannot guarantee parity across hosts.
* **No inherent safety classification.** HVE Core relies entirely on the host platform's safety stack (input classifiers, output classifiers, jailbreak detection, content filters, abuse monitoring). HVE Core does not add safety classifiers of its own.
* **Persistent memory is opaque from the artifact side.** Some agents write to the host platform's memory layer (user, session, repository scopes). HVE Core authors the writes; the host platform owns retention, scope isolation, redaction, and exposure controls. Adopters should follow the host's guidance for inspecting and clearing memory.
* **Synthetic-persona content (Customer Card Render).** The skill produces synthetic personas for facilitation. Even with low-fidelity enforcement, downstream consumers may misread synthetic personas as real research participants if they bypass the disclosure footer or remove the slide-master watermark. See Appendix 5.
* **Customer-handoff opacity.** When HVE Core artifacts are copied into a customer repository, the canonical-repo audit trail, lint coverage, and marketplace publisher verification do not travel with them. Receiving teams should record the source version and adopt their own governance for ongoing maintenance.
* **Multi-agent orchestration audit trail is partial.** Subagent execution is captured in session traces but is not yet exported in a structured, replay-friendly format suitable for downstream compliance review. Audit-trail work is tracked in the published backlog handoff.
* **AI-disclosure markers are inconsistent.** Some artifact types include the standard "Brought to you by microsoft/hve-core" attribution and an AI-assistance disclosure footer; others do not. There is no automated check that enforces disclosure on every artifact-produced output. Disclosure-marker work is tracked in the published backlog handoff.
* **Public-facing claims should be read narrowly.** The repository's documentation and marketing copy describe what the artifacts ship and what an adopter can do with them. They do not characterize the runtime behavior of the model the host platform invokes. Apparent claims of safety, fitness for purpose, or production readiness apply to the artifact corpus, not to the downstream model.
* **Coverage is uneven across languages and ecosystems.** Coding-standards instructions are weighted toward C#, Python, PowerShell, Rust, Bash, Bicep, and Terraform. Other ecosystems have lower coverage. Natural-language coverage of agent and prompt output is principally English.
* **Accessibility audit not yet performed.** Documentation, agent UX surfaces in chat, and rendered artifacts have not yet been evaluated against Microsoft's accessibility standard.
* **Security Plan is owned separately.** A Security Planner assessment for HVE Core is not yet authored. The cross-reference table in the May 2026 RAI assessment is intentionally empty pending that work.

The published RAI assessment reads HVE Core's NIST AI RMF maturity as Developing for the Valid-and-Reliable, Accountable-and-Transparent, and Fair-with-Harmful-Bias-Managed characteristics, and Foundational for Safe, Secure-and-Resilient, Explainable-and-Interpretable, and Privacy-Enhanced. See the [Review Summary](docs/planning/rai/hve-core-2026-05/rai-review-summary.md) for the per-characteristic reads and the work items that would shift those reads.

## System performance

For a static artifact corpus, "performance" is not a model-accuracy figure. It is the degree to which the shipped artifacts behave as adopters expect when loaded into a supported host platform, plus the discipline with which the corpus itself is maintained.

HVE Core's performance posture rests on five tracks:

1. **Artifact-quality validation in CI.** Markdown linting, frontmatter validation, model-reference catalog validation, link checking, PowerShell static analysis, Python linting, YAML validation, collection-metadata validation, marketplace validation, dependency-pinning checks, action version consistency, copyright header validation, and skill structure validation all run on every pull request and block merge on failure.
2. **Plugin generation gate.** Collection manifests are regenerated from source on every change; mismatches between the source collections and the generated `plugins/` outputs block merge.
3. **Pull-request review.** Human review is required for every artifact change. Dependency pinning, action SHA staleness, and supply-chain checks run as automated gates that surface to reviewers.
4. **Versioning and publication.** Releases follow `release-please` conventional-commit conventions with a CHANGELOG. The Visual Studio Code extension and npm packages carry version metadata that adopters can pin against.
5. **Issue and feedback channel.** GitHub issues on `microsoft/hve-core` are the primary channel for bug reports, feature requests, and concerns. The maintainers triage and route from there.

Performance against a specific downstream model is not measured by HVE Core. Adopters who need reproducible behavior should pin both the artifact version and the host platform configuration.

### Best practices for improving system performance

* **Pin to a known-good release tag.** Treat the canonical repository's main branch as a moving target. For production-relevant adoption, pin to a release tag and review changes before upgrading.
* **Adopt one collection at a time.** HVE Core ships thirteen collections. Most adopters do not need all of them. Start with the collection closest to your workflow (for example, `coding-standards` for engineering productivity, `security` for threat modeling assistance, `rai-planning` for Responsible AI assessment scaffolding) and expand from there.
* **Read the per-agent description before loading it.** Each agent file documents its purpose, inputs, outputs, and limitations. Loading an agent without reading its instructions is the most common source of unexpected behavior.
* **Treat all governance-bearing agent output as a draft for human review.** Planning agents (RAI, Security, SSSC), code-review agents that gate pull requests, and customer-handoff agents (Customer Card Render, design-thinking coaches) produce drafts. Do not promote drafts to a binding decision without qualified human validation.
* **Inspect persistent memory before sharing a workspace.** Agents that write to the memory layer can carry context across sessions. Before sharing a workspace, screenshot, or recording, inspect and clear memory through the host platform's controls.
* **Preserve the attribution footer on derivative work.** When you copy an HVE Core artifact into a customer repository or fork, keep the "Brought to you by microsoft/hve-core" attribution and record the source version. This is both a courtesy and a governance signal that downstream maintainers can track.
* **Report concerns through GitHub issues.** Bug reports, behavioral concerns, accessibility problems, and Responsible AI questions are tracked in the public issue tracker. Use the relevant issue template.

## Mapping, measuring, and managing risks

The May 2026 Responsible AI assessment for HVE Core followed a six-phase protocol grounded in the NIST AI Risk Management Framework 1.0. The full outputs are published in this directory. This section summarizes the approach.

**Map.**

* Phase 1 produced a system-definition pack, an evidence-driven stakeholder impact map (six stakeholder ranks from internal Microsoft engineers through community consumers), and a control surface catalog organized by NIST AI RMF characteristic and Prevent / Detect / Respond.
* Phase 2 ran a risk-classification screening that placed HVE Core in the comprehensive depth tier.
* Phase 4 produced a 15-row threat addendum (`T-RAI-001` through `T-RAI-015`) covering prompt injection through shared artifacts, memory-layer contamination, governance-agent attribution gaps, customer-handoff opacity, AI-authored workflow supply-chain risk, and the four Customer Card Render synthetic-media entries.

**Measure.**

* Phase 5 produced an evidence register (41 rows, with full / partial / gap and verified / partial / unverified status per row) and a tradeoffs log (eight tradeoffs covering disclosure-fatigue, audit-trail-versus-security, persistence-versus-privacy, customer-handoff-reach-versus-attribution, and others).
* Phase 3 mapped the work to NIST AI RMF subcategories.
* The published Review Summary tabulates per-characteristic maturity reads, key findings, and per-checkpoint quality dimensions.

**Manage.** Phase 6 generated 20 work items grouped into three suggested remediation horizons:

* **Pre-Production (10 items).** This Transparency Note, AI-disclosure markers, public-claims audit, persona-template stereotyping audit, Customer Card Render redaction step, prompt-injection lint, AI-authored workflow review gate, per-agent Impact Assessments for governance-bearing agents, and Microsoft standards adoption for Privacy, SDL, Accessibility, and the AI Code of Conduct.
* **Early Operations (4 items).** Multi-agent orchestration audit trail, production telemetry and re-assessment cadence, memory-layer retention and consent specification, and gitleaks coverage in cloud agent CI.
* **Ongoing Governance (6 items).** Customer-handoff governance, language and code-language coverage expansion, accessibility audit, evaluation cohort diversification, sensitive customer data handling guidance, and agent discoverability promotion.

Items are tracked through `microsoft/hve-core` issues; the [Backlog Handoff](docs/planning/rai/hve-core-2026-05/rai-backlog-handoff.md) lists each item with placeholder identifiers (`{{RAI-TEMP-N}}`) ready for issue conversion.

The assessment did not catalog risks tied to model training, inference-time safety thresholds, or differential-privacy accounting because HVE Core does not train models, does not host inference, and does not maintain a training corpus. Those risks belong to the host platform.

## Evaluating and integrating HVE Core for your use

HVE Core is engineering tooling, not a managed service. Three responsibilities sit with the adopter at integration time:

* **Decide which collection or extension scope is appropriate for the workload.** Coding-standards collections suit engineering productivity. Planning collections (RAI, Security, SSSC) suit governance support but require qualified human reviewers downstream. The experimental collection ships features that are explicitly less mature.
* **Verify the host platform meets the requirements.** Current GitHub Copilot Chat in Visual Studio Code or the GitHub Copilot CLI are the supported hosts. Other clients are not characterized.
* **Establish your own oversight for agent output.** Agents do not autonomously commit code, file work items, or send messages without operator confirmation. Maintain that confirmation discipline in your local workflow, and ensure code-review gates remain in place for any agent-authored change to source, configuration, infrastructure, or workflows.

Avoid automation bias. Agent suggestions should be read as starting points for human work, not as substitutes for it. The governance-bearing agents in particular (Appendices 1 through 4) carry no compliance authority; their drafts are inputs to human review boards, security teams, and qualified reviewers.

## Learn more about responsible AI

* [Microsoft AI Principles](https://www.microsoft.com/ai/responsible-ai)
* [Microsoft Responsible AI Resources](https://www.microsoft.com/en-us/ai/responsible-ai-resources)
* [NIST AI Risk Management Framework 1.0](https://www.nist.gov/itl/ai-risk-management-framework)
* [Responsible use of GitHub Copilot features](https://docs.github.com/en/copilot/responsible-use)
* [HVE Core Review Summary (May 2026)](docs/planning/rai/hve-core-2026-05/rai-review-summary.md)
* [HVE Core Backlog Handoff (May 2026)](docs/planning/rai/hve-core-2026-05/rai-backlog-handoff.md)

## Learn more about HVE Core

* [HVE Core repository (microsoft/hve-core)](https://github.com/microsoft/hve-core)
* [Documentation index](docs/README.md)
* [Contributing guidelines](docs/contributing/README.md)
* [Architecture overview](docs/architecture/README.md)
* [Custom agents](docs/contributing/custom-agents.md)
* [Skills overview](docs/contributing/skills.md)
* [Roadmap](docs/contributing/ROADMAP.md)

Issues, feedback, and Responsible AI concerns: open a GitHub issue at [microsoft/hve-core](https://github.com/microsoft/hve-core/issues) using the relevant issue template.

## Appendices: per-agent transparency notes

The five appendices below cover the agents and skills that the May 2026 RAI assessment classified as binding-by-default or as the only direct generative-AI touchpoint. They are not exhaustive; the full agent inventory is in the repository's `.github/agents/` tree, and per-agent capability statements for the remaining agents are tracked as a Pre-Production work item in the published backlog.

### Appendix 1: RAI Planner

* **Agent file:** `.github/agents/rai-planning/rai-planner.agent.md`
* **Purpose:** Walks an authoring team through a six-phase Responsible AI assessment workflow. Produces drafts of risk-classification screening, standards mapping, security model addendum, control surface catalog, evidence register, tradeoffs log, threat addendum, RAI review summary, and a backlog handoff.
* **Inputs:** Operator-supplied system definition, stakeholder context, and prior assessment artifacts (when present). Reads instruction files under `.github/instructions/rai-planning/`.
* **Outputs:** Markdown artifacts under `.copilot-tracking/rai-plans/{project}/` plus, on user direction, published artifacts under `docs/planning/rai/{project}-{YYYY-MM}/`. All outputs carry an "AI-assisted content; review and validate before use" footer.
* **Intended uses:** Drafting the structural scaffolding of a Responsible AI assessment for review by a qualified RAI reviewer or board. Maintaining session state and resuming an in-progress assessment.
* **Specific limitations:** The agent does not approve, certify, or sign off on Responsible AI assessments. Drafts must be reviewed by a qualified reviewer (RAI champion, Office of Responsible AI, ethics committee, legal, or compliance) before any use that would carry weight in a real decision. The agent's own framework knowledge is bounded by its embedded standards instructions; it is not a substitute for current regulatory or organizational guidance. The agent does not pull live regulatory updates.
* **Specific considerations:** Treat every output as a draft. Do not promote a draft to "approved" status. The agent surfaces tradeoffs and concern levels as suggested reads; rating a risk as Low or Moderate is the reviewer's decision, not the agent's.

### Appendix 2: Security Planner

* **Agent file:** `.github/agents/security/security-planner.agent.md`
* **Purpose:** Walks a team through a STRIDE-aligned security model exercise organized by operational bucket. Produces a threat model, control mapping against OWASP and NIST families, and a backlog handoff suitable for security and engineering teams to triage.
* **Inputs:** Operator-supplied architecture description, data-flow notes, prior security artifacts (when present), and instruction files under `.github/instructions/security/`.
* **Outputs:** Markdown artifacts under `.copilot-tracking/security-plans/{project}/`, including operational-bucket inventory, security model, standards mapping, and backlog handoff. All outputs carry the AI-assistance disclosure footer.
* **Intended uses:** Drafting an initial threat model for a system that does not yet have one, expanding an existing model with additional buckets, or preparing material for review by a security architect or threat-modeling lead.
* **Specific limitations:** The agent does not perform live vulnerability discovery, does not run penetration tests, and does not query CVE databases at runtime. Standards mapping reflects the embedded standards in the agent's instructions and should be cross-checked against current authoritative sources before publication. The agent does not produce certifications, attestations, or compliance evidence; its outputs are inputs to those processes.
* **Specific considerations:** Threat IDs and concern levels are suggested. A qualified security reviewer must validate the threat surface, the proposed mitigations, and the residual-risk reads before any operational decision.

### Appendix 3: SSSC Planner

* **Agent file:** `.github/agents/security/sssc-planner.agent.md`
* **Purpose:** Walks a team through a Secure Software Supply Chain assessment aligned with the OpenSSF Scorecard family, SLSA levels, the Best Practices Badge, Sigstore, and SBOM standards. Produces a 27-capability inventory, gap analysis, dual-format work-item backlog (Azure DevOps and GitHub Issues templates), and a Scorecard projection.
* **Inputs:** Operator-supplied repository scope, current toolchain state, and instruction files under `.github/instructions/security/`.
* **Outputs:** Markdown artifacts under `.copilot-tracking/sssc-plans/{project}/`. Outputs carry the AI-assistance disclosure footer.
* **Intended uses:** Establishing a baseline for supply-chain posture, identifying gaps against published standards, and producing a draft work plan to close those gaps.
* **Specific limitations:** The agent does not run Scorecard live, does not produce signed attestations, and does not generate SBOMs. Capability reads come from operator-supplied evidence; the agent cannot independently verify a claim that, for example, a workflow uses pinned action SHAs. Standards versions are pinned to the embedded mapping; recheck against current OpenSSF and SLSA documentation before publication.
* **Specific considerations:** Treat the projected Scorecard score as an estimate based on the operator-reported state. Actual scores depend on the live tooling configuration, recent commit history, and Scorecard heuristics that may evolve.

### Appendix 4: Code-review agents (full, functional, standards)

* **Agent files:**
  * `.github/agents/coding-standards/code-review-full.agent.md`
  * `.github/agents/coding-standards/code-review-functional.agent.md`
  * `.github/agents/coding-standards/code-review-standards.agent.md`
* **Purpose:** Three sibling agents that read a diff or pull request scope and produce structured review feedback against repository conventions, language-specific instructions, and a configurable verdict rubric. The "full" agent runs both functional and standards passes; "functional" focuses on behavior, correctness, and design; "standards" focuses on style, idiom, and convention.
* **Inputs:** Diff scope (branch, commit range, or attached file set), language-specific instruction files under `.github/instructions/coding-standards/`, and repository copilot instructions.
* **Outputs:** A markdown review document under `.copilot-tracking/reviews/code-reviews/{date}/` containing per-finding categorization, severity, verdict normalization, and a summary. Outputs carry the AI-assistance disclosure footer.
* **Intended uses:** Pre-pull-request self-review, draft review feedback for a human reviewer to vet, and standards-coverage spot checks.
* **Specific limitations:** The agents do not execute code, do not run tests, do not connect to a debugger, and do not reason about runtime behavior beyond what the diff and the embedded instructions allow. They cannot verify security claims, cannot confirm test coverage figures, and cannot validate that an external dependency behaves as documented. They are pattern-matching reviewers, not human reviewers.
* **Specific considerations:** Treat verdicts as suggestions. The agents may produce false positives (flagging conformant code as non-conformant) and false negatives (missing real issues). A human code-reviewer remains responsible for the merge decision. Do not configure the agent as a required-status check that blocks merge without a human in the loop.

### Appendix 5: Customer Card Render skill

* **Skill file:** `.github/skills/experimental/customer-card-render/SKILL.md`
* **Purpose:** Generates customer-card PowerPoint content from Design Thinking canonical artifacts (interview notes, observations, synthesized themes). Each card represents a synthetic persona drawn from the research and is intended for stakeholder communication, not for delivery to the depicted individuals.
* **Inputs:** Canonical Design Thinking artifacts under `.copilot-tracking/dt/{project}/`, including research notes and synthesis output. Optionally, persona templates from the bundled set.
* **Outputs:** PowerPoint slide content YAML and rendered `.pptx` files. Cards include a low-fidelity visual rendering and persona narrative.
* **Intended uses:** Producing internal stakeholder-facing summaries of customer-research findings during ISE engagements. Communicating synthesized insight in a format that reads as illustrative rather than as a literal portrait of any individual.
* **Specific limitations:**
  * This is the only direct generative-AI touchpoint in HVE Core. Because the output is synthetic media depicting people-like figures, AI-disclosure, redaction, and stereotyping controls apply.
  * Even with low-fidelity enforcement, the output may be misread as portraying real individuals.
  * The bundled persona templates may encode demographic shorthand; a stereotyping audit is tracked as a Pre-Production work item in the published backlog.
  * Real participant data may bleed from source Design Thinking artifacts into rendered cards if the operator does not redact it before invoking the skill.
* **Specific considerations:**
  * **Hold the low-fidelity visual constraint.** Do not modify the skill to produce high-fidelity or photorealistic output. The low-fidelity style is the substantive control that keeps the output reading as illustrative rather than as a portrait of any individual; relaxing it requires an explicit accuracy review and an automated AI-disclosure marker, neither of which is in place yet.
  * **Redact source artifacts before rendering.** Real names, direct quotes attributed to identifiable individuals, photographs, and any other personally identifying detail in the Design Thinking research must be removed or generalized before the skill is invoked.
  * **Preserve disclosure on every output.** Generated cards should carry the AI-assistance disclosure footer and a slide-master watermark indicating that personas are synthetic. Do not strip these markers when copying decks into other contexts.
  * **Limit distribution to the originating engagement.** Synthetic personas should not be republished, repurposed for marketing, or used as evaluation data without explicit review.

## AI-Assistance Disclosure

The author created this content with assistance from AI. All outputs should be reviewed and validated before use by a qualified human reviewer.

## Disclaimer

This Transparency Note describes the artifacts shipped by `microsoft/hve-core` as of the document date. It does not constitute a warranty, certification, or compliance attestation, and it does not characterize the runtime behavior of any downstream model that the host platform may invoke. Adopters retain full responsibility for evaluating fitness for purpose, integrating appropriate human oversight, complying with applicable laws and regulations, and meeting the terms of service of the host platform.

Outputs from HVE Core agents and skills are advisory. They do not constitute legal, regulatory, security, or compliance advice and do not replace qualified human reviewers, ethics committees, security teams, legal counsel, or other appropriate authorities.

## About this document

| Field         | Value                             |
| ------------- | --------------------------------- |
| Published     | 2026-05-14                        |
| Last updated  | 2026-05-14                        |
| Cycle         | HVE Core RAI Assessment, May 2026 |
| Document type | Transparency Note                 |

This document is provided as-is and for informational purposes only. Information in this document, including URL and other references, may change without notice. This document is not legal advice. Consult appropriate counsel for jurisdiction-specific obligations.

---

🤖 *Crafted with precision by ✨Copilot following brilliant human instruction, then carefully refined by our team of discerning human reviewers.*
