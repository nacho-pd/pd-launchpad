---
name: choose-stack
description: "Decision tree for technology stack selection, produces an ADR"
---

# Choose Stack

Structured decision process for selecting a technology stack for a new project or feature.
Uses a decision tree to walk through requirements, applies the boring technology principle,
and produces an Architecture Decision Record (ADR) appended to `docs/architecture.md`.

---

## 1. Input

| Input | Source | Required |
|---|---|---|
| Functional requirements | `docs/specs/<feature>.md` | Yes |
| Non-functional requirements | Spec or explicit from stakeholder | Yes |
| Team constraints | Team size, skills, availability | Yes |
| Existing architecture | `docs/architecture.md` (if brownfield) | No |
| Budget constraints | Infrastructure budget, licensing limits | No |
| Timeline | Delivery deadline | No |

### Non-Functional Requirements Checklist

Gather these explicitly before starting the decision tree:

```
- [ ] Expected users: <number> at launch, <number> at 12 months
- [ ] Latency requirements: p99 < <ms> for critical paths
- [ ] Availability target: <99.9% / 99.99%>
- [ ] Data residency: <regions / regulations>
- [ ] Real-time needs: <none / notifications / live collaboration>
- [ ] Offline support: <yes / no>
- [ ] SEO requirements: <critical / nice-to-have / irrelevant>
- [ ] Auth complexity: <simple login / SSO / multi-tenant / custom roles>
- [ ] Integration requirements: <list external systems>
- [ ] Compliance: <SOC2 / HIPAA / GDPR / none>
```

---

## 2. Thinking Frameworks

### 2.1 Decision Tree

Walk through the tree in order. Each node is a yes/no question that narrows the stack.

```
START
  |
  v
[1] Does this project need a UI?
  |-- NO --> API-only: Supabase Edge Functions + PostgreSQL
  |          (Skip to node 5 for backend decisions)
  |-- YES
  v
[2] Is it content-heavy or application-heavy?
  |-- CONTENT (blog, docs, marketing) --> Next.js with SSG/ISR
  |-- APPLICATION (dashboard, SaaS, tool) --> Next.js App Router with SSR
  |-- HYBRID --> Next.js App Router (SSG for content pages, SSR for app pages)
  v
[3] Does it need real-time features?
  |-- NO --> Standard REST/RPC via Supabase client
  |-- YES --> Supabase Realtime (channels + presence)
  |          If Supabase Realtime is insufficient (>10k concurrent connections
  |          or custom protocol), consider dedicated WebSocket server.
  v
[4] Does it need complex backend logic?
  |-- MINIMAL (CRUD, auth, simple validation)
  |   --> Supabase Edge Functions (Deno runtime)
  |-- MODERATE (business logic, integrations, workflows)
  |   --> Supabase Edge Functions + shared logic in /lib
  |-- COMPLEX (long-running jobs, ML, heavy computation)
  |   --> Separate API service (Node.js or Python) + Supabase for data
  v
[5] Does it need background jobs or scheduled tasks?
  |-- NO --> Skip
  |-- YES --> Vercel Cron (simple) or Inngest/Trigger.dev (complex workflows)
  v
[6] Does it need file storage?
  |-- NO --> Skip
  |-- YES --> Supabase Storage (S3-compatible, integrated with RLS)
  v
[7] Does it need full-text search?
  |-- NO --> Skip
  |-- BASIC --> PostgreSQL full-text search (built into Supabase)
  |-- ADVANCED (facets, typo tolerance, instant) --> Consider Meilisearch or Typesense
  v
[8] Does it need email/notifications?
  |-- NO --> Skip
  |-- TRANSACTIONAL --> Resend (simple API, React Email templates)
  |-- MARKETING --> Resend + audience management or external tool
  v
DONE --> Compile selections into ADR
```

### 2.2 Default Stack

When the decision tree does not produce strong reasons to deviate, use:

