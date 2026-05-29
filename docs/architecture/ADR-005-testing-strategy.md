---
id: ADR-005
kind: adr
title: Testing Strategy
status: accepted
authors: [Jonathan Gadea Harder]
reviewers: [Jonathan Gadea Harder]
tags: []
supersedes: []
superseded_by: []
depends_on: []
blocks: []
implements: []
related: []
external: []
project: ImperioCasino
checksum: 2f40a285b9175cdf0b8803815ac3e1c6d460e578733dbd573316fc6c9b511e88
---

**Context:** Casino games require high correctness guarantees. Bugs in payout calculations, deck shuffling, or bet validation can cause financial losses. The testing strategy must cover game logic, integration, and 3D rendering.

**Decision:** Use Vitest for unit and integration tests with @testing-library/svelte for component tests. Game logic modules are pure TypeScript with no mocking needed. Database adapter tests use an in-memory implementation. 3D slot tests focus on payout calculation, not visual rendering.

**Consequences:**
- Positive: Game logic tests are fast (no I/O, no DOM)
- Positive: Component tests catch UI/state issues
- Negative: 3D rendering is largely untested (visual diffing not worth the cost)
- Negative: Coverage thresholds may give false confidence if game edge cases missed

**Alternatives:**
- Playwright E2E: Catches integration bugs but slower, harder to debug
- Manual testing only: Insufficient for payout correctness
