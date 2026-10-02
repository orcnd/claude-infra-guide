# 6. Code graph (graphify)

## Why

Four repos, PHP and TypeScript, calls across repos (frontend service -> API route -> controller -> table).
Claude grepped and read dozens of files per question. [graphify](https://pypi.org/project/graphifyy/) builds a
graph from the AST (about 9k nodes, 25k edges here) and Claude pulls only the relevant subgraph.

```mermaid
flowchart LR
    subgraph BEFORE["Without the graph"]
        Q1["question"] --> G1["grep"] --> R1["read 10-30 files"] --> G2["grep again"] --> A1["answer,<br/>context mostly spent"]
    end
    subgraph AFTER["With the graph"]
        Q2["question"] --> GQ["graphify query"] --> SG["subgraph with file:line"] --> RF["read 2-4 files"] --> A2["answer"]
    end
```

## Setup

```bash
uv tool install graphifyy
graphify install --platform claude        # /graphify skill
cd ~/code/project && graphify update .    # AST only, no LLM cost
```

`.graphifyignore` keeps out WordPress, vendor code, images and minified files. Minified files filled the graph
with one-letter symbols, so they went first.

## Queries

```mermaid
flowchart TD
    Q{"question type"} -->|"how does X work"| A["graphify query ... --budget 4000"]
    Q -->|"what is this symbol"| B["graphify explain Symbol"]
    Q -->|"how are A and B connected"| C["graphify path A B"]
    Q -->|"what breaks if I change it"| D["graphify affected Symbol"]
    A --> R{"enough?"}
    B --> R
    C --> R
    D --> R
    R -- yes --> E["read the files it names"]
    R -- no --> F["targeted grep"]
```

- The default 2000-token budget cuts architecture answers short; use 4000.
- Builtins like `trim` and `json_decode` flood broad queries; `explain` and `path` stay focused.
- Nodes with no source file are builtins.

## Steering Claude

- CLAUDE.md: graph first for code questions.
- A hook (`graphify hook-guard`) reminds Claude before `Grep`, `Glob`, `Read` or a search in `Bash`.
- Graph commands need no approval.

## Keeping it fresh

```mermaid
sequenceDiagram
    participant D as Developer or Claude
    participant G as git
    participant H as post-commit hook
    participant GR as graphify

    D->>G: commit
    G->>H: run hook
    H-)GR: graphify update . (background)
    H-->>G: exit 0
    G-->>D: done, no wait
    GR->>GR: re-extract changed files
```

Template: [templates/git-hooks/post-commit](../templates/git-hooks/post-commit).
