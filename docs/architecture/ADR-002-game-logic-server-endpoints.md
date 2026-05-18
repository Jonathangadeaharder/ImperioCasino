---
id: ADR-002
kind: adr
title: Game Logic in SvelteKit Server Endpoints
status: draft
authors: []
reviewers: []
tags: []
supersedes: []
superseded_by: []
depends_on: []
blocks: []
implements: []
related: []
external: []
project: ImperioCasino
checksum: 343003e763d8eeddbc686a1831d2677c523ae61b3a4b605bb1b08ff655b5e8b6
---

**Context:** Casino games (blackjack, roulette, slots) require server-side logic to prevent client tampering. The game state and payout calculations must be authoritative.

**Decision:** All game logic lives in SvelteKit server endpoints under `src/lib/server/games/`. Each game module is a pure TypeScript module with no client-side dependencies. The client sends actions to endpoints which validate, execute, and return results. Game state is ephemeral (server memory) for active sessions and persisted to PocketBase for balances.

**Consequences:**
- Positive: Game logic is testable without browser/DOM
- Positive: Prevents client-side manipulation of outcomes
- Positive: Clean separation of game rules from UI
- Negative: State lost on server restart (mitigated by periodic persistence)
- Negative: Network latency for each game action vs local computation

**Alternatives:**
- Client-side with server validation: More complex, still needs server logic
- WebSocket real-time: Over-engineered for turn-based casino games
