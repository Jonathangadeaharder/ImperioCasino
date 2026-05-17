# AGENTS.md — ImperioCasino

## Build & Test Commands

```bash
pnpm install
pnpm run dev
pnpm run build
pnpm run check
pnpm exec vitest run
pnpm exec tsc --noEmit
pnpm dlx @biomejs/biome check
```

Backend (Python):
```bash
cd session_management
uv sync
uv run pytest
uvx ruff check
uvx ruff format
uvx pyright
```

## PR Instructions

- Branch: feature/*, fix/*, chore/*
- Title: `<type>(<scope>): <description>`
- Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore
- Run `pnpm run check` + backend lints before committing
- One logical change per commit
