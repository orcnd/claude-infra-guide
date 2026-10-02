---
name: status
description: Use when the user asks what their current situation or workload is - "durum ne", "durum nedir", "neredeyiz", "bugün ne var", "nelerim var", "what's my status", "where do things stand", "what's on my plate" - or asks which tickets came back from UAT, which need action, or what to pick up next. Produces the working list from Jira, task workspaces and past Claude sessions.
---

<!-- The Turkish trigger phrases in the description are examples: list the phrases your team actually types, in every language they use. -->

# Status

Answer "where do things stand" with the list the user actually acts on, not a Jira dump.

**Reply in the language the user asked in.**

## Get the data

One command has everything - Jira tickets, workspace state, uncommitted files, past
Claude sessions:

```bash
ws board --json
```

Takes ~3 seconds. Do not query Jira separately, do not run `ws ls`, do not grep
`~/.claude/projects/` yourself - `ws board` already joined all three.

Each ticket carries:

| Field | Meaning |
|---|---|
| `key`, `summary`, `status`, `updated`, `url` | Jira |
| `workspace.exists` | Is there an `tasks/task-<n>/` workspace |
| `workspace.running`, `workspace.mode` | Is the dev server up, and in `dev`/`prod`/`verify` |
| `workspace.branch`, `workspace.url` | Feature branch and local frontend URL |
| `dirty` | Uncommitted files across both worktrees (`null` = no worktree) |
| `sessions`, `lastSession` | How many past Claude sessions worked this ticket, and when |

`resumeStatus` at the top is the status that counts as "back to me" - `RETURNED`.

## What to report

Lead with what needs action. Order:

1. **Returned from UAT** (`status == resumeStatus`) - these came back from UAT and are the answer to
   "where do things stand". Always list all of them.
2. **Unfinished work** - any ticket with `dirty > 0`. Uncommitted work is the thing most
   easily lost between sessions; name the ticket and the file count.
3. **Servers still running** - `workspace.running == true`. Note them briefly; a forgotten
   `verify` mode server is worth flagging outright, because it serves a stale build and
   makes later edits look like they do nothing.
4. **Other statuses** - one line per status with counts, not every ticket. Expand only if
   the user asks.

For each ticket you list: key, short summary, and the state that matters - workspace up or
down, uncommitted count, how long since the last session. Skip fields that say nothing.

## Judgment

- The user has 30+ open tickets. A wall of them is not an answer. Five actionable ones plus
  a count line for the rest is.
- `sessions: 0` on a ticket in `RETURNED` means it was worked somewhere else or long
  ago - worth calling out, since `ws resume` will find nothing to reopen.
- `workspace.exists: false` on a ticket that needs work means `ws create <n>` comes first.
- Close by pointing at the next move: `ws resume` reopens a past session for a ticket in a
  new terminal tab, `ws create <n>` / `ws up <n>` sets one up from scratch.
- If the user names a ticket, run `ws jira <KEY>` for its full description and comments
  rather than working from the one-line summary.

## Related commands

| | |
|---|---|
| `ws board` | Same snapshot, human-readable |
| `ws resume` | pick a returned ticket, pick a past session, reopen it in a new terminal tab |
| `ws resume <KEY\|n>` | Skip the ticket picker |
| `ws jira <KEY>` | Full ticket with comments |
