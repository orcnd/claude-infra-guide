---
description: Stop a task workspace's dev server, warn about uncommitted work, then end the session
argument-hint: [task-number, optional - defaults to the task started with /start-task]
---

**Language:** Reply in `<your team's language>`. Code, commands, file paths, URLs and branch names
stay as they are.

Finish work on the active Jira task (task $1 if given) and close this session, as if the user had typed `/exit`.
Follow these steps in order. Do not skip the uncommitted-changes stop.

0. **Resolve the task number.** Do not ask the user for it. In this order:
   - `$1` if it was given;
   - otherwise the session marker written by `/start-task`:
     `cat ~/code/tasks/.sessions/$CLAUDE_CODE_SESSION_ID`;
   - otherwise the `tasks/task-<n>/` workspace this conversation has been working in.
   Only if all three fail, ask the user which task to stop and wait.
   Below, `<n>` is that number and `<ws>` is `~/code/tasks/task-<n>`.

1. **Stop the dev server.** Run `ws down <n>`. If a verification build is running
   (`<ws>/.ws/verify-restore` exists), `ws down` still stops it; do not run
   `ws verify <n> --end` first. Never run `ws rm` - worktrees and branches stay.

2. **Check for uncommitted work.** Run, for each of the two worktrees:
   ```bash
   git -C <ws>/api status --porcelain
   git -C <ws>/web status --porcelain
   ```
   Also check whether the shared checkouts were touched during this task (they are symlinks in the
   workspace, so edits there are shared):
   ```bash
   git -C ~/code/project/legacy status --porcelain
   git -C ~/code/project/cms status --porcelain
   ```
   - If **all four are empty**, go to step 3.
   - If **any is non-empty**, print a warning listing every changed file grouped by repo, then
     **stop and wait**. Ask the user whether to (a) commit now - show the proposed
     commit message and file list and wait for explicit approval before running `git commit`,
     (b) leave the changes in place and exit anyway, or (c) cancel the stop. Do not exit until
     the user has chosen. Never stash, reset, or discard anything.

3. **Print the closing summary**: task key, branch name, that the server is down,
   the commit state of each worktree (clean / N uncommitted files left in place), and whether
   the branch has commits not yet pushed (`git -C <ws>/api log --oneline @{u}..` and
   the same for the frontend; if there is no upstream, say so). This summary is the last thing
   the user sees, so it must stand on its own.

4. **End the session.** There is no tool for `/exit`, so terminate the Claude Code process from
   the shell, detached and after a short delay so the summary above is flushed first:
   ```bash
   nohup sh -c "sleep 2; kill -TERM $CLAUDE_PID" >/dev/null 2>&1 &
   ```
   Before it, remove the session marker: `rm -f ~/code/tasks/.sessions/$CLAUDE_CODE_SESSION_ID`.
   Run this only after steps 1-3 are done and there are no unresolved uncommitted changes. Do not
   write anything after this command; the session is over.
   If `$CLAUDE_PID` is empty (check with `echo "$CLAUDE_PID"` first), do not run `kill`; end the summary
   by asking the user to type `/exit`.
