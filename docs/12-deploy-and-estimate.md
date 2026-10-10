# 12. Deploy from the terminal, estimate from history

Two smaller `ws` commands that close gaps at both ends of a ticket: `ws estimate` before work starts,
`ws deploy` when it is ready to show.

## `ws deploy`: pressing "Run" on a manual pipeline step

Feature, test and production deploys are manual steps in Bitbucket Pipelines. Pressing them meant opening
the browser, finding the pipeline for the branch and clicking Run, for every repo.

```bash
ws deploy 1234                      # feature branch, frontend + API "Feature Deploy" steps
ws deploy 1234 --repo=api           # one repo
ws deploy test --repo=web,api       # test branch
ws deploy production ... --prod     # production: --prod required, then a confirmation prompt
ws deploy 1234 --status --json      # just read the state
```

Reading pipelines and waiting for a step works with an API token. Starting a manual step does not:
Bitbucket refuses API tokens on that endpoint. So starting goes through a small Chrome extension that uses
the browser session you are already logged in with.

```mermaid
sequenceDiagram
    autonumber
    participant CLI as ws deploy
    participant API as Bitbucket API (token)
    participant BR as Chrome (logged in)
    participant EXT as Bridge extension
    participant BB as bitbucket.org (session)

    CLI->>API: find pipeline for branch, find manual step
    CLI->>CLI: one-shot listener on 127.0.0.1:<random port>
    CLI->>CLI: job = {repo, pipeline, step, port, nonce, time, prod?}<br/>signed with HMAC-SHA256
    CLI->>BR: open pipeline page in background tab<br/>job in URL hash
    BR->>EXT: content script reads hash, removes it from URL
    EXT->>EXT: check signature, age < 2 min, repo allow-list,<br/>nonce not used before
    EXT->>BB: read step: name and state
    alt name looks like prod and job has no prod flag
        EXT-->>CLI: refused
    else step is PENDING
        EXT->>BB: start step (same request the Run button sends)
        EXT-->>CLI: result to 127.0.0.1:<port>, close tab
    end
    loop until finished or timeout
        CLI->>API: step state
    end
    CLI-->>CLI: exit code: 0 ok, 1 failed, 3 auth, 5 timeout, 6 not started ...
```

Safety design:

| Risk | Guard |
|---|---|
| A crafted link starts a deploy | Jobs are HMAC-signed with a secret created by `ws deploy bridge-setup` (Keychain + extension config, `chmod 600`) |
| A reload or a copied URL replays a job | Job removed from the URL at once; nonce stored, single use; 2-minute expiry |
| A job for another repo or a production step | Repo allow-list in the extension; the step name is re-read there, and anything that looks like production is refused unless the signed job says `prod` |
| The URL is built from untrusted input | The extension builds the Bitbucket URL from verified fields only |
| Production by accident | `--prod` is required, and a confirmation prompt follows unless `--yes` |
| The start request reports an error but the step did start | The CLI does not trust the start reply; it confirms the step state through the API |

Two things to know before copying it:

- The start request is the one Bitbucket's own UI sends to an internal endpoint, not a public API. It can
  change without notice. When it does, the CLI fails with "could not start" and you press Run by hand.
- Claude's Bash tool has no terminal, so the production confirmation prompt cannot appear and the CLI asks
  for `--yes`. Nothing in the tool stops an agent from adding it. Put production deploys on the "never without
  explicit confirmation" list in CLAUDE.md and in `autoMode.soft_deny`.

## `ws estimate`: estimating a ticket the way you would

Estimates are hours in Jira. The tool learns from your own last 120 days of estimated tickets.

```mermaid
flowchart TD
    T(["ticket text"]) --> TAG["keyword rules:<br/>area (page or system)<br/>+ work type (bugfix, copy, new page,<br/>data integration, investigation ...)<br/>+ size signals (numbered items, URLs)"]
    H[("your estimated tickets,<br/>last 120 days")] --> P1
    H --> P2
    TAG --> P1["hierarchical median<br/>area+type -> type -> area -> all"]
    TAG --> P2["median of the 5 most<br/>similar tickets by text"]
    P1 --> SEL{"method chosen by<br/>leave-one-out backtest"}
    P2 --> SEL
    SEL --> E["estimate in hour buckets<br/>0.25 / 0.5 / 1 / 2 / 3 / 4 / 6 / 8"]
    E --> LLM["optional review by a model with no tools<br/>(comments, never changes the number)"]
```

`ws estimate tree` prints the area -> type -> median hours map; `ws estimate backtest` measures every method
by hiding each past ticket in turn and estimating it from the rest.

### How good it is

```mermaid
---
config:
  xyChart:
    width: 700
    height: 320
  themeVariables:
    xyChart:
      plotColorPalette: "#4C6EF5"
---
xychart-beta horizontal
    title "Leave-one-out backtest, 307 tickets: estimate within one bucket (%)"
    x-axis ["Best model (ridge + similar tickets)", "Similar tickets", "Blend", "Ridge", "Hierarchical median", "Always 1 hour (baseline)"]
    y-axis "% within one bucket" 0 --> 100
    bar [71, 67, 67, 67, 64, 64]
```

| Method | Exact bucket | Within one bucket | Typical error |
|---|---|---|---|
| Best model | 30% | 71% | about 2x |
| Always say "1 hour" | 27% | 64% | |

The best method beats the trivial baseline by 3 points on exact hits and 7 points within one bucket, with a
typical error of about 2x. That is the honest result, and the reason we keep the backtest in the tool: it is a
sanity check ("similar tickets took about this long"), not an oracle. By area it ranges from about 40% to 89%
within one bucket; the backtest prints that per area, so you know which kinds of tickets to trust it on.
