---
id: SPEC-SVELTEKIT-PB
kind: spec
title: ImperioCasino — SvelteKit + PocketBase Port
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
checksum: ee5b1b35903423d7f2fce115cfebb38a939aaa011bec550d8edbabc79e41a96b

## Overview

Port the existing Flask + React/jQuery casino platform (Blackjack, Roulette, 3D Slots) to a single SvelteKit app backed by PocketBase (auth + DB), with an abstraction layer for future Supabase migration.

## Key Decisions

| Decision | Choice |
|----------|--------|
| App structure | Single SvelteKit app, monorepo layout |
| Game logic location | SvelteKit server endpoints (TypeScript) |
| 3D slot engine | Threlte (Svelte-native Three.js) |
| Auth + DB | PocketBase Go binary |
| DB abstraction | Adapter interface → swap PocketBase for Supabase later |

## Directory Structure

```
ImperioCasino/
├── pocketbase/              # PB binary + pb_data/
├── src/
│   ├── routes/
│   │   ├── +layout.svelte       # Auth guard + nav shell
│   │   ├── +page.svelte         # Lobby/dashboard
│   │   ├── login/
│   │   ├── signup/
│   │   ├── blackjack/
│   │   ├── roulette/
│   │   └── slots/               # Cherry-Charm (Threlte)
│   ├── lib/
│   │   ├── server/
│   │   │   ├── db/
│   │   │   │   ├── adapter.ts       # Interface: getCoins, setCoins, addCoins, etc.
│   │   │   │   ├── pocketbase.ts    # PocketBase implementation
│   │   │   │   └── supabase.ts      # Future Supabase implementation (not yet created)
│   │   │   ├── games/
│   │   │   │   ├── blackjack.ts     # Deck, shuffle, hit, stand, split, payout
│   │   │   │   ├── roulette.ts      # Bet validation, spin, payout
│   │   │   │   └── slots.ts         # Reel spin, segment mapping, payouts
│   │   │   └── auth.ts              # Auth helpers (PocketBase wrapper)
│   │   ├── components/
│   │   │   ├── Nav.svelte
│   │   │   ├── CoinBalance.svelte
│   │   │   ├── Card.svelte
│   │   │   ├── ChipSelector.svelte
│   │   │   ├── BlackjackBoard.svelte
│   │   │   ├── ResultModal.svelte
│   │   │   ├── SlotMachine.svelte
│   │   │   ├── SlotCasing.svelte
│   │   │   ├── SlotLights.svelte
│   │   │   ├── Reel.svelte
│   │   │   └── ...
│   │   └── types.ts              # Shared types
│   ├── hooks.server.ts        # PocketBase per-request setup + auth restore
│   ├── app.d.ts               # App.Locals type declarations
│   ├── app.css                # Global styles
│   └── app.html               # HTML shell
├── static/
│   ├── models/               # GLB files for Threlte slot machine
│   └── images/               # Card faces, chip textures
├── package.json
└── svelte.config.js
```

## PocketBase Schema

**Collection: `users`** (built-in auth)
- `username` (text, unique)
- `coins` (number, default 100) — custom field
- Email/password via PB native auth

**Collection: `blackjack_games`**
- `user` (relation → users)
- `deck` (json)
- `dealer_hand` (json)
- `player_hand` (json)
- `player_second_hand` (json, nullable)
- `player_coins` (number)
- `current_wager` (number)
- `game_over` (bool)
- `message` (text, nullable)
- `player_stood` (bool)
- `double_down` (bool)
- `split` (bool)
- `current_hand` (text: "first"|"second")
- `dealer_value` (number)

## Auth Flow

1. `hooks.server.ts` loads PocketBase instance per request, restores auth from `pb_auth` cookie
2. `event.locals.pb` and `event.locals.user` available in all server load/actions
3. Signup: `pb.collection('users').create(...)` + login
4. Login: `pb.collection('users').authWithPassword(email, password)`
5. Auth guard in `+layout.server.ts`: redirect to `/login` if unauthenticated
6. No manual JWT handling — PocketBase SDK manages cookies

## Game Logic Port

All Python game logic ported to TypeScript in `$lib/server/games/`:

### Blackjack (`blackjack.ts`)
- `createDeck()` — 6-deck shoe (312 cards), standard suits/values
- `calculateHandValue(hand)` — Ace adjusts 11→1 on bust
- `shuffleDeck()` — Fisher-Yates
- `startGame(user, wager)` — deal starting hands
- `playerHit()`, `playerStand()`, `playerDoubleDown()`, `playerSplit()`
- `dealerTurn()` — dealer hits until ≥17
- `determineWinner()` — payout logic, split hand handling

### Roulette (`roulette.ts`)
- `spinWheel()` — pick random 0-36
- `validateBets(bets)` — check numbers, odds, amounts
- `calculatePayouts(bets, winningNumber)` — per-bet payout calc

### Slots (`slots.ts`)
- `spinReels()` — generate 3 random segments (15-30 range)
- `segmentToFruit(reelIndex, segment)` — maps half-segment → Fruit enum
- `calculatePayout(fruits)` — payout table (3 cherries=50, 2 cherries=40, etc.)

## API Endpoints (SvelteKit Form Actions + Server routes)

| Route | Method | Purpose |
|-------|--------|---------|
| `/login` | GET/POST | Login form + auth |
| `/signup` | GET/POST | Register form + auth |
| `/` | GET | Lobby/dashboard with coin balance |
| `/blackjack` | GET | Blackjack page (loads game state) |
| `/blackjack/start` | POST | Start new game (wager) |
| `/blackjack/action` | POST | Hit/stand/double/split |
| `/roulette` | GET | Roulette page |
| `/roulette/spin` | POST | Place bets + spin |
| `/slots` | GET | Slot machine page |
| `/slots/spin` | POST | Spin reels |

## DB Abstraction Layer

Interface in `$lib/server/db/adapter.ts`:

```typescript
export interface DBAdapter {
  getUser(id: string): Promise<User>
  getUserByUsername(username: string): Promise<User | null>
  getCoins(userId: string): Promise<number>
  addCoins(userId: string, amount: number): Promise<number>
  deductCoins(userId: string, amount: number): Promise<number>
  setCoins(userId: string, amount: number): Promise<number>
  createBlackjackGame(userId: string, state: BlackjackState): Promise<string>
  updateBlackjackGame(gameId: string, state: Partial<BlackjackState>): Promise<void>
  getBlackjackGame(gameId: string): Promise<BlackjackState>
}
```

`PocketBaseAdapter` implements this. `SupabaseAdapter` will implement it later.

## Frontend

- Uses `@sveltejs/kit`, Svelte 5 runes (`$state`, `$derived`, `$effect`)
- Dashboard: game selection grid showing Blackjack, Roulette, Slots
- Blackjack: ported from jQuery/HTML — clean Svelte components (Card, Hand, ChipSelector, GameBoard)
- Roulette: ported from vanilla JS — betting grid, wheel animation (CSS), history strip
- Slots: Threlte scene — 3D reel models, spin animation, fruit result overlay
- Shared: Nav bar, coin balance display (live-updating via `$page.data`)

## Deck Cards Images

- Card face images from `static/images/` — same naming: `Hearts-Ace.png`, `Clubs-King.png`, etc.
- Card back: `back.png`