| Layer | Technology | Rationale |
|---|---|---|
| Framework | Next.js 14+ (App Router) | React ecosystem, SSR/SSG flexibility, API routes |
| Language | TypeScript (strict mode) | Type safety, IDE support, catch errors at build time |
| Database | Supabase (PostgreSQL) | Managed Postgres, built-in auth, RLS, real-time, storage |
| ORM/Client | Supabase JS Client | Direct integration, typed with generated types |
| Testing | Vitest + Playwright | Fast unit tests + reliable E2E tests |
| Deployment | Vercel | Zero-config Next.js deploys, preview environments, edge |
| Styling | Tailwind CSS + shadcn/ui | Utility-first, copy-paste components, no runtime cost |
| Validation | Zod | Runtime type checking, works with TypeScript inference |
| State | React Server Components + zustand (if needed) | Minimize client state |

### 2.3 Override Criteria

The default stack should be overridden only when:

1. **Technical impossibility:** The default cannot meet a non-functional requirement (e.g., sub-10ms latency requires edge compute closer to users than Vercel provides).
2. **Team expertise:** The team has deep expertise in an alternative and zero Next.js experience, AND the timeline does not allow for learning.
3. **Ecosystem lock-in:** An existing system requires integration that is only well-supported by a different stack (e.g., .NET backend for Azure AD integration).
4. **Regulatory requirement:** Compliance mandates a specific technology or hosting provider.

Override is NOT justified by:
- Personal preference for a different framework
- "I heard X is faster" without benchmarks for the specific use case
- Resume-driven development
- "Everyone is using Y now"

### 2.4 Boring Technology Principle

From Dan McKinley's "Choose Boring Technology":

- Every team has a limited budget of **innovation tokens** (roughly 3).
- Spend them on the core differentiator of the product, not on infrastructure.
- "Boring" means well-understood failure modes, abundant documentation, large community.
- New technology has unknown unknowns that consume engineering time disproportionately.

**Application:** If the default stack works, use it. Spend innovation tokens on what makes
the product unique, not on replacing PostgreSQL with a graph database "just in case."

### 2.5 Operational Complexity Tax

Every technology added to the stack incurs ongoing costs:

```
Operational cost = (learning curve) + (maintenance burden) + (incident surface area)
```

Before adding a technology, answer:
1. Who on the team can debug it at 2 AM?
2. What is the upgrade path when a major version is released?
3. What happens if the maintainer abandons it?
4. Does it have a managed/hosted option, or must we self-host?

If the answer to #1 is "nobody" and #3 is "we're stuck," do not adopt it.

---

## 3. Expected Output

### ADR Template

The output is an Architecture Decision Record appended to `docs/architecture.md`:

```markdown
## ADR-<number>: Technology Stack Selection

**Status:** Proposed
**Date:** <ISO date>
**Deciders:** <agent + human reviewer>

### Context

<What is the project? What problem does it solve? What constraints exist?>

We are building <project description>. The project requires:
- <functional requirement 1>
- <functional requirement 2>
- <non-functional requirement 1: e.g., "support 1,000 concurrent users">
- <non-functional requirement 2: e.g., "SEO-critical landing pages">

Team constraints:
- <team size and skills>
- <timeline>

### Decision Tree Walkthrough

| Node | Question | Answer | Selection |
|------|----------|--------|-----------|
| 1 | Needs UI? | Yes | — |
| 2 | Content or app? | Application | Next.js App Router |
| 3 | Real-time? | Yes (notifications) | Supabase Realtime |
| 4 | Backend complexity? | Moderate | Supabase Edge Functions |
| 5 | Background jobs? | Yes (daily digest) | Vercel Cron |
| 6 | File storage? | Yes (user uploads) | Supabase Storage |
| 7 | Full-text search? | Basic | PostgreSQL FTS |
| 8 | Email? | Transactional | Resend |

### Decision

We will use the following stack:

| Layer | Technology | Version |
|---|---|---|
| Framework | Next.js (App Router) | 14.x |
| Language | TypeScript (strict) | 5.x |
| Database | Supabase (PostgreSQL 15) | — |
| Auth | Supabase Auth | — |
| Real-time | Supabase Realtime | — |
| Storage | Supabase Storage | — |
| Testing | Vitest + Playwright | — |
| Deployment | Vercel | — |
| Styling | Tailwind CSS + shadcn/ui | — |
| Email | Resend | — |
| Validation | Zod | — |
| Background Jobs | Vercel Cron | — |

**Innovation tokens spent:** 0 (all defaults)

### Consequences

**Positive:**
- <benefit 1>
- <benefit 2>

**Negative:**
- <tradeoff 1>
- <tradeoff 2>

**Risks:**
- <risk 1 + mitigation>

### Alternatives Considered

#### Alternative 1: <Technology>
- **Reason considered:** <why it was on the table>
- **Reason rejected:** <why it was not selected>
- **Would reconsider if:** <conditions that would change the decision>

#### Alternative 2: <Technology>
- **Reason considered:** <why>
- **Reason rejected:** <why not>
- **Would reconsider if:** <conditions>
```

