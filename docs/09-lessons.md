# 9. Lessons

## What worked

| Lesson | Detail |
|---|---|
| Data before tools | We assumed "more tests". Labelled returns showed skipped items, contradicting numbers and missing translations. |
| Hooks over text | Prohibitions in CLAUDE.md fade in long sessions; hooks do not. |
| One CLI for agent and human | Short output, called from Bash. One thing to maintain, and people can run it too. |
| Stops | Context question, checklist approval, fix approval. Code written too early costs the most. |
| Evidence | "Which URL, what did you see", enforced by checklist and gate. |
| Protected context | Verification in a sub-agent, reference in path rules, code questions in the graph. |
| Predictable addresses | Port and host derive from the task number; Claude can work out the URL. |
| Status in one call | Jira, workspaces, git and past sessions in one JSON. |

## Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| Edits not showing | Server left in build mode | MODE column in `ws ls`; always end verification |
| No hooks in task session | No `.claude` in task folder | Symlink it |
| Rule file not loaded | File outside session root | "Read the rule first" in CLAUDE.md |
| One task broke another | Shared repo or DB | Warn before shared edits; list tasks before migrations |
| Edit in source checkout | Lost track of the task | Session marker + explicit rule |
| Slow machine | Many dev servers | Memory cap, `ws down`, `ws clean` |
| Token in allowlist | Personal permissions store commands verbatim | Never share it; tokens from env vars |

## Where to start

```mermaid
quadrantChart
    title Cost vs impact
    x-axis Low setup cost --> High setup cost
    y-axis Low impact --> High impact
    quadrant-1 Plan for it
    quadrant-2 Do first
    quadrant-3 Nice to have
    quadrant-4 Only if needed
    "CLAUDE.md + approvals": [0.15, 0.8]
    "Slop hooks": [0.2, 0.55]
    "Path rules": [0.3, 0.6]
    "Ticket checklist": [0.35, 0.85]
    "Verifier agent": [0.45, 0.75]
    "Code graph": [0.4, 0.45]
    "Shared browser": [0.7, 0.65]
    "UAT gate": [0.75, 0.8]
    "Task workspaces": [0.85, 0.5]
```

```mermaid
flowchart LR
    S1["1. Label your<br/>return or bug data"] --> S2["2. CLAUDE.md<br/>+ approvals"]
    S2 --> S3["3. Slop checker"]
    S3 --> S4["4. Checklist +<br/>verifier agent"]
    S4 --> S5{"parallel tasks<br/>common?"}
    S5 -- yes --> S6["5. Workspace CLI"]
    S5 -- no --> S7["skip"]
    S6 --> S8["6. UAT gate:<br/>enforce what the data shows"]
    S7 --> S8
```

Our five checks fit our returns. Label yours first and let that pick the tools.
