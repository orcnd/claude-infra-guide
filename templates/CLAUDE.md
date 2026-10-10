# Codebase Overview

Four repos live in this directory:

- `legacy/` - Custom PHP framework (no Laravel/Symfony). Multi-host MVC.
- `api/` - Standalone REST API (FastRoute + Eloquent).
- `web/` - Next.js frontend (App Router, React, TypeScript, next-intl, 7 locales).
- `cms/` - Headless WordPress. Content backend consumed by `api/` and `web/`.

Repo reference (folder layout, DB connections, helpers, endpoints, patterns) lives in `.claude/rules/`, one
file per repo. They load by themselves only for files under the session's project root. When you work in a
task worktree (`~/code/tasks/task-<n>/...`), Read the matching rule file by its full path before your first
read or edit in that repo, once per session.

## Git

The root is not a git repo. Always scope git to a repo: `git -C web status`, `git -C api log`.

---

# Text & Typography

Never use the em dash or the en dash in any text you produce. Use a plain hyphen (`-`). This covers code
comments, commit messages, UI copy, translation files, docs and chat replies.

Avoid the phrases in `.claude/slop/rules.txt`. Hooks run `.claude/slop/slop_check.py` on every edit, commit
message and reply and make you fix what they find. Rewrite the sentence plainly instead of swapping in a
synonym. For a genuine false positive (quoted example, product name) put `slop-ok` on that line.

---

# Verification: no tests

Do not write, update or run unit/integration tests in `legacy/`, `api/` or `web/`. This overrides any skill or
plan step that says to write a failing test first.

Why: our UAT returns came from skipped ticket items, numbers that contradict each other, untranslated
locales and broken clicks, not from logic a unit test would cover.

Every change ends with a logical verification pass on what the user will see:

1. Open the affected page(s) on the task frontend (`https://<n>.ws.test:8443/...`, plus one non-English
   locale), and read the page text and the API payload behind it.
2. Look for things that cannot all be true at once: the same value differing between a card, a table row
   and a chart; ranks out of order; totals that do not add up; rows that the page's own rules should hide;
   labels that do not match their data; raw translation keys, `undefined`, `NaN`, `null`; broken images;
   duplicated entries; dates in the future.
3. Report every finding with where it is and why it is wrong. Fix it only after the user agrees.

The `page-logic-verifier` agent runs this pass. Browser work goes through `ws browse`
(`check`, `crawl`, `numbers`); use Playwright or Chrome only for visual or authenticated checks.

---

# Never Do Without Explicit Confirmation

- Fix any bug: diagnose first, present file:line, cause and proposed fix; wait for approval.
- Run `git commit`: show the proposed message and file list; wait for approval.
- Push to a remote.
- Start a deploy (`ws deploy`), and never pass `--prod` or `--yes` on your own.
- Drop or truncate tables, or run destructive DB operations.
- Create new architectural patterns; reuse existing ones.
- Modify shared infrastructure (nginx configs, cron schedules, queues).
- Commit `.env` files, credentials or other secrets. Never.

# Always Safe To Do

- Search and read the codebase before writing code.
- Run static analysis and clear route caches.
- Use existing helpers and services instead of new ones.

---

# Output

Reports and analysis go under `analysis/`. One-off scripts go under a gitignored scratch folder.
AI specs, plans and design docs go under a gitignored docs folder; never `git add` them.

---

# Processes

## Parallel task workspaces

Each task gets its own workspace, created by the `ws` CLI:

```
~/code/
├── project/                 source checkouts + shared code. NEVER edit task code here.
└── tasks/task-<n>/
    ├── api/  web/           git worktrees, branch feature/task-<n>
    ├── legacy  cms  CLAUDE.md  .claude   symlinks to the shared copies
    └── .ws/                 server.log, build.log, mode, checklist
```

- All reads and edits for a task go through `~/code/tasks/task-<n>/`.
- `legacy/` and `cms/` are shared. Say so before editing them.
- The database, Redis and php-fpm are shared. Do not run migrations or flush caches without first telling
  the user which other tasks are open (`ws ls`).

## `start task <n>`

Reply in `<your team's language>` for the whole conversation that starts this way. Code, commands, paths and URLs stay as-is.

1. `ws ls` - show which tasks are already open.
2. `ws create <n> --yes`. If DNS or the certificate is missing, run `ws setup` and relay its sudo steps.
3. `ws up <n>`, then record the task for this session:
   `mkdir -p ~/code/tasks/.sessions && echo <n> > ~/code/tasks/.sessions/$CLAUDE_CODE_SESSION_ID`.
4. From now on every path you touch is under `~/code/tasks/task-<n>/`.
5. `ws jira <n>`; show the ticket, then the workspace path and URLs.
6. Ask what the user wants to do and whether there is context to add. Wait.
7. Before any code: `ws checklist <n> round`, then one `ws checklist <n> add "<item>" --page /path` per
   checkable requirement. Tell the user in 3-6 lines how you understood the task plus open questions, show
   the list, and wait for confirmation.

## Checklist and UAT gate

- Close an item only with evidence from the rendered page:
  `ws checklist <n> done 1.3 --evidence "/tr/products: filter shows 12 price ranges, browse check clean"`.
- Before hand-over: commit (with approval), push, then `ws uat <n>`. It blocks on open items, unpushed work,
  missing locale keys and page errors in every locale. `--force` is the user's decision, never yours.
- After a return from UAT: `ws checklist <n> round`, one item per tester note, fix, evidence, `ws uat <n>` again.

## `stop task`

1. Resolve `<n>` from the argument, else the session marker, else the current workspace.
2. `ws down <n>`. Never `ws rm`.
3. `git -C ... status --porcelain` for both worktrees and the shared repos. If anything is dirty, list it and
   wait: commit (with approval), leave it, or cancel. Never stash, reset or discard.
4. Print a closing summary, then end the session (`kill -TERM $CLAUDE_PID`, detached; if the variable is
   empty, ask the user to type `/exit`).

---

# Code graph

For codebase questions, first run `graphify query "<question>" --budget 4000`. Use `graphify explain "<Symbol>"`
and `graphify path "<A>" "<B>"` for focused questions, `graphify affected "<Symbol>"` before refactoring.