---

## 4. Review / Rubric

### ADR Quality Checklist

| Criterion | Pass/Fail |
|---|---|
| Decision tree was followed (all relevant nodes visited) | |
| Every non-functional requirement is addressed by a technology selection | |
| Rationale is documented for each layer, not just "it's the default" | |
| At least 2 alternatives were genuinely considered (not strawmen) | |
| Operational complexity tax was acknowledged for non-default choices | |
| Innovation token budget is explicit (how many spent, on what) | |
| Consequences include both positive and negative outcomes | |
| "Would reconsider if" conditions are concrete and testable | |
| ADR follows the template format completely | |
| Status is "Proposed" (not "Accepted" — human must approve) | |

### Red Flags

- Choosing a technology because "it's trending" without concrete requirement match
- More than 3 innovation tokens spent without exceptional justification
- No alternatives considered (indicates the decision was predetermined)
- Operational complexity tax ignored for self-hosted dependencies
- Missing non-functional requirements in the context section

---

## 5. Skill Definition (Orchestration)

### Sub-Tasks

```yaml
tasks:
  - id: cs-01
    name: read-spec-requirements
    action: "Read docs/specs/ for functional and non-functional requirements"
    output: "Parsed requirements list with NFR checklist filled"

  - id: cs-02
    name: classify-project-type
    action: "Determine if project is content-heavy, app-heavy, or hybrid"
    depends_on: [cs-01]
    output: "Project classification with justification"

  - id: cs-03
    name: gather-team-constraints
    action: "Read team context: size, skills, timeline, budget"
    output: "Team constraints summary"

  - id: cs-04
    name: read-existing-architecture
    action: "Read docs/architecture.md if it exists (brownfield project)"
    output: "Existing stack and constraints, or 'greenfield'"

  - id: cs-05
    name: walk-decision-tree
    action: "Walk through each node of the decision tree, answering based on requirements"
    depends_on: [cs-01, cs-02, cs-03, cs-04]
    output: "Decision tree walkthrough table with selections per node"

  - id: cs-06
    name: identify-nfr-gaps
    action: "Check if any non-functional requirement is not covered by the tree selections"
    depends_on: [cs-05]
    output: "List of NFRs and whether they are addressed"

  - id: cs-07
    name: check-override-criteria
    action: "Determine if any override criteria apply to deviate from defaults"
    depends_on: [cs-05, cs-03]
    output: "Override decisions with justification"

  - id: cs-08
    name: select-technologies
    action: "Compile final technology selection per layer"
    depends_on: [cs-05, cs-06, cs-07]
    output: "Stack table with technology, version, and rationale"

  - id: cs-09
    name: document-rationale
    action: "Write the Context and Decision sections of the ADR"
    depends_on: [cs-08]
    output: "ADR context + decision text"

  - id: cs-10
    name: list-alternatives
    action: "Document at least 2 alternatives that were considered and why they were rejected"
    depends_on: [cs-08]
    output: "Alternatives section of the ADR"

  - id: cs-11
    name: write-adr
    action: "Compile the full ADR from all sections"
    depends_on: [cs-09, cs-10]
    output: "Complete ADR markdown"

  - id: cs-12
    name: append-to-architecture
    action: "Append the ADR to docs/architecture.md"
    depends_on: [cs-11]
    output: "Updated architecture.md file"

  - id: cs-13
    name: update-claude-md
    action: "Update CLAUDE.md stack section with the selected technologies"
    depends_on: [cs-12]
    output: "Updated CLAUDE.md"
```

