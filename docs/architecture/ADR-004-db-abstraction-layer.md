---
id: ADR-004
kind: adr
title: Database Abstraction Layer for Future Migration
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
checksum: 42b282ffe8bd1c0ab3b208be89bc234f5f8046125ce26daa44f9763c818fc4e5
---

**Context:** The initial backend uses PocketBase for speed of development. However, for production scale, Supabase or another cloud database may be needed. The architecture should not couple tightly to PocketBase APIs.

**Decision:** Define a database adapter interface in `src/lib/server/db/adapter.ts` with methods for all data operations (getCoins, updateCoins, createUser, etc.). PocketBase implements this interface initially. A future Supabase implementation can be swapped in without changing game logic.

**Consequences:**
- Positive: Zero changes to game logic when switching databases
- Positive: Clear boundary between storage and application logic
- Positive: Simplifies testing (mock the adapter interface)
- Negative: Interface may need breaking changes if PocketBase/Supabase APIs diverge
- Negative: Slightly more boilerplate than direct PocketBase calls

**Alternatives:**
- Direct PocketBase calls: Faster initially, coupling makes migration painful
- Supabase from start: More production-ready but heavier for prototyping
