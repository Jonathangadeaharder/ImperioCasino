# ImperioCasino

Multi-game online casino. Blackjack, Roulette, 3D Slots (Threlte/Three.js). SvelteKit + PGlite (embedded Postgres in WASM) + Drizzle ORM.

## Architecture

```
ImperioCasino/
├── src/
│   ├── routes/               # SvelteKit pages
│   │   ├── +layout.svelte    # App shell (nav + auth guard)
│   │   ├── +page.svelte      # Lobby/dashboard
│   │   ├── blackjack/        # Blackjack game
│   │   │   ├── start/        # POST - start game
│   │   │   └── action/       # POST - hit/stand/double/split
│   │   ├── roulette/         # Roulette game
│   │   │   └── spin/         # POST - place bets + spin
│   │   ├── slots/            # 3D slot machine (Threlte)
│   │   │   └── spin/         # POST - spin reels
│   │   ├── login/            # Auth (form action)
│   │   ├── signup/           # Registration (form action)
│   │   └── logout/           # Logout (form action)
│   ├── lib/
│   │   ├── components/       # Shared UI components
│   │   ├── server/
│   │   │   ├── db/           # DB layer
│   │   │   │   ├── adapter.ts    # DBAdapter interface + DrizzleAdapter
│   │   │   │   ├── database.ts    # PGlite bootstrap, ensureDb, migrations
│   │   │   │   └── schema.ts     # Drizzle schema (user, session, blackjack_game)
│   │   │   ├── games/        # Server-side game logic
│   │   │   │   ├── blackjack.ts
│   │   │   │   ├── roulette.ts
│   │   │   │   └── slots.ts
│   │   │   └── auth-service.ts  # bcrypt + hashed session tokens
│   │   └── types.ts          # Shared TypeScript types
│   ├── hooks.server.ts       # ensureDb, locals.auth/db/user, auth redirect
│   ├── app.d.ts              # App.Locals type declarations
│   ├── app.html              # HTML shell
│   └── app.css               # Global styles
├── drizzle.config.ts         # Drizzle Kit config (migration generation)
├── static/                   # Static assets (images, 3D models)
│   ├── images/               # Card faces, chip textures
│   └── models/               # GLB files for Threlte slot machine
└── package.json
```

Single SvelteKit app. PGlite runs in-process (zero external DB service). All game logic runs server-side to prevent client tampering. Auth uses bcrypt (12 salt rounds) with sha256-hashed session tokens stored in a `session` table.

## Quick Start

```bash
pnpm install
pnpm run dev    # Start SvelteKit on :5173 (PGlite boots in-process)
```

PGlite persists to `.pglite/` by default. Set `PGLITE_DATA_DIR=memory` for an ephemeral in-process DB (used by tests).

## Requirements

- Node.js 20+
- pnpm 9+

## Stack

| Layer | Tech |
|-------|------|
| Frontend | SvelteKit, Svelte 5 |
| 3D | Threlte (@threlte/core, @threlte/extras), Three.js |
| Database | PGlite (embedded Postgres WASM) |
| ORM | Drizzle ORM |
| Auth | bcryptjs + hashed session tokens (httpOnly cookies) |
| Build | Vite |
| Test | Vitest, @testing-library/svelte, jsdom |
| Lint | Biome |
| Coverage | @vitest/coverage-v8 |

## Scripts

```bash
pnpm run dev         # Dev server
pnpm run build       # Production build
pnpm run preview     # Preview production build
pnpm run check       # Type check (svelte-kit sync + tsc --noEmit)
pnpm run test        # Run tests (vitest run)
pnpm run test:watch  # Run tests in watch mode
pnpm run db:generate # Generate Drizzle migration from schema changes
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

## Database Schema

- **user** - `id` (uuid), `username`, `email`, `password_hash` (bcrypt), `coins` (default 100), timestamps
- **session** - `id`, `user_id`, `token_hash` (sha256), `expires_at`, timestamps
- **blackjack_game** - `id`, `user_id`, `deck`, `dealer_hand`, `player_hand`, `player_second_hand`, `player_coins`, `current_wager`, `game_over`, `message`, `player_stood`, `double_down`, `split`, `current_hand`, `dealer_value`, timestamps

## License

MIT