### Execution Flow

```
cs-01 (spec) ──┐
cs-03 (team) ──┤──> cs-05 (tree) ──> cs-06 (NFR gaps) ──┐
cs-04 (arch) ──┤                 ──> cs-07 (overrides) ──┤
cs-02 (type) ──┘                                         └──> cs-08 (select)
                                                               |
                                                          cs-09 (rationale)
                                                          cs-10 (alternatives)
                                                               |
                                                          cs-11 (write ADR)
                                                               |
                                                     cs-12 (append) ──> cs-13 (CLAUDE.md)
```

---

## 6. HITL Build

### Agent Autonomy

The stack selection agent **proposes** but does not **decide**. The ADR is written with
status "Proposed" and requires human approval before any implementation begins.

**Autonomous actions:**
- Read all input documents (spec, architecture, team constraints)
- Walk the decision tree based on requirements
- Select technologies per layer
- Write the complete ADR
- Append to architecture.md with "Proposed" status

**Escalation triggers:**
- Non-functional requirements are missing or contradictory — ask stakeholder to clarify
- Override criteria apply — present both the default and override options with tradeoffs
- Innovation token budget exceeds 3 — present the budget with justification for each token
- Team has zero experience with the default stack — present learning curve assessment
- Budget constraints conflict with the selected managed services — present cost comparison

### Safety Constraints

- The agent MUST NOT set ADR status to "Accepted" — only human can accept
- The agent MUST NOT install packages or scaffold code — that happens after approval
- The agent MUST NOT delete existing ADRs or overwrite architecture decisions
- The agent MUST present alternatives honestly (not as strawmen to justify a predetermined choice)

---

## 7. HITL Review

### Review Protocol

This skill requires **FULL human review** before proceeding. The agent presents:

1. **Decision tree walkthrough:** Show each node, the answer, and the resulting selection.
   The human verifies that the answers match their understanding of the requirements.

2. **Stack summary table:** Full technology selection with rationale per layer.
   The human can challenge any selection and ask for re-evaluation.

3. **Innovation token budget:** How many tokens were spent and on what.
   The human decides if the spend is justified.

4. **Alternatives considered:** At least 2 alternatives with honest pros/cons.
   The human may select an alternative or propose a new one.

5. **Operational complexity assessment:** For any non-default technology, the human
   reviews the maintenance implications.

### Approval Flow

```
Agent proposes ADR (status: Proposed)
  |
  v
Human reviews decision tree walkthrough
  |-- Disagrees with a node answer --> Agent re-walks tree with corrected input
  |-- Agrees
  v
Human reviews stack selection
  |-- Wants to change a technology --> Agent updates ADR and re-evaluates consequences
  |-- Agrees
  v
Human approves
  |
  v
Agent updates ADR status to "Accepted"
Agent proceeds to scaffolding (separate skill)
```

### Post-Approval

Once the ADR is accepted:
- The status is changed to "Accepted" with the approval date.
- The stack section in CLAUDE.md is updated to reflect the accepted technologies.
- The ADR is immutable — future changes require a new ADR that supersedes it.
- Implementation can begin using the approved stack.
