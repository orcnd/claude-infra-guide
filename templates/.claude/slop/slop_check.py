#!/usr/bin/env python3
"""AI-slop checker for agent-written text. Hooks make the agent fix findings (SLOP_MODE=warn to only report).

CLI:
  slop_check.py FILE [FILE...]      check whole files (code files: comments only)
  slop_check.py -                   check stdin as plain text (rendered page text, a draft)
  slop_check.py --json ...          machine-readable output
  Exit code: 0 clean, 1 findings.

Claude Code hooks (reads the hook payload from stdin, always exits 0):
  slop_check.py --hook post-edit    PostToolUse Edit|Write|MultiEdit - only the added lines
  slop_check.py --hook pre-bash     PreToolUse Bash - git commit / gh pr messages
  slop_check.py --hook stop         Stop - the assistant's last chat reply

Rules live next to this file in rules.txt.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES_FILE = HERE / "rules.txt"
MAX_REPORTED = 15

# Files whose every line is prose.
PROSE_EXT = {".md", ".txt", ".tpl", ".html", ".twig"}
# Files where only comments are prose (plus the prose-path exceptions below).
CODE_EXT = {".php", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".scss", ".css", ".py", ".sh", ".sql"}
PROSE_PATH_RE = re.compile(r"(/messages/[a-z]{2}\.json$|/resources/lang/[a-z]{2}/[^/]+\.php$)")
SKIP_PATH_RE = re.compile(
    r"(/node_modules/|/vendor/|/graphify-out/|/\.next/|/\.claude/slop/|/Icons/|"
    r"\.min\.(js|css)$|package-lock\.json$|composer\.lock$|/public/build/)"
)
COMMENT_LINE_RE = re.compile(r"^\s*(//|#(?!\[)|\*|/\*|\{/\*|<!--|--\s)")
TRAILING_COMMENT_RE = re.compile(r"\s(//|#)\s+(.*)$")

DASH_RE = re.compile("[—–]")
BOLD_LEAD_RE = re.compile(r"^\s*([-*]|\d+\.)\s+\*\*[^*]{1,60}\*\*\s*[:\-]")
EMOJI_BULLET_RE = re.compile("^\\s*([-*]\\s*)?[\U0001F300-\U0001FAFF☀-➿]")


@dataclass
class Rule:
    lang: str
    pattern: re.Pattern[str]
    source: str
    hint: str


@dataclass
class Finding:
    line: int
    text: str
    match: str
    hint: str
    lang: str


def load_rules() -> list[Rule]:
    """Parse rules.txt into compiled rules."""
    rules: list[Rule] = []
    lang = "all"
    for raw in RULES_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        section = re.fullmatch(r"\[([a-z]+)\]", line)
        if section:
            lang = section.group(1)
            continue
        src, _, hint = line.partition(" => ")
        src = src.strip()
        anchored = src.startswith("^")
        body = src[1:] if anchored else src
        regex = ("^" if anchored else r"(?<!\w)") + body
        try:
            rules.append(Rule(lang, re.compile(regex, re.IGNORECASE | re.MULTILINE), src, hint.strip()))
        except re.error as exc:
            print(f"slop: bad rule {src!r}: {exc}", file=sys.stderr)
    return rules


def check_lines(lines: list[tuple[int, str]], rules: list[Rule], markdown: bool) -> list[Finding]:
    """Run phrase rules and structural checks over numbered lines."""
    findings: list[Finding] = []
    for no, text in lines:
        if "slop-ok" in text:  # author vouched for this line (quoted example, product name)
            continue
        if DASH_RE.search(text):
            findings.append(Finding(no, text, DASH_RE.search(text).group(0), "em/en dash, use a plain hyphen", "all"))
        taken: list[tuple[int, int]] = []  # one warning per phrase, first rule wins
        for rule in rules:
            m = rule.pattern.search(text)
            if m and not any(m.start() < e and s < m.end() for s, e in taken):
                taken.append(m.span())
                findings.append(Finding(no, text, m.group(0), rule.hint, rule.lang))
        emoji = EMOJI_BULLET_RE.search(text) if markdown else None
        if emoji:
            findings.append(Finding(no, text, emoji.group(0).strip(" -*"), "emoji used as a bullet", "all"))

    if markdown:
        run: list[tuple[int, str]] = []
        for no, text in lines + [(-1, "")]:
            if BOLD_LEAD_RE.search(text) and (not run or no == run[-1][0] + 1):
                run.append((no, text))
                continue
            if len(run) >= 4:
                findings.append(Finding(
                    run[0][0], run[0][1], f"{len(run)} items",
                    "every bullet opens with **Bold**: - write some as plain sentences", "all",
                ))
            run = [(no, text)] if BOLD_LEAD_RE.search(text) else []
    return sorted(findings, key=lambda f: f.line)


def prose_lines(path: str, text: str, first_line: int = 1) -> tuple[list[tuple[int, str]], bool]:
    """Return the prose lines of a file body and whether it is markdown-like."""
    ext = Path(path).suffix.lower()
    if ext == ".md":
        text = strip_markdown_code(text)  # quoted examples in `code` are not prose
    numbered = list(enumerate(text.splitlines(), start=first_line))
    if PROSE_PATH_RE.search(path) or ext in PROSE_EXT:
        return numbered, ext == ".md"
    if ext in CODE_EXT:
        out = []
        for no, line in numbered:
            if COMMENT_LINE_RE.match(line):
                out.append((no, line))
            else:
                m = TRAILING_COMMENT_RE.search(line)
                if m and "://" not in line[max(0, m.start() - 6):m.start() + 3]:
                    out.append((no, m.group(2)))
        return out, False
    return [], False


def strip_markdown_code(text: str) -> str:
    """Blank out fenced blocks, inline code and URLs so they are not checked."""
    text = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.DOTALL)
    text = re.sub(r"`[^`\n]*`", "", text)
    return re.sub(r"https?://\S+", "", text)


def format_findings(findings: list[Finding], label: str) -> str:
    """Human-readable warning block."""
    out = [f"AI-slop warning ({label}): {len(findings)} pattern(s). Rewrite if the phrase adds nothing."]
    for f in findings[:MAX_REPORTED]:
        snippet = f.text.strip()
        if len(snippet) > 110:
            i = max(0, snippet.lower().find(f.match.lower()) - 40)
            snippet = ("..." if i else "") + snippet[i:i + 110] + "..."
        out.append(f"  L{f.line}: \"{f.match}\" -> {f.hint}\n        {snippet}")
    if len(findings) > MAX_REPORTED:
        out.append(f"  ... and {len(findings) - MAX_REPORTED} more")
    return "\n".join(out)


# ---------------------------------------------------------------- hooks

def added_lines(new: str, old: str) -> str:
    """Lines of `new` that do not appear in `old` (order kept)."""
    old_set = set(old.splitlines())
    return "\n".join(l for l in new.splitlines() if l not in old_set)


def git_head_version(path: str) -> str:
    """Committed content of a file, or '' when untracked / not in git."""
    p = Path(path)
    try:
        top = subprocess.run(["git", "-C", str(p.parent), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=3).stdout.strip()
        if not top:
            return ""
        rel = os.path.relpath(p.resolve(), Path(top).resolve())
        return subprocess.run(["git", "-C", top, "show", f"HEAD:{rel}"],
                              capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return ""


def hook_post_edit(payload: dict, rules: list[Rule]) -> str | None:
    """Check only what an Edit/Write/MultiEdit added."""
    ti = payload.get("tool_input", {})
    path = ti.get("file_path", "")
    if not path or SKIP_PATH_RE.search(path):
        return None
    tool = payload.get("tool_name", "")
    if tool == "Write":
        body = added_lines(ti.get("content", ""), git_head_version(path))
    elif tool == "MultiEdit":
        body = "\n".join(added_lines(e.get("new_string", ""), e.get("old_string", "")) for e in ti.get("edits", []))
    else:
        body = added_lines(ti.get("new_string", ""), ti.get("old_string", ""))
    lines, md = prose_lines(path, body)
    findings = check_lines(lines, rules, md)
    if not findings:
        return None
    # Line numbers refer to the added snippet, not the file.
    return format_findings(findings, f"added text in {Path(path).name}, line numbers are within the edit")


def hook_pre_bash(payload: dict, rules: list[Rule]) -> str | None:
    """Check commit messages and PR bodies inside a Bash command."""
    cmd = payload.get("tool_input", {}).get("command", "")
    # Only a command that actually runs: at the start of a line or after ; & | ( - not the words
    # "git commit" inside an echo, a test payload or a grep pattern.
    m = re.search(r"(?:^|[;&|(]|\n)\s*(?:git(?:\s+-C\s+\S+)?\s+commit\b|gh\s+pr\s+(?:create|edit)\b)", cmd)
    if not m:
        return None
    text = cmd[m.start():]
    text = re.sub(r"Co-Authored-By:.*", "", text)
    findings = check_lines(list(enumerate(text.splitlines(), 1)), rules, markdown=True)
    return format_findings(findings, "commit / PR message") if findings else None


def last_assistant_text(transcript_path: str) -> str:
    """Text the assistant wrote since the last real user message."""
    texts: list[str] = []
    try:
        with open(transcript_path, encoding="utf-8") as fh:
            for raw in fh:
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                msg = entry.get("message") or {}
                content = msg.get("content")
                if entry.get("type") == "user":
                    # Only a real human prompt starts a new turn; tool results, reminders,
                    # subagent hand-backs and task notifications are also "user" entries.
                    is_tool_result = isinstance(content, list) and any(
                        isinstance(c, dict) and c.get("type") == "tool_result" for c in content)
                    origin = (entry.get("origin") or {}).get("kind")
                    if not is_tool_result and not entry.get("isMeta") and origin in (None, "human"):
                        texts = []
                elif entry.get("type") == "assistant" and isinstance(content, list):
                    texts += [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
    except OSError:
        return ""
    return "\n".join(texts)


def hook_stop(payload: dict, rules: list[Rule]) -> str | None:
    """Check the final chat reply of the turn."""
    text = strip_markdown_code(last_assistant_text(payload.get("transcript_path", "")))
    if not text.strip():
        return None
    findings = check_lines(list(enumerate(text.splitlines(), 1)), rules, markdown=True)
    return format_findings(findings, "last reply") if findings else None


# "block" (default) makes the agent fix what it wrote; "warn" only reports. SLOP_MODE=warn
# is the escape hatch when a rule misfires in bulk.
MODE = os.environ.get("SLOP_MODE", "block")

FIX_EDIT = ("Fix these lines now with another edit: rewrite each flagged phrase plainly (say the concrete "
            "thing, or drop it), do not swap in a synonym. If a match is a false positive (a quoted example, "
            "a product name), append `slop-ok` in a comment on that line.")
FIX_COMMIT = "Commit refused. Rewrite the message without these patterns and run the command again."
FIX_REPLY = ("Your reply above contains these patterns. Send the reply again with the flagged sentences "
             "rewritten plainly; keep everything else the same and do not mention this check.")


def run_hook(kind: str) -> int:
    """Dispatch a hook event and print the JSON Claude Code expects."""
    try:
        payload = json.load(sys.stdin)
        rules = load_rules()
        if kind == "post-edit":
            msg = hook_post_edit(payload, rules)
        elif kind == "pre-bash":
            msg = hook_pre_bash(payload, rules)
        elif kind == "stop":
            msg = hook_stop(payload, rules)
        else:
            return 0
    except Exception as exc:  # a broken checker must never break the session
        print(f"slop hook error: {exc}", file=sys.stderr)
        return 0
    if not msg:
        return 0

    block = MODE == "block"
    if kind == "post-edit":
        out = ({"decision": "block", "reason": f"{msg}\n{FIX_EDIT}"} if block else
               {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}})
    elif kind == "pre-bash":
        out = {"hookSpecificOutput": {"hookEventName": "PreToolUse", **(
            {"permissionDecision": "deny", "permissionDecisionReason": f"{msg}\n{FIX_COMMIT}"} if block else
            {"additionalContext": msg})}}
    else:
        # stop_hook_active: the agent is already re-answering because of this hook. Warn only,
        # so a rule the agent cannot satisfy never loops the turn.
        if block and not payload.get("stop_hook_active"):
            out = {"decision": "block", "reason": f"{msg}\n{FIX_REPLY}"}
        else:
            out = {"systemMessage": msg}
    print(json.dumps(out, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- CLI

def main(argv: list[str]) -> int:
    """CLI entry point."""
    if len(argv) >= 2 and argv[0] == "--hook":
        return run_hook(argv[1])
    as_json = "--json" in argv
    targets = [a for a in argv if a != "--json"] or ["-"]
    rules = load_rules()
    total = 0
    report: dict[str, list[dict]] = {}
    for target in targets:
        if target == "-":
            text = sys.stdin.read()
            lines, md = list(enumerate(text.splitlines(), 1)), True
        else:
            text = Path(target).read_text(encoding="utf-8", errors="replace")
            lines, md = prose_lines(target, text)
        findings = check_lines(lines, rules, md)
        total += len(findings)
        if as_json:
            report[target] = [f.__dict__ for f in findings]
        elif findings:
            print(format_findings(findings, "stdin" if target == "-" else target))
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    elif not total:
        print("slop: clean")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
