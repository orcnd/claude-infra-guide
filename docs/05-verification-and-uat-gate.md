# 5. Verification and the UAT gate

## Why pages, not tests

We took about six months of UAT returns from Jira (status changes plus comments around each return),
labelled them against a fixed reason list with three separate model runs, and spot-checked by hand.
About a third of hand-overs had come back at least once.

```mermaid
---
config:
  xyChart:
    width: 760
    height: 360
  themeVariables:
    xyChart:
      plotColorPalette: "#4C6EF5"
---
xychart-beta horizontal
    title "Main reason for a UAT return (% of returns)"
    x-axis ["Ticket items missing", "Numbers wrong or contradicting", "Process, no defect", "Broken feature or link", "Translation or locale format", "Layout or mobile", "External dependency", "Misread request", "New request in UAT", "Cache or deploy"]
    y-axis "% of returns" 0 --> 20
    bar [17, 14, 14, 14, 12, 8, 6, 5, 5, 3]
```

About 70% were preventable, and not by unit tests. The check that would have caught each one:

```mermaid
---
config:
  xyChart:
    width: 760
    height: 300
  themeVariables:
    xyChart:
      plotColorPalette: "#4C6EF5"
---
xychart-beta horizontal
    title "Check that would have caught it (% of preventable returns)"
    x-axis ["Walk ticket items on the page", "Cross-check the same number", "Open non-English locales", "Click links, filters, forms", "Open at mobile width", "Other"]
    y-axis "% of preventable returns" 0 --> 35
    bar [32, 19, 18, 15, 7, 9]
```

The first five cover over 90%. So: no tests in these repos, and every change ends with those five checks,
done by tools. CLAUDE.md says this overrides any "write a failing test first" step.

## The verification pass

```mermaid
flowchart TD
    A["change made"] --> B["open page + one<br/>non-English locale"]
    B --> C["page text + API payload"]
    C --> D["ws browse check --locales all"]
    C --> E["ws browse crawl"]
    C --> F["ws browse numbers vs API"]
    C --> G["read for contradictions:<br/>same value differs across views<br/>ranks, totals, % over 100<br/>rows the page should hide<br/>labels vs data, stale copy<br/>future dates, wrong label or image<br/>one card's extra line stretching a row"]
    D --> X["findings"]
    E --> X
    F --> X
    G --> X
    X --> Y{"any?"}
    Y -- no --> Z["close item with evidence"]
    Y -- yes --> R{{"report where, what, why<br/>fix after approval"}}
```

Run by the [page-logic-verifier](../templates/.claude/agents/page-logic-verifier.md) agent.

## `ws browse`: one browser for all agents

Playwright MCP started a browser per session with long output, and five parallel tasks ran the machine out of
memory. We replaced it with one headless Chromium daemon (`playwright-core`, about 1,100 lines):

```mermaid
flowchart LR
    subgraph CLIENTS["Callers"]
        C1["session, task 1234"]
        C2["session, task 1240"]
        C3["you, in a terminal"]
    end
    CL["ws browse client<br/>local socket"]
    subgraph D["Daemon, one per machine"]
        BR["Chromium headless shell"]
        X1["context: task 1234<br/>pages p1, p2"]
        X2["context: task 1240<br/>page p3"]
    end
    C1 --> CL
    C2 --> CL
    C3 --> CL
    CL --> D
    BR --- X1
    BR --- X2
```

- One context per task; a session cannot touch another task's pages.
- Text output: an outline with `[eN]` refs on open, only the diff on click.
- Images, fonts and analytics blocked by default.
- Idle pages close after 10 minutes, the daemon after 15.

| Command | Catches |
|---|---|
| `check <url> --locales all` | Per locale: raw keys, `NaN`/`undefined`/`null`, broken images, duplicate rows, h1 count, `lang` mismatch, console/HTTP errors, copy still in English, `.` decimals on comma locales, 390px overflow (with screenshot) |
| `crawl <url>` | Every button, tab, select and checkbox clicked one by one; failures and 4xx/5xx links listed |
| `numbers <url>` | Numbers per entity from tables and cards, to compare with the API |

`ws i18n` checks key parity across all locale files.

## Checklist

```mermaid
stateDiagram-v2
    [*] --> open: add "text" --page /path
    open --> done: done id --evidence "..."
    open --> dropped: drop id --reason "..."
    done --> open: reopen id
    dropped --> open: reopen id
    done --> [*]
    dropped --> [*]
    note right of open
        ws uat blocks while
        any item is open
    end note
```

Evidence means URL, what is visible, which check came back clean. "Done" alone does not count.

## `ws uat <n>`

The only way into UAT:

```mermaid
flowchart TD
    S(["ws uat 1234"]) --> C1{"open items?"}
    C1 -- yes --> F["BLOCKED<br/>print reasons"]
    C1 -- no --> C2{"uncommitted or<br/>unpushed?"}
    C2 -- yes --> F
    C2 -- no --> C3{"locale key gaps?"}
    C3 -- yes --> F
    C3 -- no --> B["release build"]
    B --> L["each checklist page<br/>x 7 locales + mobile"]
    L --> C4{"HTTP/page error, raw key,<br/>untranslated, decimals,<br/>overflow, failing click,<br/>broken link?"}
    C4 -- yes --> F
    C4 -- no --> R["write uat-report.md"]
    R --> T[("ticket -> UAT")]
    T --> CM{"--comment?"}
    CM -- "yes, human asked" --> J["post report to Jira"]
    F -.->|"--force reason<br/>human only"| R
```

Posting to Jira and `--force` are human calls; CLAUDE.md forbids Claude from doing either alone.

Next: after a month with the gate, relabel returns the same way and see if the preventable share drops.
