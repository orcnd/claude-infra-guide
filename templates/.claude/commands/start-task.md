---
description: Open an isolated parallel workspace for a Jira task and load its details
argument-hint: <task-number>
---

**Language:** Reply to the user in `<your team's language>` for the whole conversation that starts
with this command: step narration, the ticket summary, the workspace summary, questions and every later
message. Code, commands, file paths, URLs, branch names and Jira field names stay as they are. Drop this
rule if the user asks for another language.

Start work on Jira task **$1** in its own isolated workspace, so other tasks can stay open
in parallel. Follow these steps in order and do not skip the stop at the end.

1. Run `ws ls` and show the user which task workspaces are already open.
2. Run `ws create $1 --yes`. This creates the `feature/task-$1` branches, two git worktrees under
   `~/code/tasks/task-$1/`, the `.env.local` files, and the nginx vhost. The
   `~/code/project/` checkouts are deliberately left untouched.
   If it fails because DNS or the certificate is missing, run `ws setup` and relay its sudo
   commands to the user - do not improvise a workaround.
3. Run `ws up $1` to start that task's Next dev server on its own port, detached.
   Then record the active task for this session so `/stop-task` can find it without an argument:
   ```bash
   mkdir -p ~/code/tasks/.sessions && echo $1 > ~/code/tasks/.sessions/$CLAUDE_CODE_SESSION_ID
   ```
4. **Switch context.** Every file you read or edit, and every command you run, for this task must be
   under `~/code/tasks/task-$1/`. Treat
   `~/code/project/api` and `.../web` as off-limits here -
   they are the shared source checkouts and another session may be using them.
   `legacy/` and `cms/` inside the workspace are symlinks to shared copies: say so before editing them.
   MySQL, Redis and php-fpm are shared across tasks - never run migrations or flush Redis without
   first telling the user which other tasks are open.
5. Run `ws jira $1` and display the task details.
6. Print the workspace summary: workspace path, frontend `https://$1.ws.test:8443`, API
   `https://api-$1.ws.test:8443`.
7. Ask: "What do you want to do with this task? Is there any context to add before we start?" -
   then **stop and wait**. Do not read code, plan, or change anything until the
   user answers.
8. After the user answers, and before any code: build the acceptance checklist. A skipped ticket
   item caused more UAT returns than anything else (see `docs/05-verification-and-uat-gate.md` in this guide).
   - Run `ws checklist $1 round`; it prints the description and comments.
   - Add one item per concrete, checkable requirement, with the page it shows on:
     `ws checklist $1 add "Product table has a price filter" --page /products`.
     Split numbered lists and "also ..." sentences into separate items. Linked Sheets rows count too.
   - Tell the user in 3-6 lines how you understood the task and list open questions, then show
     `ws checklist $1`. Wait for their confirmation before writing code.
