---
paths:
  - "web/**"
---

<!-- Example of a path-scoped rule file. Loaded only when a file under web/ is read.
     Keep repo reference here, not in the root CLAUDE.md. Replace every section with your own. -->

# web/ - Next.js frontend

App Router, React, TypeScript, next-intl (7 locales).

## Folder structure

| Path | Holds |
|---|---|
| `src/app/[locale]/` | Routes |
| `src/services/` | One file per API resource; the only place that calls the API |
| `src/types/` | Response types, one per service |
| `src/components/` | UI; no data fetching here |
| `messages/<locale>.json` | Translation strings |

## New page checklist

1. Service function in `src/services/`
2. Types in `src/types/`
3. Mock data for local work
4. Route and page component
5. Translation keys in every locale file (`ws i18n <n>` checks parity)

## Code standards

- All UI text through `useTranslations()` / `getTranslations()`; no literal strings in components.
- Use the shared axios instance; never call `fetch` against the API directly.
- Do not edit generated files (icons, API clients); run the generator.

## Task dev server

| | dev (default) | verification build |
|---|---|---|
| Started by | `ws up <n>` | `ws verify <n>` |
| Edits picked up | immediately (HMR) | only via `ws rebuild <n>` |
| When | all development | one pass before pushing |

Always end a verification session with `ws verify <n> --end`; a build server ignores edits.

Logs: `~/code/tasks/task-<n>/.ws/server.log` (runtime) and `.ws/build.log` (route table, build errors).
Read them before guessing why a page is broken.
