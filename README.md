# ImperioCasino

Multi-game online casino. Blackjack, Roulette, 3D Slots (Threlte/Three.js). SvelteKit + PocketBase.

## Architecture

```
ImperioCasino/
├── src/
│   ├── routes/               # SvelteKit pages
│   │   ├── +layout.svelte    # App shell (nav + auth guard)
│   │   ├── +page.svelte      # Lobby/dashboard
│   │   ├── blackjack/        # Blackjack game
│   │   │   ├── start/        # POST — start game
│   │   │   └── action/       # POST — hit/stand/double/split
│   │   ├── roulette/         # Roulette game
│   │   │   └── spin/         # POST — place bets + spin
│   │   ├── slots/            # 3D slot machine (Threlte)
│   │   │   └── spin/         # POST — spin reels
│   │   ├── login/            # Auth (form action)
│   │   ├── signup/           # Registration (form action)
│   │   └── logout/           # Logout (form action)
│   ├── lib/
│   │   ├── components/       # Shared UI components
│   │   │   ├── Nav.svelte
│   │   │   ├── CoinBalance.svelte
│   │   │   ├── Card.svelte
│   │   │   ├── ChipSelector.svelte
│   │   │   ├── BlackjackBoard.svelte
│   │   │   ├── ResultModal.svelte
│   │   │   ├── SlotMachine.svelte
│   │   │   ├── SlotCasing.svelte
│   │   │   ├── SlotLights.svelte
│   │   │   └── Reel.svelte
│   │   ├── server/
│   │   │   ├── db/           # DB abstraction layer
│   │   │   │   ├── adapter.ts    # DBAdapter interface
│   │   │   │   └── pocketbase.ts # PocketBase implementation
│   │   │   ├── games/        # Server-side game logic
│   │   │   │   ├── blackjack.ts
│   │   │   │   ├── roulette.ts
│   │   │   │   └── slots.ts
│   │   │   └── auth.ts       # Auth helpers (signup, login)
│   │   └── types.ts          # Shared TypeScript types
│   ├── hooks.server.ts       # PocketBase per-request setup
│   ├── app.d.ts              # App.Locals type declarations
│   ├── app.html              # HTML shell
│   └── app.css               # Global styles
├── pocketbase/               # PocketBase binary + pb_data
├── scripts/                  # Setup scripts (PocketBase download + schema)
├── static/                   # Static assets (images, 3D models)
│   ├── images/               # Card faces, chip textures
│   └── models/               # GLB files for Threlte slot machine
└── package.json
```

Single SvelteKit app with PocketBase backend. All game logic runs server-side to prevent client tampering. DB abstraction layer enables future migration to Supabase.

## Quick Start

```bash
pnpm install
pnpm run setup  # Download PocketBase + create collections
pnpm run pb     # Start PocketBase on :8090
pnpm run dev    # Start SvelteKit on :5173
```

## Requirements

- Node.js 20+
- pnpm 9+
- PocketBase (downloaded via `scripts/setup.sh`)

## Stack

| Layer | Tech |
|-------|------|
| Frontend | SvelteKit, Svelte 5 |
| 3D | Threlte (@threlte/core, @threlte/extras), Three.js |
| Backend | PocketBase (Go binary) |
| Auth | PocketBase auth (httpOnly cookies) |
| Build | Vite |
| Test | Vitest, @testing-library/svelte, jsdom |
| Lint | Biome |
| Coverage | @vitest/coverage-v8 |

## Scripts

```bash
pnpm run dev        # Dev server
pnpm run build      # Production build
pnpm run preview    # Preview production build
pnpm run check      # Type check (svelte-kit sync + tsc --noEmit)
pnpm run test       # Run tests (vitest run)
pnpm run test:watch # Run tests in watch mode
pnpm run pb         # Start PocketBase
pnpm run setup      # Initial setup (PocketBase download + schema)
```

## API Endpoints

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Lobby/dashboard |
| `/login` | GET/POST | Login page + form action |
| `/signup` | GET/POST | Registration page + form action |
| `/logout` | POST | Clear auth + redirect |
| `/blackjack` | GET | Blackjack page |
| `/blackjack/start` | POST | Start new game (wager) |
| `/blackjack/action` | POST | Hit/stand/double/split |
| `/roulette` | GET | Roulette page |
| `/roulette/spin` | POST | Place bets + spin |
| `/slots` | GET | Slot machine page |
| `/slots/spin` | POST | Spin reels (1 coin) |

## PocketBase Collections

- **users** (auth) — `username`, `coins` (default 100)
- **blackjack_games** — `user_id`, `deck`, `dealer_hand`, `player_hand`, `player_second_hand`, `player_coins`, `current_wager`, `game_over`, `message`, `player_stood`, `double_down`, `split`, `current_hand`, `dealer_value`

## License

MIT
