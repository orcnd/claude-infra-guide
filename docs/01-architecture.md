# 1. Architecture and principles

## Component map

```mermaid
flowchart TB
    subgraph EXT["External"]
        JIRA[("Jira")]
    end

    subgraph CLI["ws CLI (one Node script)"]
        direction LR
        W1["create / up / verify<br/>down / rm / clean"]
        W2["checklist / i18n / uat"]
        W3["browse<br/>check / crawl / numbers"]
        W4["board / resume"]
    end

    subgraph ROOT["~/code/project (source checkouts)"]
        direction LR
        R1["api/  web/<br/>stay on main"]
        R2["legacy/  cms/<br/>shared"]
        R3["CLAUDE.md  .claude/<br/>graphify-out/"]
    end

    subgraph TASK["~/code/tasks/task-1234"]
        direction LR
        T1["api/  web/<br/>worktrees<br/>feature/task-1234"]
        T2["legacy  cms  CLAUDE.md  .claude<br/>symlinks"]
        T3[".ws/<br/>logs, mode, checklist, report"]
    end

    subgraph NET["Local network"]
        direction LR
        N1["https://1234.ws.test<br/>nginx -> Next :31234"]
        N2["https://api-1234.ws.test<br/>nginx -> php-fpm"]
    end

    JIRA <--> W2
    JIRA --> W4
    W1 -->|git worktree add| T1
    W1 -->|ln -s| T2
    R2 -.-> T2
    R3 -.-> T2
    W1 -->|vhost + server| NET
    T1 --> NET
    W3 -->|headless Chromium| N1
```

Claude Code always opens in `~/code/project`, moves into the task folder itself, and runs the same `ws`
commands a human would.

## Principles

| Principle | In practice |
|---|---|
| One task, one space | Task code is edited only under `tasks/task-<n>/`. Root `api/` and `web/` stay on main. |
| Diagnose, ask, then fix | Claude shows file:line, cause and fix, then waits. |
| Humans commit and push | Claude proposes message and file list, waits for a yes. |
| Read the page, skip the tests | Every change ends with a logical check of the rendered page and its API payload ([05](05-verification-and-uat-gate.md)). |
| Close with evidence | A checklist item closes with what was seen on the page. |
| Give context up front | Repo knowledge in rule files, code relationships in a graph; both before grep. |
| Hooks enforce rules | Typography, slop and graph-first are hooks, not just text. |
| One tool for agent and human | `ws` behaves the same in a terminal and in Claude's Bash tool; output is short plain text. |

## Shared vs per-task

```mermaid
flowchart LR
    subgraph PER["Per task"]
        A["api/ worktree"]
        W["web/ worktree"]
        S["Next dev server<br/>port 30000+n"]
        L[".ws/ logs + checklist"]
    end
    subgraph SHARED["Shared by every task"]
        LG["legacy/"]
        CM["cms/"]
        DB[("MySQL")]
        RD[("Redis")]
        FPM["php-fpm"]
        CFG["CLAUDE.md + .claude/"]
    end
    A --> FPM --> DB
    A --> RD
    W --> S
    LG -.symlink.-> PER
    CM -.symlink.-> PER
    CFG -.symlink.-> PER
```

| Resource | Scope | Consequence |
|---|---|---|
| `api/`, `web/` | Per task | Own branch and server |
| `legacy/`, `cms/` | Shared | A change shows up in every task; Claude warns before editing |
| Database, Redis, php-fpm | Shared | Open tasks are listed before a migration or cache flush |
| `CLAUDE.md`, `.claude/` | Shared | Sessions inside a task folder keep the same hooks and agents |

`legacy/` and `cms/` are not worktrees: they change rarely and are expensive to set up per task
(WordPress, a multi-host framework). We took the trade-off and made the warning a rule.
